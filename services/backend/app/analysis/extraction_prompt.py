"""Shared extraction prompt + schema for LLM-backed adapters.

The OpenAI and Anthropic adapters both ask the model to return the SAME `raw`
dict shape the fixture adapter produces, so the downstream policy engine and
pipeline are identical regardless of provider. The model does the reading
(hazard energy, exposure, control state, LSR relevance); the deterministic
`policy.py` still makes the Luck Test decision. This keeps the classification
rule auditable and outcome-resistant rather than delegating judgement to a
black box.
"""

from __future__ import annotations

import json

# The hazard/LSR vocabularies the model must map into (must match fixture output).
HAZARD_KINDS = [
    "gravity", "mechanical", "electrical", "pressure",
    "fire_explosion", "toxic_asphyxiation", "vehicle", "other",
]

LSR_IDS = [
    "work_authorisation", "energy_isolation", "confined_space", "driving",
    "hot_work", "line_of_fire", "safe_mechanical_lifting",
    "working_at_height", "bypassing_safety_controls",
]

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

SYSTEM_PROMPT = """You are a process-safety analyst for an oil & gas operator. \
Your ONLY job is to EXTRACT structured facts from an incident/near-miss narrative. \
You do NOT decide whether the event is a serious-injury-or-fatality (SIF) precursor — \
a separate deterministic policy does that. Extract only what the text supports; do \
not infer an outcome that isn't stated. Return STRICT JSON, no prose."""


def build_user_prompt(narrative: str) -> str:
    """Build the extraction instruction for a given narrative."""
    return f"""Analyse the following safety report narrative and extract facts.

Return a JSON object with EXACTLY these keys:
{{
  "hazards": [
    {{"hazard_kind": one of {HAZARD_KINDS},
      "signal_strength": integer 1-5 (how strongly the text supports this hazard),
      "evidence_spans": [{{"quote": "<exact substring from the narrative>",
                           "start": <char index>, "end": <char index>}}]}}
  ],
  "has_exposure": boolean,  // was a person (or people in the area) exposed to the hazard energy?
  "exposure_spans": [{{"quote": "...", "start": int, "end": int}}],
  "control_failure_count": integer,  // count of controls that were absent, failed, or bypassed
  "control_failure_spans": [{{"quote": "...", "start": int, "end": int}}],
  "control_success_count": integer,  // count of controls reported present and effective
  "control_success_spans": [{{"quote": "...", "start": int, "end": int}}],
  "lsr_findings": [
    {{"rule_id": one of {LSR_IDS},
      "official_title": "<matching title>",
      "control_issue": "control_gap" or "no_issue_identified",
      "signal_strength": integer 1-5,
      "evidence_spans": [{{"quote": "...", "start": int, "end": int}}]}}
  ],
  "narrative_length": {len(narrative)}
}}

Rules:
- Every quote MUST be an exact substring of the narrative, with correct start/end char indices.
- "serious" hazard energies: gravity/height, pressure, mechanical (lifting/crushing),
  electrical (>50V), fire/explosion, toxic/asphyxiation, vehicle.
- Do NOT let the OUTCOME (injury or no injury) affect extraction. Extract the hazard,
  exposure, and control state as described, whether or not harm occurred.
- If the narrative is too short/vague to assess, return empty hazards and has_exposure=false.

Narrative:
\"\"\"{narrative}\"\"\"
"""


def coerce_raw(parsed: dict, narrative: str) -> dict:
    """Validate/normalise a model's JSON into the raw contract the pipeline expects.

    Missing keys are defaulted; unknown hazard/LSR ids are dropped. Guarantees the
    shape `policy.apply_policy` and `pipeline.run_analysis` rely on.
    """
    def _spans(items):
        out = []
        for s in items or []:
            q = str(s.get("quote", ""))[:400]
            start = int(s.get("start", 0)) if str(s.get("start", "")).lstrip("-").isdigit() else 0
            end = int(s.get("end", 0)) if str(s.get("end", "")).lstrip("-").isdigit() else 0
            # Repair offsets if they don't match the quote
            if q and narrative[start:end] != q:
                idx = narrative.find(q)
                if idx != -1:
                    start, end = idx, idx + len(q)
            out.append({"quote": q, "start": start, "end": end})
        return out[:3]

    hazards = []
    for h in parsed.get("hazards", []) or []:
        kind = h.get("hazard_kind")
        if kind not in HAZARD_KINDS:
            continue
        hazards.append({
            "hazard_kind": kind,
            "signal_strength": int(h.get("signal_strength", 1) or 1),
            "evidence_snippets": [s["quote"] for s in _spans(h.get("evidence_spans"))],
            "evidence_spans": _spans(h.get("evidence_spans")),
        })

    lsr = []
    for r in parsed.get("lsr_findings", []) or []:
        rid = r.get("rule_id")
        if rid not in LSR_IDS:
            continue
        lsr.append({
            "rule_id": rid,
            "official_title": LSR_TITLES.get(rid, rid),
            "relevance": "relevant" if int(r.get("signal_strength", 1) or 1) >= 2 else "possibly_relevant",
            "control_issue": r.get("control_issue", "no_issue_identified"),
            "evidence_snippets": [s["quote"] for s in _spans(r.get("evidence_spans"))],
            "evidence_spans": _spans(r.get("evidence_spans")),
            "signal_strength": int(r.get("signal_strength", 1) or 1),
        })

    return {
        "hazards": hazards,
        "has_exposure": bool(parsed.get("has_exposure", False)),
        "exposure_snippets": [s["quote"] for s in _spans(parsed.get("exposure_spans"))],
        "exposure_spans": _spans(parsed.get("exposure_spans")),
        "control_failure_count": int(parsed.get("control_failure_count", 0) or 0),
        "control_failure_snippets": [s["quote"] for s in _spans(parsed.get("control_failure_spans"))],
        "control_failure_spans": _spans(parsed.get("control_failure_spans")),
        "control_success_count": int(parsed.get("control_success_count", 0) or 0),
        "control_success_snippets": [s["quote"] for s in _spans(parsed.get("control_success_spans"))],
        "control_success_spans": _spans(parsed.get("control_success_spans")),
        "lsr_findings": lsr,
        "narrative_length": len(narrative),
    }


def safe_json_loads(text: str) -> dict:
    """Parse model output, tolerating code fences and leading/trailing prose."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
    # Find the outermost JSON object
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        text = text[start : end + 1]
    return json.loads(text)
