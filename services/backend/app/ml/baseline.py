"""Baseline classifier + evaluation harness.

The baseline is a TF-IDF + logistic regression pipeline — a standard, reasonable
text classifier. The point of the comparison is NOT that TF-IDF is a bad algorithm;
it is that **the labels you train on decide what you learn**.

In real incident systems, historical SIF labels are largely assigned by OUTCOME
severity — a fatality is filed as serious, a near-miss as minor — because that is
what was visible after the fact. So we train the baseline on *outcome-derived*
labels (a narrative is "serious" if it contains severe-outcome words like
"fatal"/"died"/"hospital"). That is the realistic supervision signal.

We then evaluate BOTH models against GROUND TRUTH, where the label is SIF
*potential* (hazard + exposure + control failure), independent of outcome.

Two metrics:
  - accuracy vs. ground truth
  - PAIR CONSISTENCY: on each outcome-swapped pair, does the model give both
    members the same label? Ground truth requires yes.

The eval reports whatever it measures — no conclusion is hard-coded.

Run:  python -m app.ml.baseline
"""

from __future__ import annotations

import asyncio
import re
import uuid
from collections import defaultdict

from app.ml.eval_dataset import EVAL_RECORDS

# Severe-outcome cues — how an outcome-biased labeller would tag "serious".
_SEVERE_OUTCOME = re.compile(
    r"\b(fatal|fatally|died|dead|death|killed|electrocuted|hospital|"
    r"second-degree|crush injuries|pronounced dead|injuring|injured)\b",
    re.IGNORECASE,
)


def outcome_derived_label(text: str) -> int:
    """Label a narrative the way an outcome-biased historical process would:
    1 (serious) if it mentions a severe outcome, else 0."""
    return 1 if _SEVERE_OUTCOME.search(text) else 0


def _train_baseline(train_texts: list[str], train_labels: list[int]):
    """Train a TF-IDF + logistic regression baseline."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline

    model = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
    ])
    model.fit(train_texts, train_labels)
    return model


async def _engine_predict(text: str) -> int:
    """Predict with the Luck Test engine. Returns 1 for sif_potential."""
    from app.analysis.pipeline import run_analysis

    result, _ = await run_analysis(
        text, analysis_id=str(uuid.uuid4()), report_revision_id="eval", provider="fixture"
    )
    return 1 if result.candidate_label and result.candidate_label.value == "sif_potential" else 0


def _metrics(y_true: list[int], y_pred: list[int]) -> dict:
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)
    n = len(y_true)
    acc = (tp + tn) / n if n else 0.0
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    return {"accuracy": acc, "precision": prec, "recall": rec, "f1": f1,
            "tp": tp, "tn": tn, "fp": fp, "fn": fn}


def _pair_consistency(records, preds) -> dict:
    """Fraction of outcome-swapped pairs given a consistent label."""
    by_pair: dict[str, list[int]] = defaultdict(list)
    for (_, _, pair_id), pred in zip(records, preds):
        by_pair[pair_id].append(pred)
    pairs = {pid: ps for pid, ps in by_pair.items() if len(ps) > 1}
    consistent = sum(1 for ps in pairs.values() if len(set(ps)) == 1)
    return {
        "pairs_total": len(pairs),
        "pairs_consistent": consistent,
        "consistency_rate": consistent / len(pairs) if pairs else 1.0,
    }


async def run_evaluation() -> dict:
    """Run the full evaluation and return a metrics report."""
    texts = [r[0] for r in EVAL_RECORDS]
    labels = [r[1] for r in EVAL_RECORDS]

    # --- Engine predictions (no training needed) ---
    engine_preds = [await _engine_predict(t) for t in texts]
    engine_metrics = _metrics(labels, engine_preds)
    engine_consistency = _pair_consistency(EVAL_RECORDS, engine_preds)

    # --- Baseline: trained on OUTCOME-DERIVED labels (the realistic signal) ---
    # We add lightly-perturbed copies so TF-IDF has enough signal to fit; labels
    # come from outcome cues, not ground truth. Evaluation is still vs. ground truth.
    outcome_labels = [outcome_derived_label(t) for t in texts]
    train_texts = texts + [t.replace("worker", "operative") for t in texts]
    train_labels = outcome_labels + outcome_labels

    try:
        baseline = _train_baseline(train_texts, train_labels)
        baseline_preds = [int(p) for p in baseline.predict(texts)]
        baseline_metrics = _metrics(labels, baseline_preds)
        baseline_consistency = _pair_consistency(EVAL_RECORDS, baseline_preds)
        # How well did the baseline just reproduce outcome bias?
        outcome_agreement = sum(
            1 for p, o in zip(baseline_preds, outcome_labels) if p == o
        ) / len(texts)
        baseline_metrics["outcome_agreement"] = round(outcome_agreement, 2)
        baseline_available = True
    except ImportError:
        baseline_metrics = {}
        baseline_consistency = {}
        baseline_available = False

    return {
        "dataset_size": len(EVAL_RECORDS),
        "engine": {
            "metrics": engine_metrics,
            "pair_consistency": engine_consistency,
        },
        "baseline": {
            "available": baseline_available,
            "metrics": baseline_metrics,
            "pair_consistency": baseline_consistency,
        },
    }


def _fmt(m: dict) -> str:
    if not m:
        return "  (unavailable — install scikit-learn)"
    return (f"  accuracy={m['accuracy']:.2f}  precision={m['precision']:.2f}  "
            f"recall={m['recall']:.2f}  f1={m['f1']:.2f}  "
            f"(tp={m['tp']} tn={m['tn']} fp={m['fp']} fn={m['fn']})")


def main():
    report = asyncio.run(run_evaluation())
    print("=" * 68)
    print(f"SIF Sentinel — Evaluation ({report['dataset_size']} labelled narratives)")
    print("=" * 68)
    print("\nLuck Test engine:")
    print(_fmt(report["engine"]["metrics"]))
    ec = report["engine"]["pair_consistency"]
    print(f"  pair consistency: {ec['pairs_consistent']}/{ec['pairs_total']} "
          f"({ec['consistency_rate']*100:.0f}%)")

    print("\nTF-IDF + LogReg baseline (trained on outcome-derived labels):")
    print(_fmt(report["baseline"]["metrics"]))
    if report["baseline"]["available"]:
        bc = report["baseline"]["pair_consistency"]
        oa = report["baseline"]["metrics"].get("outcome_agreement")
        print(f"  pair consistency: {bc['pairs_consistent']}/{bc['pairs_total']} "
              f"({bc['consistency_rate']*100:.0f}%)")
        print(f"  agreement with outcome-bias labels: {oa}")
        print("\nRead the numbers above, not a slogan: the baseline's accuracy vs.")
        print("ground truth and its pair consistency show how much it tracks OUTCOME")
        print("rather than POTENTIAL. The engine's pair-consistency is its outcome")
        print("resistance. (Dataset is small — this is an illustration, not a benchmark.)")
    print("=" * 68)


if __name__ == "__main__":
    main()
