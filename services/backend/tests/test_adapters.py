"""Tests for the LLM adapter contract (no API calls).

These cover the provider-agnostic `coerce_raw` normalisation and JSON parsing
that both the OpenAI and Anthropic adapters rely on, so the LLM path has
coverage without needing API keys.
"""

from app.analysis import extraction_prompt as ep
from app.analysis.policy import apply_policy


NARRATIVE = (
    "During well-head maintenance, a rigger was working at 6 meters height on the "
    "monkey board without a fall arrest harness. His harness was damaged and he "
    "decided to proceed. No injury occurred."
)


def test_safe_json_loads_strips_fences():
    assert ep.safe_json_loads('```json\n{"a": 1}\n```') == {"a": 1}
    assert ep.safe_json_loads('here you go: {"b": 2} thanks') == {"b": 2}


def test_coerce_raw_repairs_offsets_and_drops_unknowns():
    model_json = {
        "hazards": [
            {"hazard_kind": "gravity", "signal_strength": 3,
             "evidence_spans": [{"quote": "6 meters height", "start": 0, "end": 0}]},
            {"hazard_kind": "not_a_real_kind", "signal_strength": 5, "evidence_spans": []},
        ],
        "has_exposure": True,
        "control_failure_count": 2,
        "control_failure_spans": [{"quote": "without a fall arrest harness", "start": 0, "end": 0}],
        "control_success_count": 0,
        "lsr_findings": [
            {"rule_id": "working_at_height", "official_title": "Working at Height",
             "control_issue": "control_gap", "signal_strength": 3, "evidence_spans": []},
            {"rule_id": "invalid_rule", "signal_strength": 4},
        ],
    }
    raw = ep.coerce_raw(model_json, NARRATIVE)

    # Unknown hazard + rule dropped
    assert [h["hazard_kind"] for h in raw["hazards"]] == ["gravity"]
    assert [r["rule_id"] for r in raw["lsr_findings"]] == ["working_at_height"]

    # Offset repair: the 0,0 span was corrected to the real location of the quote
    span = raw["hazards"][0]["evidence_spans"][0]
    assert NARRATIVE[span["start"]:span["end"]] == "6 meters height"


def test_coerced_raw_flows_through_policy():
    """A model-shaped raw dict must classify the same way the fixture path does."""
    model_json = {
        "hazards": [{"hazard_kind": "gravity", "signal_strength": 3,
                     "evidence_spans": [{"quote": "6 meters height",
                                         "start": NARRATIVE.find("6 meters height"),
                                         "end": NARRATIVE.find("6 meters height") + 15}]}],
        "has_exposure": True,
        "control_failure_count": 2,
        "control_success_count": 0,
        "lsr_findings": [],
    }
    raw = ep.coerce_raw(model_json, NARRATIVE)
    policy = apply_policy(raw)
    assert policy["candidate_label"] == "sif_potential"
    assert policy["interpretation"] == "serious_exposure"
