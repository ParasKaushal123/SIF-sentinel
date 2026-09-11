"""Fixture adapter — deterministic, keyword-driven analysis for demo/testing.

This adapter implements the Luck Test heuristically. It is NOT a real model;
it is a rule-based extractor that reads the narrative for signals of:
  - serious hazard energy (height, pressure, gravity, electrical, vehicle...)
  - exposure (a person in the line of fire)
  - control state (missing/failed/bypassed barriers)

The key property it demonstrates is OUTCOME RESISTANCE: the classification
depends on hazard energy + exposure + control failure, NOT on whether someone
was actually injured. A near-miss where a worker was 6m up without a harness
classifies the same as if he had fallen — because the *potential* is identical.

And CONTROL SENSITIVITY: if the narrative says the harness was worn and the
fall arrested, the same scenario becomes non-SIF-potential.
"""

from __future__ import annotations

import re
import time

from app.analysis.adapter import AdapterRequest, AdapterResponse, ModelAdapter

MODEL_VERSION = "fixture-v1"
PROMPT_VERSION = "luck-test-heuristic-v1"


# ---------------------------------------------------------------------------
# Hazard energy signal patterns
# ---------------------------------------------------------------------------
HAZARD_PATTERNS: dict[str, list[str]] = {
    "gravity": [
        r"\bfall\b", r"\bheight\b", r"\bmonkey board\b", r"\bscaffold\b",
        r"\d+\s*(?:m|meter|metre|feet|ft)\b.*(?:height|elevat|up|above)",
        r"\bworking at height\b", r"\bharness\b", r"\bfall arrest\b",
        r"\belevat", r"\bplatform\b", r"\bderrick\b",
    ],
    "pressure": [
        r"\bpressure\b", r"\bbar\b", r"\bpsi\b", r"\brelief valve\b",
        r"\boverpressure\b", r"\bvessel\b", r"\bcompressor\b", r"\bflange\b",
        r"\bsteam\b", r"\bgas\b.*\bleak\b", r"\bblowout\b", r"\bBOP\b",
    ],
    "mechanical": [
        r"\blifting\b", r"\bcrane\b", r"\bsling\b", r"\bhoist\b",
        r"\brigging\b", r"\bload\b", r"\bdropped object\b", r"\brotor\b",
        r"\bmoving part\b", r"\bcrush\b", r"\bton\b",
    ],
    "electrical": [
        r"\belectric", r"\d+\s*V\b", r"\bvolt", r"\bshock\b",
        r"\blive conductor", r"\bbus bar", r"\bbreaker\b", r"\benergiz",
        r"\barc flash\b", r"\bLOTO\b", r"\blockout\b",
    ],
    "fire_explosion": [
        r"\bfire\b", r"\bexplos", r"\bignit", r"\bflammable\b",
        r"\bmethane\b", r"\bhot work\b", r"\bspark\b", r"\bhydrocarbon\b",
        r"\bZone\s*[012]\b", r"\bhazardous area\b",
    ],
    "toxic_asphyxiation": [
        r"\btoxic\b", r"\bH2S\b", r"\bhydrogen sulphide\b", r"\basphyxiat",
        r"\bconfined space\b", r"\boxygen\b", r"\bgas detector",
        r"\bventilation\b", r"\bfume", r"\bexposure limit\b",
    ],
    "vehicle": [
        r"\bvehicle\b", r"\btanker\b", r"\btruck\b", r"\bdriving\b",
        r"\boverturn", r"\bcollision\b", r"\bspeed\b", r"\bhaul road\b",
        r"\bcurve\b", r"\bdriver\b",
    ],
}

# ---------------------------------------------------------------------------
# Exposure signals — a person in the line of fire
# ---------------------------------------------------------------------------
EXPOSURE_PATTERNS = [
    r"\bworker\b", r"\brigger\b", r"\boperator\b", r"\belectrician\b",
    r"\bcrew\b", r"\bpersonnel\b", r"\bemployee\b", r"\bstaff\b",
    r"\bdriver\b", r"\bpassenger\b", r"\boccupant\b", r"\broughneck\b",
    r"\bwithin\s+\d+\s*(?:m|meter)", r"\bred zone\b", r"\bdanger zone\b",
    r"\bbeneath\b", r"\bunder the load\b", r"\bline of fire\b",
    r"\breceived\b.*\bburn", r"\binjur", r"\bstruck\b",
]

# ---------------------------------------------------------------------------
# Control failure signals — barriers missing / failed / bypassed
# ---------------------------------------------------------------------------
CONTROL_FAILURE_PATTERNS = [
    r"\bwithout\b.*(?:harness|guard|permit|ppe|protection)",
    r"\bmissing\b", r"\boverdue\b", r"\bnot\s+(?:test|inspect|repair|worn|present|available)",
    r"\bbypass", r"\bjumper", r"\bdisabled\b", r"\bseized\b", r"\bcorroded\b",
    r"\bfaulty\b", r"\bfailed\b", r"\bfault mode\b", r"\bwrong\b.*(?:gasket|spec)",
    r"\bno\s+(?:permit|guardrail|signage|dig permit)",
    r"\bexpired\b", r"\bunauthorized\b", r"\bnot\s+completed\b",
    r"\bdecided to proceed\b", r"\bdamaged\b",
]

# ---------------------------------------------------------------------------
# Control SUCCESS signals — barriers held (pushes toward non-SIF)
# ---------------------------------------------------------------------------
CONTROL_SUCCESS_PATTERNS = [
    r"\bharness\s+(?:was\s+)?worn\b", r"\bfall\s+(?:was\s+)?arrested\b",
    r"\bpermit\s+(?:was\s+)?(?:valid|in place)\b", r"\bproperly\s+guard",
    r"\binspect\w*\s+(?:up to date|current|valid)\b",
    r"\bworking\s+correctly\b", r"\bfunctioned as designed\b",
    r"\bbarrier\s+held\b", r"\bstopped the (?:work|load|fall)\b",
]

# ---------------------------------------------------------------------------
# IOGP Life-Saving Rules keyword mapping
# ---------------------------------------------------------------------------
LSR_PATTERNS: dict[str, list[str]] = {
    "work_authorisation": [r"\bpermit\b", r"\bwork authoriz", r"\bpermit-to-work\b", r"\bPTW\b"],
    "energy_isolation": [r"\bisolat", r"\bLOTO\b", r"\blockout\b", r"\benergiz", r"\bbypass"],
    "confined_space": [r"\bconfined space\b", r"\bvessel entry\b", r"\btank entry\b"],
    "driving": [r"\bdriving\b", r"\bvehicle\b", r"\bseatbelt\b", r"\bspeed\b", r"\btanker\b", r"\bdriver\b"],
    "hot_work": [r"\bhot work\b", r"\bwelding\b", r"\bspark\b", r"\bignition source\b", r"\bflammable\b"],
    "line_of_fire": [r"\bline of fire\b", r"\bred zone\b", r"\bdanger zone\b", r"\bbeneath\b", r"\bstruck\b", r"\bmoving\b"],
    "safe_mechanical_lifting": [r"\blifting\b", r"\bcrane\b", r"\bsling\b", r"\bhoist\b", r"\bload\b", r"\brigging\b"],
    "working_at_height": [r"\bheight\b", r"\bfall\b", r"\bharness\b", r"\bscaffold\b", r"\bplatform\b", r"\bmonkey board\b"],
    "bypassing_safety_controls": [r"\bbypass", r"\bjumper", r"\bdisabled\b", r"\boverride\b", r"\bdefeat"],
}

LSR_TITLES = {
    "work_authorisation": "Work Authorisation",
    "energy_isolation": "Energy Isolation",
    "confined_space": "Confined Space",
    "driving": "Driving",
    "hot_work": "Hot Work",
    "line_of_fire": "Line of Fire",
    "safe_mechanical_lifting": "Safe Mechanical Lifting",
    "working_at_height": "Working at Height",
    "bypassing_safety_controls": "Bypassing Safety Controls",
}


def _count_matches(text: str, patterns: list[str]) -> tuple[int, list[str]]:
    """Count how many patterns match; return (count, matched_snippets)."""
    count = 0
    snippets: list[str] = []
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            count += 1
            snippets.append(m.group(0))
    return count, snippets


def _match_spans(text: str, patterns: list[str]) -> list[dict]:
    """Return match spans with character offsets: {quote, start, end}.

    Offsets are Python string indices (code points). The pipeline converts
    these to UTF-16 offsets for the evidence contract. Each pattern
    contributes at most one span (its first match), and to give reviewers
    readable evidence we widen the span to the surrounding sentence fragment.
    """
    spans: list[dict] = []
    seen: set[tuple[int, int]] = set()
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if not m:
            continue
        # Widen to sentence-ish boundaries around the match
        start = m.start()
        end = m.end()
        left = text.rfind(".", 0, start)
        left = 0 if left == -1 else left + 1
        right = text.find(".", end)
        right = len(text) if right == -1 else right + 1
        # Trim leading whitespace
        while left < start and text[left] in " \n\t":
            left += 1
        key = (left, right)
        if key in seen:
            continue
        seen.add(key)
        spans.append({
            "quote": text[left:right].strip(),
            "start": left,
            "end": right,
        })
    return spans


class FixtureAdapter(ModelAdapter):
    """Deterministic keyword-based analysis adapter."""

    @property
    def model_version(self) -> str:
        return MODEL_VERSION

    async def analyze(self, request: AdapterRequest) -> AdapterResponse:
        start = time.monotonic()
        text = request.narrative

        # --- Detect hazards ---
        hazards: list[dict] = []
        for hazard_kind, patterns in HAZARD_PATTERNS.items():
            count, snippets = _count_matches(text, patterns)
            if count > 0:
                hazards.append({
                    "hazard_kind": hazard_kind,
                    "signal_strength": count,
                    "evidence_snippets": snippets[:3],
                    "evidence_spans": _match_spans(text, patterns)[:2],
                })

        # Sort by signal strength
        hazards.sort(key=lambda h: h["signal_strength"], reverse=True)

        # --- Detect exposure ---
        exposure_count, exposure_snippets = _count_matches(text, EXPOSURE_PATTERNS)
        has_exposure = exposure_count > 0

        # --- Detect control state ---
        failure_count, failure_snippets = _count_matches(text, CONTROL_FAILURE_PATTERNS)
        success_count, success_snippets = _count_matches(text, CONTROL_SUCCESS_PATTERNS)

        # --- Map LSRs ---
        lsr_findings: list[dict] = []
        for rule_id, patterns in LSR_PATTERNS.items():
            count, snippets = _count_matches(text, patterns)
            if count > 0:
                # A rule is "relevant" if hazard signals present;
                # "control_issue" if failure signals present
                control_issue = failure_count > 0 and count >= 1
                lsr_findings.append({
                    "rule_id": rule_id,
                    "official_title": LSR_TITLES[rule_id],
                    "relevance": "relevant" if count >= 2 else "possibly_relevant",
                    "control_issue": "control_gap" if control_issue else "no_issue_identified",
                    "evidence_snippets": snippets[:3],
                    "evidence_spans": _match_spans(text, patterns)[:2],
                    "signal_strength": count,
                })

        lsr_findings.sort(key=lambda r: r["signal_strength"], reverse=True)

        raw = {
            "hazards": hazards,
            "has_exposure": has_exposure,
            "exposure_snippets": exposure_snippets[:3],
            "exposure_spans": _match_spans(text, EXPOSURE_PATTERNS)[:2],
            "control_failure_count": failure_count,
            "control_failure_snippets": failure_snippets[:5],
            "control_failure_spans": _match_spans(text, CONTROL_FAILURE_PATTERNS)[:3],
            "control_success_count": success_count,
            "control_success_snippets": success_snippets[:3],
            "control_success_spans": _match_spans(text, CONTROL_SUCCESS_PATTERNS)[:2],
            "lsr_findings": lsr_findings,
            "narrative_length": len(text),
        }

        duration_ms = int((time.monotonic() - start) * 1000)

        return AdapterResponse(
            raw=raw,
            model_version=MODEL_VERSION,
            prompt_version=PROMPT_VERSION,
            duration_ms=duration_ms,
        )
