"""Tests for the Luck Test analysis pipeline — the core value proposition.

These verify the two defining properties of the classifier:
  - OUTCOME RESISTANCE: classification does not depend on whether harm occurred
  - CONTROL SENSITIVITY: effective controls flip a scenario to non-SIF

Run with: pytest tests/test_luck_test.py
"""

import pytest

from app.analysis.pipeline import run_analysis


async def _classify(text: str):
    result, _ = await run_analysis(
        text,
        analysis_id="test",
        report_revision_id="test",
        provider="fixture",
    )
    return result


@pytest.mark.asyncio
async def test_outcome_resistance_near_miss_equals_injury():
    """A fall from height without a harness is SIF-potential whether or not
    the worker was actually injured."""
    base = (
        "A worker was on the monkey board at 6 meters height without a "
        "fall arrest harness. The harness was damaged and he proceeded anyway."
    )
    near_miss = base + " No injury occurred."
    injury = base + " He fell and was seriously injured."

    r_near = await _classify(near_miss)
    r_injury = await _classify(injury)

    assert r_near.candidate_label.value == "sif_potential"
    assert r_near.candidate_label == r_injury.candidate_label


@pytest.mark.asyncio
async def test_control_sensitivity_effective_controls_flip_label():
    """The same height scenario with controls in place is non-SIF."""
    controlled = (
        "A worker was on the monkey board at 6 meters height. His fall arrest "
        "harness was worn correctly and inspection was up to date. The permit "
        "was valid. Work proceeded safely."
    )
    result = await _classify(controlled)
    assert result.candidate_label.value == "non_sif_potential"
    assert result.interpretation.value == "controls_reported"


@pytest.mark.asyncio
async def test_insufficient_information_triggers_clarification():
    """A vague narrative is flagged for clarification rather than misclassified."""
    result = await _classify("Something happened at the site.")
    assert result.interpretation.value == "insufficient_information"
    assert result.clarification_question is not None


@pytest.mark.asyncio
async def test_process_safety_hazard_area_exposure():
    """A large gas leak in a hazardous area with failed detectors is SIF-potential
    even without a named exposed individual (area-level exposure)."""
    leak = (
        "A significant methane leak was detected at the compressor inlet flange, "
        "estimated at 50 kg/hour, in a Zone 1 hazardous area. Two of four gas "
        "detectors were in fault mode and had not been repaired. The leak had "
        "gone undetected for several days."
    )
    result = await _classify(leak)
    assert result.candidate_label.value == "sif_potential"


@pytest.mark.asyncio
async def test_evidence_spans_offsets_round_trip():
    """Evidence spans carry UTF-16 offsets that map back to the exact quote,
    and findings link to evidence ids that exist."""
    text = (
        "A rigger was working at 6 meters height on the monkey board without a "
        "fall arrest harness. The harness was damaged and he proceeded."
    )
    result = await _classify_with_text(text)

    assert len(result.evidence) > 0
    u16 = text.encode("utf-16-le")
    for ev in result.evidence:
        sub = u16[ev.start_utf16 * 2 : ev.end_utf16 * 2].decode("utf-16-le")
        assert sub.strip() == ev.exact_quote.strip()

    all_ids = {e.id for e in result.evidence}
    for f in result.facts:
        for eid in f.evidence_ids:
            assert eid in all_ids


async def _classify_with_text(text: str):
    from app.analysis.pipeline import run_analysis

    result, _ = await run_analysis(
        text, analysis_id="test", report_revision_id="seg-1", provider="fixture"
    )
    return result


@pytest.mark.asyncio
async def test_lsr_mapping_populated_for_relevant_scenario():
    """A lifting scenario maps to the Safe Mechanical Lifting rule."""
    lifting = (
        "While lifting a 2.8-ton BOP stack with the rig crane, the main lifting "
        "sling showed visible strand breakage. Two workers were in the red zone "
        "beneath the load."
    )
    result = await _classify(lifting)
    rule_ids = {f.rule_id.value for f in result.lsr_findings}
    assert "safe_mechanical_lifting" in rule_ids or "line_of_fire" in rule_ids
