"""Evaluation guardrail tests.

These lock in the two claims the project makes about the Luck Test engine
relative to an outcome-trained baseline:

  1. The engine is more outcome-resistant (higher pair consistency).
  2. The engine catches SIF potential well (high recall).

Skipped automatically if scikit-learn is not installed.
"""

import pytest

pytest.importorskip("sklearn")

from app.ml.baseline import run_evaluation


@pytest.mark.asyncio
async def test_engine_more_outcome_resistant_than_baseline():
    report = await run_evaluation()
    engine_consistency = report["engine"]["pair_consistency"]["consistency_rate"]
    baseline_consistency = report["baseline"]["pair_consistency"]["consistency_rate"]
    # The engine should be strictly more consistent across outcome-swapped pairs.
    assert engine_consistency > baseline_consistency
    # And it should be strongly consistent in absolute terms.
    assert engine_consistency >= 0.80


@pytest.mark.asyncio
async def test_engine_recall_is_high():
    report = await run_evaluation()
    # The engine must not miss serious-potential events (few false negatives).
    assert report["engine"]["metrics"]["recall"] >= 0.85


@pytest.mark.asyncio
async def test_baseline_tracks_outcome():
    """Confirm the baseline really did learn outcome bias (sanity check on the
    experimental setup, so the comparison is meaningful)."""
    report = await run_evaluation()
    assert report["baseline"]["metrics"]["outcome_agreement"] >= 0.80
