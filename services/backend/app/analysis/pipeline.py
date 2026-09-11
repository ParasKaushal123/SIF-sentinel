"""Analysis pipeline — orchestrates adapter → policy → AnalysisResult.

This is the 8-step pipeline described in the build spec:
  1. validate input
  2. extract signals (via adapter)
  3. validate evidence
  4. apply policy (Luck Test)
  5. map LSRs
  6. generate explanation
  7. assemble AnalysisResult
  8. (persistence handled by the worker)
"""

from __future__ import annotations

import uuid

from app.analysis.adapter import AdapterRequest, get_adapter
from app.analysis.policy import apply_policy
from app.schemas.analysis import (
    AnalysisResult,
    AnalysisVersions,
    ControlFinding,
    EvidenceSpan,
    HazardFinding,
    MissingFact,
    RuleFinding,
)
from app.schemas.enums import ClaimKind
from app.schemas.enums import (
    AnalysisMode,
    CandidateLabel,
    ControlState,
    ControlTiming,
    EventState,
    ExposureAssessment,
    Interpretation,
    LifeSavingRule,
    ProcessingStatus,
    RuleControlIssue,
    RuleMappingStatus,
    RuleRelevance,
    SeriousMechanism,
)

# Map policy control_state → ControlState enum
_CONTROL_STATE_MAP = {
    "absent_or_failed": ControlState.FAILED,
    "reported_effective": ControlState.EFFECTIVE_REPORTED,
    "unclear": ControlState.UNKNOWN,
    "unknown": ControlState.UNKNOWN,
}


async def run_analysis(
    narrative: str,
    *,
    analysis_id: str,
    report_revision_id: str,
    provider: str,
    mode: str = "live",
) -> tuple[AnalysisResult, int]:
    """Run the full analysis pipeline.

    Returns (AnalysisResult, duration_ms).
    """
    # --- Steps 1-2: validate + extract ---
    adapter = get_adapter(provider)
    request = AdapterRequest(
        narrative=narrative,
        revision_id=report_revision_id,
        mode=mode,
    )
    adapter_response = await adapter.analyze(request)
    raw = adapter_response.raw

    # --- Step 3: build evidence spans + an index for linking ---
    evidence: list[EvidenceSpan] = []
    # Map (start, end) → evidence id, so identical spans reuse one record
    span_index: dict[tuple[int, int], str] = {}

    def _register_span(span: dict, segment_id: str) -> str:
        """Create or reuse an EvidenceSpan; return its id."""
        start = span["start"]
        end = span["end"]
        key = (start, end)
        if key in span_index:
            return span_index[key]
        ev_id = f"ev-{len(evidence) + 1}"
        # UTF-16 offsets: count UTF-16 code units up to the char index
        start_u16 = len(narrative[:start].encode("utf-16-le")) // 2
        end_u16 = len(narrative[:end].encode("utf-16-le")) // 2
        evidence.append(
            EvidenceSpan(
                id=ev_id,
                source_segment_id=segment_id,
                exact_quote=span["quote"],
                start_utf16=start_u16,
                end_utf16=end_u16,
                claim_kind=ClaimKind.REPORTED,
            )
        )
        span_index[key] = ev_id
        return ev_id

    segment_id = report_revision_id  # single-segment for original narratives

    # --- Step 4: apply policy ---
    policy_result = apply_policy(raw)

    candidate_label = CandidateLabel(policy_result["candidate_label"])
    interpretation = Interpretation(policy_result["interpretation"])
    control_state = _CONTROL_STATE_MAP.get(
        policy_result["control_state"], ControlState.UNKNOWN
    )

    # --- Build hazard findings ---
    hazard_findings: list[HazardFinding] = []
    for h in raw.get("hazards", []):
        has_exposure = raw.get("has_exposure", False)
        exposure_assessment = (
            ExposureAssessment.EXPLICIT
            if has_exposure
            else ExposureAssessment.NOT_ESTABLISHED
        )

        # Serious mechanism supported if it's a serious hazard type
        from app.analysis.policy import SERIOUS_HAZARDS
        serious = (
            SeriousMechanism.SUPPORTED
            if h["hazard_kind"] in SERIOUS_HAZARDS
            else SeriousMechanism.NOT_SUPPORTED
        )

        # Event state
        if raw.get("control_failure_count", 0) > 0 and not has_exposure:
            event_state = EventState.EXPOSURE_ONLY
        elif has_exposure:
            event_state = EventState.INCIDENT_REPORTED
        else:
            event_state = EventState.NO_EVENT_REPORTED

        # Evidence for this hazard
        hazard_evidence_ids = [
            _register_span(s, segment_id) for s in h.get("evidence_spans", [])
        ]

        # Control evidence: failure spans if controls failed, else success spans
        if control_state in (ControlState.FAILED, ControlState.ABSENT):
            control_span_source = raw.get("control_failure_spans", [])
        elif control_state == ControlState.EFFECTIVE_REPORTED:
            control_span_source = raw.get("control_success_spans", [])
        else:
            control_span_source = []
        control_evidence_ids = [
            _register_span(s, segment_id) for s in control_span_source
        ]

        control_findings = [
            ControlFinding(
                control_name="primary_barrier",
                state=control_state,
                timing=ControlTiming.BEFORE_OR_DURING,
                evidence_ids=control_evidence_ids,
                rationale=f"Derived from {raw.get('control_failure_count', 0)} failure "
                          f"and {raw.get('control_success_count', 0)} success signals.",
            )
        ]

        hazard_findings.append(
            HazardFinding(
                finding_id=str(uuid.uuid4()),
                hazard_kind=h["hazard_kind"],
                hazard_description=(
                    f"{h['hazard_kind'].replace('_', ' ').title()} energy source "
                    f"detected ({h['signal_strength']} signals)."
                ),
                serious_mechanism=serious,
                exposure=exposure_assessment,
                controls=control_findings,
                event_state=event_state,
                evidence_ids=hazard_evidence_ids,
                rationale_code=f"hazard_{h['hazard_kind']}",
            )
        )

    # --- Step 5: map LSRs ---
    lsr_findings: list[RuleFinding] = []
    valid_rule_ids = {r.value for r in LifeSavingRule}
    for r in raw.get("lsr_findings", []):
        rule_id = r["rule_id"]
        if rule_id not in valid_rule_ids:
            continue

        relevance = (
            RuleRelevance.RELEVANT
            if r.get("signal_strength", 0) >= 2
            else RuleRelevance.UNCERTAIN
        )
        control_issue = (
            RuleControlIssue.NOT_ESTABLISHED
            if r.get("control_issue") == "control_gap"
            else RuleControlIssue.SUPPORTED
        )

        rule_evidence_ids = [
            _register_span(s, segment_id) for s in r.get("evidence_spans", [])
        ]

        lsr_findings.append(
            RuleFinding(
                rule_id=LifeSavingRule(rule_id),
                official_title=r["official_title"],
                relevance=relevance,
                control_issue=control_issue,
                evidence_ids=rule_evidence_ids,
            )
        )

    rule_mapping_status = (
        RuleMappingStatus.MAPPED if lsr_findings else RuleMappingStatus.NO_MATCH
    )

    # --- Missing facts (for insufficient_information) ---
    missing_facts: list[MissingFact] = []
    clarification_question = None
    if interpretation == Interpretation.INSUFFICIENT_INFORMATION:
        missing_facts.append(
            MissingFact(
                fact_id=str(uuid.uuid4()),
                description="Hazard energy, exposure, and control state details",
                importance="Required to determine SIF potential under the Luck Test.",
            )
        )
        clarification_question = (
            "Can you describe what hazard was present, whether anyone was exposed "
            "to it, and what safety controls were or were not in place?"
        )

    # --- Assemble result ---
    result = AnalysisResult(
        analysis_id=analysis_id,
        report_revision_id=report_revision_id,
        mode=AnalysisMode(mode) if mode in ("live", "fixture_replay") else AnalysisMode.LIVE,
        processing_status=ProcessingStatus.SUCCEEDED,
        candidate_label=candidate_label,
        interpretation=interpretation,
        review_reasons=_derive_review_reasons(policy_result, raw),
        facts=hazard_findings,
        lsr_findings=lsr_findings,
        rule_mapping_status=rule_mapping_status,
        missing_facts=missing_facts,
        clarification_question=clarification_question,
        evidence=evidence,
        rationale_summary=policy_result["rationale"],
        versions=AnalysisVersions(
            model=adapter_response.model_version,
            prompt=adapter_response.prompt_version,
            policy=policy_result["policy_version"],
            taxonomy=policy_result["taxonomy_version"],
        ),
    )

    return result, adapter_response.duration_ms


def _derive_review_reasons(policy_result: dict, raw: dict) -> list[str]:
    """Flag reports that warrant closer human review."""
    reasons: list[str] = []

    if policy_result["interpretation"] == "insufficient_information":
        reasons.append("insufficient_information")

    if policy_result["control_state"] == "unclear":
        reasons.append("unclear_control_state")

    # Borderline: serious hazard but no clear exposure
    if policy_result["has_serious_hazard"] and not policy_result["has_exposure"]:
        reasons.append("hazard_without_clear_exposure")

    # Multiple serious hazards
    serious_count = sum(
        1 for h in raw.get("hazards", [])
        if h["hazard_kind"] in {
            "gravity", "pressure", "mechanical", "electrical",
            "fire_explosion", "toxic_asphyxiation", "vehicle",
        }
    )
    if serious_count >= 3:
        reasons.append("multiple_serious_hazards")

    return reasons
