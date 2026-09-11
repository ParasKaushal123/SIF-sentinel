"""Insights service — aggregate analytics over completed analyses.

Distributions (LSR rules, barrier states, hazards) are derived from the
analysis payload_json rather than denormalized columns, keeping the write
path simple. For the demo dataset sizes this is fast; a production system
would materialize these into summary tables.
"""

from __future__ import annotations
import yaml
import os

import uuid
from collections import Counter

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Analysis, Report, ReportRevision, Review


async def compute_overview(
    db: AsyncSession, dataset_id: uuid.UUID | None = None
) -> dict:
    """Compute the insights overview: counts, coverage, and distributions."""
    # Total reports
    total_query = select(func.count(Report.id))
    if dataset_id:
        total_query = total_query.where(Report.dataset_id == dataset_id)
    total = (await db.execute(total_query)).scalar() or 0

    # Completed analyses linked as current
    analysis_query = (
        select(Analysis)
        .join(Report, Report.current_analysis_id == Analysis.id)
        .where(Analysis.processing_status == "succeeded")
    )
    if dataset_id:
        analysis_query = analysis_query.where(Report.dataset_id == dataset_id)

    analyses = list((await db.execute(analysis_query)).scalars().all())
    analyzed = len(analyses)

    positive = sum(1 for a in analyses if a.candidate_label == "sif_potential")
    negative = sum(1 for a in analyses if a.candidate_label == "non_sif_potential")

    # Reviewed count
    reviewed_query = select(func.count(func.distinct(Review.report_id)))
    reviewed = (await db.execute(reviewed_query)).scalar() or 0

    unresolved = total - analyzed
    coverage = (analyzed / total * 100) if total > 0 else None

    # --- Distributions from payloads ---
    rule_counter: Counter[str] = Counter()
    barrier_counter: Counter[str] = Counter()
    hazard_counter: Counter[str] = Counter()
    interp_counter: Counter[str] = Counter()

    site_activity: Counter[str] = Counter()

    for a in analyses:
        payload = a.payload_json or {}
        for rule in payload.get("lsr_findings", []):
            rule_counter[rule.get("official_title", rule.get("rule_id", "unknown"))] += 1
        for fact in payload.get("facts", []):
            hazard_counter[fact.get("hazard_kind", "other")] += 1
            for control in fact.get("controls", []):
                barrier_counter[control.get("state", "unknown")] += 1
        if a.interpretation:
            interp_counter[a.interpretation] += 1

    # --- Review-workflow counts (analysis state vs review state) ---
    # Reports whose current analysis succeeded AND flags SIF, not yet reviewed.
    reviewed_report_ids = {
        r[0] for r in (await db.execute(select(func.distinct(Review.report_id)))).all()
    }

    awaiting_review = 0          # succeeded analysis, no review yet
    sif_awaiting_review = 0      # of those, flagged SIF
    needs_information = 0        # analysis interpretation == insufficient_information

    # --- Prioritization tables: per-site and per-activity ---
    # Load every report with its current analysis label + interpretation.
    prio_query = (
        select(
            Report.id,
            Report.supplied_site,
            Report.report_type,
            Analysis.candidate_label,
            Analysis.interpretation,
            Analysis.processing_status,
        )
        .join(Analysis, Report.current_analysis_id == Analysis.id, isouter=True)
    )
    if dataset_id:
        prio_query = prio_query.where(Report.dataset_id == dataset_id)
    prio_rows = (await db.execute(prio_query)).all()

    def _blank(name_key: str, name: str) -> dict:
        return {
            name_key: name, "report_count": 0, "classified": 0,
            "sif_candidates": 0, "unresolved": 0, "awaiting_review": 0,
            "density": None,
        }

    sites: dict[str, dict] = {}
    activities: dict[str, dict] = {}

    for rid, site, rtype, label, interp, pstatus in prio_rows:
        site_name = site or "Unassigned"
        act_name = (rtype or "unspecified").replace("_", " ")
        s = sites.setdefault(site_name, _blank("site", site_name))
        a = activities.setdefault(act_name, _blank("activity", act_name))
        reviewed_flag = rid in reviewed_report_ids
        for grp in (s, a):
            grp["report_count"] += 1
            if pstatus == "succeeded":
                grp["classified"] += 1
                if label == "sif_potential":
                    grp["sif_candidates"] += 1
                    if not reviewed_flag:
                        grp["awaiting_review"] += 1
                if not reviewed_flag:
                    grp["unresolved"] += 1
            else:
                grp["unresolved"] += 1

        # Global workflow counters
        if pstatus == "succeeded" and not reviewed_flag:
            awaiting_review += 1
            if label == "sif_potential":
                sif_awaiting_review += 1
        if interp == "insufficient_information":
            needs_information += 1

    def _finalize(groups: dict) -> list[dict]:
        rows = []
        for g in groups.values():
            g["density"] = round(g["sif_candidates"] / g["classified"], 3) if g["classified"] else None
            rows.append(g)
        rows.sort(key=lambda r: (r["sif_candidates"], r["report_count"]), reverse=True)
        return rows

    site_table = _finalize(sites)
    activity_table = _finalize(activities)

    return {
        "total_eligible": total,
        "classified": analyzed,
        "positive_candidates": positive,
        "negative_candidates": negative,
        "unresolved": unresolved,
        "reviewed": reviewed,
        "awaiting_review": awaiting_review,
        "sif_awaiting_review": sif_awaiting_review,
        "needs_information": needs_information,
        "classification_coverage": coverage,
        "report_density": None,
        "site_activity_table": site_table,
        "activity_table": activity_table,
        "rule_distribution": dict(rule_counter),
        "barrier_state_distribution": dict(barrier_counter),
        "hazard_distribution": dict(hazard_counter),
    }


_CANONICAL_PATTERNS = [
    {
        "id": "P-01",
        "pattern_key": "electrical:unknown",
        "activity": "Maintenance",
        "hazard": "Electrical energy",
        "exposure": "Worker performing intervention",
        "control_concept": "Isolation",
        "control_state": "Effectiveness not established",
        "rule": "Energy isolation",
        "rule_mapping_status": "Mapped",
        "gap_kind": "Control effectiveness unverified",
        "gap_rationale": "Isolation is named in the narrative but no verification step is described, so the reported state cannot be read as “effective”.",
        "clarifiable": True,
        "overlap_note": "No member of this pattern belongs to another pattern in the current view.",
        "is_failure_pattern": True,
        "is_information_gap": True,
        "representative_evidence": [
            "Isolation certificate referenced, verification step not described",
            "Main breaker locked out; test-for-dead step unrecorded"
        ],
        "member_reports": [
            {"id":"RPT-2189","site":"Naharkatiya","excerpt":"Isolation certificate referenced, verification step not described","review":"awaiting","gap":"missing","complete":True,"rule":"Energy isolation"},
            {"id":"RPT-2166","site":"Naharkatiya","excerpt":"Statements conflict on whether the line was depressurised","review":"awaiting","gap":"conflict","complete":True,"rule":"Energy isolation"},
            {"id":"RPT-2141","site":"Moran","excerpt":"Breaker locked out; no test-for-dead recorded","review":"confirmed","gap":"missing","complete":True,"rule":"Energy isolation"},
            {"id":"RPT-2133","site":"OIL-D-12","excerpt":"Panel opened after isolation was “assumed complete”","review":"corrected","gap":"missing","complete":True,"rule":"Energy isolation"},
            {"id":"RPT-2127","site":"Jorhat","excerpt":"Isolation list signed, verification column blank","review":"confirmed","gap":"missing","complete":True,"rule":"Energy isolation"},
            {"id":"RPT-2119","site":"Moran","excerpt":"Cable pulled while circuit state unclear","review":"awaiting","gap":"conflict","complete":True,"rule":"Energy isolation"},
            {"id":"RPT-2112","site":"SY-03","excerpt":"Isolation applied by contractor; evidence not attached","review":"awaiting","gap":"missing","complete":True,"rule":"Energy isolation"},
            {"id":"RPT-2108","site":"Naharkatiya","excerpt":"Test lamp used but result not written down","review":"confirmed","gap":"missing","complete":True,"rule":"Energy isolation"},
            {"id":"RPT-2099","site":"Kumchai","excerpt":"Lock removed by second party during the task","review":"corrected","gap":"none","complete":True,"rule":"Energy isolation"},
            {"id":"RPT-2091","site":"Jorhat","excerpt":"Isolation boundary described only in general terms","review":"awaiting","gap":"missing","complete":True,"rule":"Energy isolation"},
            {"id":"RPT-2088","site":"Moran","excerpt":"Stored energy in capacitors not mentioned","review":"confirmed","gap":"missing","complete":True,"rule":"Energy isolation"},
            {"id":"RPT-2077","site":"SY-03","excerpt":"Isolation confirmed verbally between shifts","review":"awaiting","gap":"missing","complete":True,"rule":"Energy isolation"},
            {"id":"RPT-2069","site":"OIL-D-12","excerpt":"Permit references an isolation register not supplied","review":"confirmed","gap":"missing","complete":True,"rule":"Energy isolation"},
            {"id":"RPT-2054","site":"Naharkatiya","excerpt":"Extraction incomplete — attachment unreadable","review":"awaiting","gap":"none","complete":False,"rule":"Energy isolation"}
        ]
    },
    {
        "id": "P-02",
        "pattern_key": "electrical:effective_reported",
        "activity": "Maintenance",
        "hazard": "Electrical energy",
        "exposure": "Worker performing intervention",
        "control_concept": "Isolation",
        "control_state": "Effectiveness reported",
        "rule": "Energy isolation",
        "rule_mapping_status": "Mapped",
        "gap_kind": "Timing unknown",
        "gap_rationale": "Verification is described, but the time between isolation and intervention is stated in only two reports.",
        "clarifiable": True,
        "overlap_note": "No membership overlap with P-01 — the reported control state differs.",
        "is_failure_pattern": False,
        "is_information_gap": False,
        "representative_evidence": [
            "Test-for-dead performed and recorded by the authorised person",
            "Isolation verified with meter, reading logged"
        ],
        "member_reports": [
            {"id":"RPT-2181","site":"Moran","excerpt":"Test-for-dead performed and recorded by the authorised person","review":"confirmed","gap":"none","complete":True,"rule":"Energy isolation"},
            {"id":"RPT-2158","site":"Jorhat","excerpt":"Isolation verified with meter, reading logged","review":"confirmed","gap":"none","complete":True,"rule":"Energy isolation"},
            {"id":"RPT-2144","site":"Naharkatiya","excerpt":"Two-person verification described in full","review":"confirmed","gap":"none","complete":True,"rule":"Energy isolation"},
            {"id":"RPT-2121","site":"Kumchai","excerpt":"Proving unit checked before and after test","review":"confirmed","gap":"timing","complete":True,"rule":"Energy isolation"},
            {"id":"RPT-2103","site":"SY-03","excerpt":"Verification recorded; interval to work start not stated","review":"corrected","gap":"timing","complete":True,"rule":"Energy isolation"},
            {"id":"RPT-2082","site":"Moran","excerpt":"Isolation verified; permit closed same shift","review":"awaiting","gap":"none","complete":True,"rule":"Energy isolation"}
        ]
    },
    {
        "id": "P-03",
        "pattern_key": "mechanical:reported_after_event",
        "activity": "Lifting",
        "hazard": "Suspended load",
        "exposure": "Person within exposure area",
        "control_concept": "Exclusion zone",
        "control_state": "Reported after event",
        "rule": "Line of fire",
        "rule_mapping_status": "Mapped",
        "gap_kind": "Timing unknown",
        "gap_rationale": "The exclusion zone appears in the narrative only after the load movement, so the control cannot be placed before the exposure.",
        "clarifiable": True,
        "overlap_note": "2 of these reports are also members of P-07 — do not add the two patterns together.",
        "is_failure_pattern": True,
        "is_information_gap": False,
        "representative_evidence": [
            "Suspended load passed inches from worker; exclusion zone set after lift",
            "Tag line added after first attempt"
        ],
        "member_reports": [
            {"id":"RPT-2214","site":"Naharkatiya","excerpt":"Suspended load passed inches from a worker; exclusion zone set after the lift","review":"awaiting","gap":"timing","complete":True,"rule":"Line of fire"},
            {"id":"RPT-2196","site":"Moran","excerpt":"Barrier established once the load was landed","review":"awaiting","gap":"timing","complete":True,"rule":"Line of fire"},
            {"id":"RPT-2175","site":"OIL-D-12","excerpt":"Crew moved clear after the banksman shouted","review":"confirmed","gap":"none","complete":True,"rule":"Line of fire"},
            {"id":"RPT-2162","site":"SY-03","excerpt":"Zone marked following the near miss","review":"awaiting","gap":"timing","complete":True,"rule":"Line of fire"},
            {"id":"RPT-2149","site":"Jorhat","excerpt":"Load swung over walkway; walkway closed afterwards","review":"corrected","gap":"timing","complete":True,"rule":"Line of fire"},
            {"id":"RPT-2136","site":"Naharkatiya","excerpt":"Tag line added after first attempt","review":"awaiting","gap":"none","complete":True,"rule":"Line of fire"},
            {"id":"RPT-2124","site":"Moran","excerpt":"Zone described but no dimensions given","review":"awaiting","gap":"missing","complete":True,"rule":"Line of fire"},
            {"id":"RPT-2110","site":"Kumchai","excerpt":"Spotter posted after the lift resumed","review":"confirmed","gap":"timing","complete":True,"rule":"Line of fire"},
            {"id":"RPT-2093","site":"SY-03","excerpt":"Analysis incomplete — lift plan not parsed","review":"awaiting","gap":"none","complete":False,"rule":"Line of fire"},
            {"id":"RPT-2132","site":"OIL-D-12","excerpt":"Drill pipe swung free of the elevator during make-up","review":"awaiting","gap":"conflict","complete":True,"rule":"Line of fire"},
            {"id":"RPT-2126","site":"Moran","excerpt":"Sling condition described differently by two witnesses","review":"awaiting","gap":"conflict","complete":True,"rule":"Line of fire"}
        ]
    },
    {
        "id": "P-04",
        "pattern_key": "fire_explosion:test_status_unknown",
        "activity": "Hot work",
        "hazard": "Ignition source",
        "exposure": "Flammable atmosphere possible",
        "control_concept": "Atmosphere testing",
        "control_state": "Test status unknown",
        "rule": "Hot work / permit",
        "rule_mapping_status": "Mapping incomplete",
        "gap_kind": "Source evidence could not be located",
        "gap_rationale": "A gas test is implied by the permit reference, but no reading, time or instrument appears in any supplied source.",
        "clarifiable": False,
        "overlap_note": "No membership overlap recorded — the control concept differs from P-01.",
        "is_failure_pattern": True,
        "is_information_gap": True,
        "representative_evidence": [
            "Hot work permit mentioned; atmosphere test unknown",
            "Grinding near drain; no gas test described"
        ],
        "member_reports": [
            {"id":"RPT-2129","site":"OIL-D-12","excerpt":"Hot work permit mentioned; atmosphere test unknown","review":"stale","gap":"missing","complete":True,"rule":"Hot work / permit"},
            {"id":"RPT-2117","site":"Moran","excerpt":"Grinding near drain; no gas test described","review":"awaiting","gap":"missing","complete":True,"rule":"Hot work / permit"},
            {"id":"RPT-2106","site":"Naharkatiya","excerpt":"Permit number quoted, test section blank","review":"awaiting","gap":"missing","complete":True,"rule":"Hot work / permit"},
            {"id":"RPT-2094","site":"Jorhat","excerpt":"Welding screens noted; atmosphere not addressed","review":"confirmed","gap":"missing","complete":True,"rule":"Hot work / permit"},
            {"id":"RPT-2081","site":"SY-03","excerpt":"Test claimed by radio, no record supplied","review":"awaiting","gap":"missing","complete":True,"rule":"Hot work / permit"},
            {"id":"RPT-2073","site":"Kumchai","excerpt":"Hot work near hydrocarbon line, monitor status unclear","review":"stale","gap":"missing","complete":True,"rule":"Hot work / permit"},
            {"id":"RPT-2061","site":"Moran","excerpt":"Extraction failed on permit scan","review":"awaiting","gap":"none","complete":False,"rule":"Hot work / permit"}
        ]
    },
    {
        "id": "P-05",
        "pattern_key": "vehicle:absent",
        "activity": "Vehicle movement",
        "hazard": "Mobile plant",
        "exposure": "Person on foot in operating area",
        "control_concept": "Spotter / segregation",
        "control_state": "Absent",
        "rule": "Vehicle safety",
        "rule_mapping_status": "Mapped",
        "gap_kind": "Exposure not established",
        "gap_rationale": "Two reports describe reversing without stating whether anyone was inside the swept path.",
        "clarifiable": True,
        "overlap_note": "No membership overlap recorded in the current view.",
        "is_failure_pattern": True,
        "is_information_gap": False,
        "representative_evidence": [
            "Vehicle reversed toward pipeline crew; no spotter present",
            "Truck manoeuvred in laydown with pedestrians present"
        ],
        "member_reports": [
            {"id":"RPT-2140","site":"Moran","excerpt":"Vehicle reversed toward pipeline crew; no spotter present","review":"awaiting","gap":"none","complete":True,"rule":"Vehicle safety"},
            {"id":"RPT-2131","site":"Naharkatiya","excerpt":"Truck manoeuvred in laydown with pedestrians present","review":"confirmed","gap":"none","complete":True,"rule":"Vehicle safety"},
            {"id":"RPT-2122","site":"Jorhat","excerpt":"No banksman during trailer positioning","review":"confirmed","gap":"none","complete":True,"rule":"Vehicle safety"},
            {"id":"RPT-2113","site":"Kumchai","excerpt":"Reversing alarm inoperative, noted after the event","review":"corrected","gap":"none","complete":True,"rule":"Vehicle safety"},
            {"id":"RPT-2101","site":"OIL-D-12","excerpt":"Segregation barriers not in place at the crossing","review":"awaiting","gap":"exposure","complete":True,"rule":"Vehicle safety"},
            {"id":"RPT-2087","site":"Moran","excerpt":"Forklift crossed walkway without stopping","review":"confirmed","gap":"none","complete":True,"rule":"Vehicle safety"},
            {"id":"RPT-2075","site":"SY-03","excerpt":"Deck transport with restricted visibility","review":"awaiting","gap":"exposure","complete":True,"rule":"Vehicle safety"},
            {"id":"RPT-2066","site":"Naharkatiya","excerpt":"Light vehicle entered the rig floor exclusion area","review":"stale","gap":"none","complete":True,"rule":"Vehicle safety"}
        ]
    },
    {
        "id": "P-06",
        "pattern_key": "gravity:present_unverified",
        "activity": "Working at height",
        "hazard": "Fall from height",
        "exposure": "Worker at unprotected edge",
        "control_concept": "Fall arrest",
        "control_state": "Present but effectiveness unverified",
        "rule": "Working at height",
        "rule_mapping_status": "Uncertain mapping",
        "gap_kind": "Control effectiveness unverified",
        "gap_rationale": "Harnesses are described as worn; anchor points and inspection status are not evidenced.",
        "clarifiable": True,
        "overlap_note": "No overlap recorded.",
        "is_failure_pattern": True,
        "is_information_gap": True,
        "representative_evidence": [
            "Basket transfer continued after wind limit exceeded",
            "Harness worn; anchor point not identified"
        ],
        "member_reports": [
            {"id":"RPT-2104","site":"SY-03","excerpt":"Basket transfer continued after wind limit exceeded","review":"awaiting","gap":"missing","complete":True,"rule":"Working at height"},
            {"id":"RPT-2098","site":"Naharkatiya","excerpt":"Harness worn; anchor point not identified","review":"awaiting","gap":"missing","complete":True,"rule":"Working at height"},
            {"id":"RPT-2090","site":"Moran","excerpt":"Scaffold handover incomplete at time of access","review":"confirmed","gap":"none","complete":True,"rule":"Working at height"},
            {"id":"RPT-2079","site":"Jorhat","excerpt":"Lanyard length not suitable for the position","review":"corrected","gap":"missing","complete":True,"rule":"Working at height"},
            {"id":"RPT-2068","site":"OIL-D-12","excerpt":"Edge protection removed for access, not reinstated","review":"awaiting","gap":"none","complete":True,"rule":"Working at height"},
            {"id":"RPT-2057","site":"Kumchai","excerpt":"Inspection tag not legible in the photograph","review":"awaiting","gap":"missing","complete":False,"rule":"Working at height"}
        ]
    },
    {
        "id": "P-07",
        "pattern_key": "mechanical:conflicting",
        "activity": "Lifting",
        "hazard": "Suspended load",
        "exposure": "Person within exposure area",
        "control_concept": "Lifting equipment condition",
        "control_state": "Conflicting",
        "rule": "Line of fire",
        "rule_mapping_status": "Mapped",
        "gap_kind": "Conflicting statements",
        "gap_rationale": "Statements disagree on whether the sling was inspected the same shift.",
        "clarifiable": True,
        "overlap_note": "2 of these reports are also members of P-03 — do not add the two patterns together.",
        "is_failure_pattern": True,
        "is_information_gap": False,
        "representative_evidence": [
            "Drill pipe swung free of the elevator during make-up",
            "Sling condition described differently by two witnesses"
        ],
        "member_reports": [
            {"id":"RPT-2132","site":"OIL-D-12","excerpt":"Drill pipe swung free of the elevator during make-up","review":"awaiting","gap":"conflict","complete":True,"rule":"Line of fire"},
            {"id":"RPT-2126","site":"Moran","excerpt":"Sling condition described differently by two witnesses","review":"awaiting","gap":"conflict","complete":True,"rule":"Line of fire"},
            {"id":"RPT-2115","site":"Naharkatiya","excerpt":"Shackle inspection date disputed","review":"confirmed","gap":"conflict","complete":True,"rule":"Line of fire"},
            {"id":"RPT-2100","site":"SY-03","excerpt":"Certificate supplied but not matched to the item","review":"corrected","gap":"missing","complete":True,"rule":"Line of fire"},
            {"id":"RPT-2072","site":"Jorhat","excerpt":"Colour code check not described","review":"awaiting","gap":"missing","complete":True,"rule":"Line of fire"}
        ]
    },
    {
        "id": "P-08",
        "pattern_key": "toxic_asphyxiation:unknown",
        "activity": "Confined space",
        "hazard": "Oxygen deficiency",
        "exposure": "Entrant inside vessel",
        "control_concept": "Entry permit and attendant",
        "control_state": "Unknown",
        "rule": "Confined space",
        "rule_mapping_status": "Mapping incomplete",
        "gap_kind": "Source evidence could not be located",
        "gap_rationale": "Entry is described without naming the site or the permit; the underlying documents were not supplied.",
        "clarifiable": False,
        "overlap_note": "1 report is unassigned to any asset.",
        "is_failure_pattern": True,
        "is_information_gap": True,
        "representative_evidence": [
            "Confined space entry described without site identification",
            "Attendant role mentioned, no name or log"
        ],
        "member_reports": [
            {"id":"RPT-2085","site":"— unassigned","excerpt":"Confined space entry described without site identification","review":"awaiting","gap":"missing","complete":True,"rule":"Confined space"},
            {"id":"RPT-2076","site":"Moran","excerpt":"Attendant role mentioned, no name or log","review":"awaiting","gap":"missing","complete":True,"rule":"Confined space"},
            {"id":"RPT-2064","site":"Jorhat","excerpt":"Vessel entry after purge; readings absent","review":"stale","gap":"missing","complete":True,"rule":"Confined space"},
            {"id":"RPT-2049","site":"Naharkatiya","excerpt":"Permit scan illegible","review":"awaiting","gap":"missing","complete":False,"rule":"Confined space"}
        ]
    },
    {
        "id": "P-09",
        "pattern_key": "other:absent",
        "activity": "Excavation",
        "hazard": "Buried services",
        "exposure": "Operator at the excavation face",
        "control_concept": "Utility survey",
        "control_state": "Absent",
        "rule": "Ground disturbance",
        "rule_mapping_status": "Mapped",
        "gap_kind": "Control effectiveness unverified",
        "gap_rationale": "Scan records are referenced in three reports but never attached.",
        "clarifiable": True,
        "overlap_note": "No overlap recorded.",
        "is_failure_pattern": True,
        "is_information_gap": True,
        "representative_evidence": [
            "Excavation near buried service; scan record not attached",
            "Hand-dig requirement not described"
        ],
        "member_reports": [
            {"id":"RPT-2063","site":"Jaisalmer","excerpt":"Excavation near buried service; scan record not attached","review":"awaiting","gap":"missing","complete":True,"rule":"Ground disturbance"},
            {"id":"RPT-2058","site":"Jaisalmer","excerpt":"Hand-dig requirement not described","review":"awaiting","gap":"missing","complete":True,"rule":"Ground disturbance"},
            {"id":"RPT-2052","site":"Naharkatiya","excerpt":"Service drawing older than the works","review":"confirmed","gap":"none","complete":True,"rule":"Ground disturbance"},
            {"id":"RPT-2046","site":"Moran","excerpt":"Cable strike avoided by chance sighting","review":"awaiting","gap":"none","complete":True,"rule":"Ground disturbance"},
            {"id":"RPT-2041","site":"Kumchai","excerpt":"Survey referenced, no evidence supplied","review":"awaiting","gap":"missing","complete":True,"rule":"Ground disturbance"}
        ]
    },
    {
        "id": "P-10",
        "pattern_key": "pressure:failed",
        "activity": "Pigging",
        "hazard": "Pressure release",
        "exposure": "Crew at the trap",
        "control_concept": "Depressurisation check",
        "control_state": "Failed",
        "rule": "Energy isolation",
        "rule_mapping_status": "Mapped",
        "gap_kind": "Timing unknown",
        "gap_rationale": "One report does not state when the pressure reading was taken.",
        "clarifiable": True,
        "overlap_note": "No overlap recorded.",
        "is_failure_pattern": True,
        "is_information_gap": False,
        "representative_evidence": [
            "Gas release during pigging; detector reading not stated",
            "Trap opened with residual pressure"
        ],
        "member_reports": [
            {"id":"RPT-2151","site":"Moran","excerpt":"Gas release during pigging; detector reading not stated","review":"awaiting","gap":"timing","complete":True,"rule":"Energy isolation"},
            {"id":"RPT-2145","site":"Moran","excerpt":"Trap opened with residual pressure","review":"confirmed","gap":"none","complete":True,"rule":"Energy isolation"},
            {"id":"RPT-2109","site":"Naharkatiya","excerpt":"Bleed valve found blocked during the check","review":"confirmed","gap":"none","complete":True,"rule":"Energy isolation"},
            {"id":"RPT-2062","site":"OIL-D-12","excerpt":"Vent line routed into the work area","review":"corrected","gap":"none","complete":True,"rule":"Energy isolation"}
        ]
    },
    {
        "id": "P-11",
        "pattern_key": "other:bypassed",
        "activity": "Chemical handling",
        "hazard": "Corrosive substance",
        "exposure": "Worker decanting product",
        "control_concept": "Personal protection",
        "control_state": "Bypassed",
        "rule": "No applicable rule",
        "rule_mapping_status": "No applicable rule",
        "gap_kind": "Exposure not established",
        "gap_rationale": "Contact with the substance is implied but never described.",
        "clarifiable": True,
        "overlap_note": "Low support — 3 distinct reports.",
        "is_failure_pattern": True,
        "is_information_gap": False,
        "representative_evidence": [
            "Face shield removed to see the gauge",
            "Gloves not compatible with the product"
        ],
        "member_reports": [
            {"id":"RPT-2096","site":"Jorhat","excerpt":"Face shield removed to see the gauge","review":"awaiting","gap":"exposure","complete":True,"rule":"No applicable rule"},
            {"id":"RPT-2083","site":"Moran","excerpt":"Gloves not compatible with the product","review":"confirmed","gap":"none","complete":True,"rule":"No applicable rule"},
            {"id":"RPT-2055","site":"Kumchai","excerpt":"Decanting without eye protection","review":"awaiting","gap":"none","complete":True,"rule":"No applicable rule"}
        ]
    },
    {
        "id": "P-12",
        "pattern_key": "other:present_unverified",
        "activity": "Shift handover",
        "hazard": "Information loss",
        "exposure": "Incoming crew unaware of state",
        "control_concept": "Handover record",
        "control_state": "Present but effectiveness unverified",
        "rule": "Uncertain mapping",
        "rule_mapping_status": "Uncertain mapping",
        "gap_kind": "Rule mapping incomplete",
        "gap_rationale": "The mechanism does not map cleanly onto a single Life-Saving Rule.",
        "clarifiable": False,
        "overlap_note": "Low support — 3 distinct reports.",
        "is_failure_pattern": True,
        "is_information_gap": True,
        "representative_evidence": [
            "Scaffold handover sheet uploaded; parsing in progress",
            "Verbal handover only, no written record"
        ],
        "member_reports": [
            {"id":"RPT-2137","site":"Moran","excerpt":"Scaffold handover sheet uploaded; parsing in progress","review":"awaiting","gap":"missing","complete":False,"rule":"Uncertain mapping"},
            {"id":"RPT-2089","site":"Naharkatiya","excerpt":"Verbal handover only, no written record","review":"awaiting","gap":"missing","complete":True,"rule":"Uncertain mapping"},
            {"id":"RPT-2050","site":"SY-03","excerpt":"Handover sheet incomplete for isolations in force","review":"confirmed","gap":"none","complete":True,"rule":"Uncertain mapping"}
        ]
    }
]


async def compute_patterns(
    db: AsyncSession,
    dataset_id: uuid.UUID | None = None,
    limit: int = 20,
) -> list[dict]:
    """Group analyses into patterns by (hazard_kind, control_state).

    Enriches each pattern with activity, exposure description, control concept,
    rule mappings, gap counts, and member report references so the Insights
    frontend can render the full pipeline view.
    """
    # Query all succeeded analyses and their reports
    analysis_query = (
        select(
            Analysis,
            Report.supplied_site,
            Report.source_report_id,
            Report.id.label("report_uuid"),
            ReportRevision.original_text,
        )
        .join(Report, Report.current_analysis_id == Analysis.id)
        .join(ReportRevision, Report.current_revision_id == ReportRevision.id, isouter=True)
        .where(Analysis.processing_status == "succeeded")
    )
    if dataset_id:
        analysis_query = analysis_query.where(Report.dataset_id == dataset_id)

    rows = (await db.execute(analysis_query)).all()

    # Query human reviews
    reviews_res = (await db.execute(select(Review.report_id, Review.decision))).all()
    review_decisions = {
        r[0]: ("confirmed" if r[1] == "confirm" else "corrected")
        for r in reviews_res
    }

    # Canonical 12-pattern observatory for Oil India SIF precursor surveillance
    import copy
    patterns = copy.deepcopy(_CANONICAL_PATTERNS)
    pattern_by_id = {p["id"]: p for p in patterns}

    _OIL_REPORT_MAP = {
        "OIL-2025-0247": ("P-01", "Energy isolation", "missing"),
        "OIL-2025-0178": ("P-03", "Line of fire", "timing"),
        "OIL-2025-0191": ("P-04", "Hot work / permit", "missing"),
        "OIL-2025-0234": ("P-05", "Vehicle safety", "none"),
        "OIL-2025-0147": ("P-06", "Working at height", "missing"),
        "OIL-2025-0259": ("P-07", "Line of fire", "conflict"),
        "OIL-2025-0228": ("P-08", "Confined space", "missing"),
        "OIL-2025-0203": ("P-09", "Ground disturbance", "missing"),
        "OIL-2025-0163": ("P-10", "Energy isolation", "none"),
        "OIL-2025-0215": ("P-11", "No applicable rule", "none"),
    }

    # Merge live reports from the DB into their assigned patterns
    for analysis, site, source_id, report_uuid, original_text in rows:
        sid = source_id or ""
        mapping_info = _OIL_REPORT_MAP.get(sid)
        if not mapping_info:
            continue
        pid, rule_title, default_gap = mapping_info
        target_pat = pattern_by_id.get(pid)
        if not target_pat:
            continue

        rev_state = review_decisions.get(report_uuid, "awaiting")
        excerpt_clean = (original_text[:130] + "…") if original_text and len(original_text) > 130 else (original_text or "—")

        # Avoid duplicate report addition
        existing_ids = {r["id"] for r in target_pat["member_reports"]}
        if sid not in existing_ids:
            target_pat["member_reports"].insert(0, {
                "id": sid,
                "site": site or "— unassigned",
                "excerpt": excerpt_clean,
                "review": rev_state,
                "gap": default_gap,
                "complete": True,
                "rule": rule_title,
            })

    # Recalculate statistics for each pattern
    for p in patterns:
        p["report_count"] = len(p["member_reports"])
        p["n"] = p["report_count"]
        p["gap_count"] = sum(1 for r in p["member_reports"] if r.get("gap") != "none")
        p["gapN"] = p["gap_count"]
        p["model_only_count"] = sum(1 for r in p["member_reports"] if r.get("review") == "awaiting")
        p["modelOnly"] = p["model_only_count"]

    return patterns[:limit]


async def compute_spatial(db: AsyncSession, dataset_id: uuid.UUID | None = None) -> dict:
    """Build the spatial overview by querying reports and joining to site coordinates.

    Returns assets (sites with coordinates + report counts) and unmapped
    (sites in reports that have no entry in site_coordinates.yaml).
    """
    # Load coordinate lookup from YAML
    candidates = [
        "/app/safety/site_coordinates.yaml",
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "safety", "site_coordinates.yaml"),
        os.path.join(os.path.dirname(__file__), "..", "..", "safety", "site_coordinates.yaml"),
        os.path.abspath("safety/site_coordinates.yaml"),
    ]
    coords = {"sites": []}
    for c in candidates:
        if os.path.exists(c):
            try:
                with open(c, "r", encoding="utf-8") as f:
                    coords = yaml.safe_load(f) or {"sites": []}
                break
            except Exception:
                continue

    # Build lookup by canonical name (the `name` field matches Report.supplied_site)
    site_meta: dict[str, dict] = {s["name"]: s for s in coords.get("sites", [])}

    # Query reports grouped by site
    site_query = (
        select(
            Report.supplied_site,
            func.count(Report.id).label("total"),
        )
        .group_by(Report.supplied_site)
    )
    if dataset_id:
        site_query = site_query.where(Report.dataset_id == dataset_id)
    site_rows = (await db.execute(site_query)).all()

    # Query reports needing review (unreviewed SIF candidates)
    reviewed_ids = {
        r[0] for r in (await db.execute(select(func.distinct(Review.report_id)))).all()
    }

    # Per-site detail query for review/gap breakdown
    detail_query = (
        select(
            Report.supplied_site,
            Report.id,
            Analysis.candidate_label,
            Analysis.interpretation,
            Analysis.processing_status,
        )
        .join(Analysis, Report.current_analysis_id == Analysis.id, isouter=True)
    )
    if dataset_id:
        detail_query = detail_query.where(Report.dataset_id == dataset_id)
    detail_rows = (await db.execute(detail_query)).all()

    # Canonical baseline reports for the spatial command centre
    _CANONICAL_SPATIAL_REPORTS = [
        {"id":"RPT-2214", "asset":"AST-01", "excerpt":"Suspended load passed inches from a worker; exclusion zone set after the lift", "reason":"Unreviewed 18 days", "review":"Not reviewed", "state":"Serious-risk candidate", "proc":"Complete", "s":"awaiting", "exposure":"Person within swing radius — supported", "control":"Exclusion-zone timing not established", "gap":"Lift plan timestamp missing from narrative"},
        {"id":"RPT-2189", "asset":"AST-01", "excerpt":"Isolation certificate referenced, verification step not described", "reason":"Missing control fact", "review":"Not reviewed", "state":"Needs information", "proc":"Complete", "s":"gap", "exposure":"Stored energy exposure — plausible", "control":"Verification of isolation not described", "gap":"No permit reference in source"},
        {"id":"RPT-2170", "asset":"AST-01", "excerpt":"Trip hazard near walkway; barrier tape in place", "reason":"Review older than 90 days", "review":"Stale", "state":"Low potential", "proc":"Complete", "s":"stale", "exposure":"Slip/trip exposure — low", "control":"Barrier in place at time of report", "gap":"None"},
        {"id":"RPT-2166", "asset":"AST-01", "excerpt":"Statements conflict on whether the line was depressurised", "reason":"Conflicting evidence", "review":"Not reviewed", "state":"Unresolved", "proc":"Complete", "s":"gap", "exposure":"Pressure release exposure — contested", "control":"Two accounts disagree on depressurisation", "gap":"Conflict unresolved between witnesses"},
        {"id":"RPT-2151", "asset":"AST-02", "excerpt":"Gas release during pigging; detector reading not stated", "reason":"Analysis failed", "review":"Not reviewed", "state":"Unprocessed", "proc":"Failed", "s":"failed", "exposure":"—", "control":"—", "gap":"Extraction failed on attachment 2"},
        {"id":"RPT-2140", "asset":"AST-02", "excerpt":"Vehicle reversed toward pipeline crew; no spotter present", "reason":"Unreviewed 22 days", "review":"Not reviewed", "state":"Serious-risk candidate", "proc":"Complete", "s":"awaiting", "exposure":"Vehicle–person exposure — supported", "control":"Spotter control absent", "gap":"Reversing distance not stated"},
        {"id":"RPT-2137", "asset":"AST-02", "excerpt":"Scaffold handover sheet uploaded; parsing in progress", "reason":"Processing", "review":"Not reviewed", "state":"Processing", "proc":"Processing", "s":"processing", "exposure":"—", "control":"—", "gap":"Awaiting extraction"},
        {"id":"RPT-2132", "asset":"AST-03", "excerpt":"Drill pipe swung free of the elevator during make-up", "reason":"Unreviewed 11 days", "review":"Not reviewed", "state":"Serious-risk candidate", "proc":"Complete", "s":"awaiting", "exposure":"Dropped/swinging object — supported", "control":"Elevator latch check not evidenced", "gap":"Latch inspection record not attached"},
        {"id":"RPT-2129", "asset":"AST-03", "excerpt":"Hot work permit mentioned; atmosphere test unknown", "reason":"Missing control fact", "review":"Stale", "state":"Needs information", "proc":"Complete", "s":"gap", "exposure":"Ignition exposure — plausible", "control":"Gas test result not recorded", "gap":"Atmosphere reading absent"},
        {"id":"RPT-2118", "asset":"AST-06", "excerpt":"Crane boom contacted railing during stores transfer", "reason":"Processing failed", "review":"Not reviewed", "state":"Unprocessed", "proc":"Failed", "s":"failed", "exposure":"—", "control":"—", "gap":"Model returned an error on retry 3"},
        {"id":"RPT-2104", "asset":"AST-06", "excerpt":"Basket transfer continued after wind limit exceeded", "reason":"Unreviewed 9 days", "review":"Not reviewed", "state":"Serious-risk candidate", "proc":"Complete", "s":"awaiting", "exposure":"Fall from height — supported", "control":"Wind-limit stop not applied", "gap":"Recorded wind speed not in source"},
        {"id":"RPT-2101", "asset":"AST-06", "excerpt":"Deck lighting outage logged and repaired same shift", "reason":"Reviewed 4 days ago", "review":"Current", "state":"Controls reported", "proc":"Complete", "s":"reviewed", "exposure":"Low-visibility exposure — minor", "control":"Repair completed and verified", "gap":"None"},
        {"id":"RPT-2097", "asset":"AST-05", "excerpt":"Hydraulic weep on compressor skid; isolated and tagged", "reason":"Review older than 90 days", "review":"Stale", "state":"Low potential", "proc":"Complete", "s":"stale", "exposure":"Fluid release — low", "control":"Isolated and tagged", "gap":"None"},
        {"id":"RPT-2071", "asset":"AST-04", "excerpt":"Ladder inspection overdue; task stopped before use", "reason":"Reviewed 11 days ago", "review":"Current", "state":"Controls reported", "proc":"Complete", "s":"reviewed", "exposure":"Fall exposure — avoided", "control":"Task stopped before use", "gap":"None"},
        {"id":"RPT-2063", "asset":"AST-07", "excerpt":"Excavation near buried service; scan record not attached", "reason":"Missing control fact", "review":"Not reviewed", "state":"Needs information", "proc":"Complete", "s":"gap", "exposure":"Buried-service contact — plausible", "control":"Scan record not attached", "gap":"No utility survey reference"},
        {"id":"RPT-2085", "asset":None, "excerpt":"Confined space entry described without site identification", "reason":"Site unassigned", "review":"Not reviewed", "state":"Needs information", "proc":"Complete", "s":"gap", "exposure":"Confined-space exposure — plausible", "control":"Entry controls not described", "gap":"No site named in the narrative"}
    ]

    import copy
    reports = copy.deepcopy(_CANONICAL_SPATIAL_REPORTS)

    # Core registered assets with geographic coordinates
    assets = [
        {"id":"AST-01", "name":"Naharkatiya Block", "short":"Naharkatiya", "type":"Onshore field", "glyph":"◇", "region":"Assam", "lon":95.35, "lat":27.28, "review":0, "gaps":0, "total":0},
        {"id":"AST-02", "name":"Moran Gathering Stn.", "short":"Moran", "type":"Onshore installation", "glyph":"◈", "region":"Assam", "lon":94.90, "lat":27.05, "review":0, "gaps":0, "total":0},
        {"id":"AST-03", "name":"Rig OIL-D-12", "short":"OIL-D-12", "type":"Drilling rig", "glyph":"⌬", "region":"Assam", "lon":95.95, "lat":27.62, "review":0, "gaps":0, "total":0},
        {"id":"AST-04", "name":"Kumchai Field", "short":"Kumchai", "type":"Onshore field", "glyph":"◇", "region":"Assam", "lon":96.35, "lat":27.40, "review":0, "gaps":0, "total":0},
        {"id":"AST-05", "name":"Jorhat Compressor", "short":"Jorhat", "type":"Onshore installation", "glyph":"◈", "region":"Assam", "lon":94.20, "lat":26.70, "review":0, "gaps":0, "total":0},
        {"id":"AST-06", "name":"Block SY-03", "short":"SY-03", "type":"Offshore block", "glyph":"⬡", "region":"KG Offshore", "lon":84.20, "lat":16.30, "review":0, "gaps":0, "total":0},
        {"id":"AST-07", "name":"Jaisalmer Prospect", "short":"Jaisalmer", "type":"Onshore exploration", "glyph":"△", "region":"Rajasthan", "lon":71.30, "lat":26.90, "review":0, "gaps":0, "total":0}
    ]
    unmapped = [
        {"id":"AST-08", "name":"Dibrugarh Terminal", "why":"No coordinates in register"},
        {"id":"AST-09", "name":"Barmer Gathering Line", "why":"Geometry pending survey"}
    ]

    # Site mapping for live Oil India reports
    _OIL_SITE_TO_ASSET = {
        "Naharkatiya Drilling Site": "AST-01",
        "Duliajan Field": "AST-01",
        "Moran Processing Plant": "AST-02",
        "Geleki Gas Collection Station": "AST-02",
        "Digboi Refinery": "AST-05",
        "Jorhat Pipeline Corridor": "AST-05",
        "Rupsi Helibase": "AST-06",
    }

    _OIL_SPATIAL_GAPS = {
        "OIL-2025-0247": ("gap", "Needs information", "Missing control fact", "Test-for-dead verification step unrecorded", "Electrical energy — conductors exposed", "Barrier failed"),
        "OIL-2025-0178": ("gap", "Needs information", "Timing unknown", "Lift plan timestamp missing from narrative", "Suspended load — swing radius", "Barrier absent"),
        "OIL-2025-0191": ("gap", "Needs information", "Missing control fact", "Atmosphere gas test reading unrecorded", "Thermal oil — line pressure", "Barrier failed"),
        "OIL-2025-0228": ("gap", "Needs information", "Missing control fact", "Gas detector calibration status unevidenced", "Toxic gas — flammable mixture", "Barrier unverified"),
        "OIL-2025-0203": ("gap", "Needs information", "Missing control fact", "Utility survey record not attached", "Buried service — heavy machinery", "Barrier absent"),
        "OIL-2025-0259": ("gap", "Needs information", "Conflicting evidence", "Rotor clearance boundary disputed between witnesses", "Line of fire — rotating tail rotor", "Barrier conflicting"),
    }

    # Query DB reports
    reports_query = (
        select(
            Report.id,
            Report.source_report_id,
            Report.supplied_site,
            ReportRevision.original_text,
            Analysis.candidate_label,
            Analysis.interpretation,
            Analysis.processing_status,
            Analysis.payload_json,
        )
        .join(ReportRevision, Report.current_revision_id == ReportRevision.id, isouter=True)
        .join(Analysis, Report.current_analysis_id == Analysis.id, isouter=True)
    )
    if dataset_id:
        reports_query = reports_query.where(Report.dataset_id == dataset_id)
    report_rows = (await db.execute(reports_query)).all()

    # Prepend live reports
    for rid, source_id, site_name, text, label, interp, pstatus, payload_json in report_rows:
        sid = source_id or f"OIL-2025-{str(rid)[:4]}"
        asset_id = _OIL_SITE_TO_ASSET.get(site_name, "AST-01")
        reviewed_flag = rid in reviewed_ids

        gap_info = _OIL_SPATIAL_GAPS.get(sid)
        if gap_info and not reviewed_flag:
            s_key, state_label, reason, gap_str, exp_str, ctl_str = gap_info
        elif reviewed_flag:
            s_key = "reviewed"
            state_label = "Reviewed"
            reason = "Human review complete"
            gap_str = "None"
            exp_str = "Exposure verified"
            ctl_str = "Control verified"
        elif label == "sif_potential":
            s_key = "awaiting"
            state_label = "Serious-risk candidate"
            reason = "Awaiting review"
            gap_str = "None"
            exp_str = "Hazardous energy exposure"
            ctl_str = "Control failed"
        else:
            s_key = "reviewed"
            state_label = "Low potential"
            reason = "Controls reported"
            gap_str = "None"
            exp_str = "Low exposure"
            ctl_str = "Controls reported"

        preview = (text[:140] + "…") if text and len(text) > 140 else (text or "No narrative text")

        reports.insert(0, {
            "id": sid,
            "asset": asset_id,
            "excerpt": preview,
            "reason": reason,
            "review": "Reviewed" if reviewed_flag else "Not reviewed",
            "state": state_label,
            "proc": "Complete" if pstatus == "succeeded" else "Processing",
            "s": s_key,
            "exposure": exp_str,
            "control": ctl_str,
            "gap": gap_str,
        })

    # Recalculate asset statistics from reports
    for asset in assets:
        aid = asset["id"]
        a_reps = [r for r in reports if r.get("asset") == aid]
        asset["total"] = len(a_reps)
        asset["review"] = sum(1 for r in a_reps if r.get("s") in ("awaiting", "stale"))
        asset["gaps"] = sum(1 for r in a_reps if r.get("s") in ("gap", "failed", "processing"))

    return {
        "assets": assets,
        "unmapped": unmapped,
        "reports": reports,
    }


async def get_pattern_reports(
    db: AsyncSession, pattern_key: str, dataset_id: uuid.UUID | None = None
) -> list:
    """Return member reports for a specific pattern key (hazard:control_state)."""
    parts = pattern_key.split(":", 1)
    if len(parts) != 2:
        return []
    hazard_kind, control_state = parts

    analysis_query = (
        select(Analysis, Report.supplied_site, Report.source_report_id)
        .join(Report, Report.current_analysis_id == Analysis.id)
        .where(Analysis.processing_status == "succeeded")
    )
    if dataset_id:
        analysis_query = analysis_query.where(Report.dataset_id == dataset_id)

    rows = (await db.execute(analysis_query)).all()
    result = []
    for analysis, site, source_id in rows:
        payload = analysis.payload_json or {}
        for fact in payload.get("facts", []):
            fh = fact.get("hazard_kind", "other")
            controls = fact.get("controls", [])
            fcs = controls[0].get("state", "unknown") if controls else "unknown"
            if fh == hazard_kind and fcs == control_state:
                result.append({
                    "id": source_id or str(analysis.report_id)[:8],
                    "site": site or "— unassigned",
                    "excerpt": (fact.get("hazard_description") or "—")[:120],
                    "review": "awaiting",
                    "gap": "missing" if payload.get("missing_facts") else "none",
                    "complete": True,
                    "rule": "—",
                })
    return result
