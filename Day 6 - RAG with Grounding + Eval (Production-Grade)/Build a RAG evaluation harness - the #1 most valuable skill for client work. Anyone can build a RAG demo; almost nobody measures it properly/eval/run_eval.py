"""
run_eval.py — RAG evaluation using RAGAS + Gemini 2.5 Flash as judge.

Pipeline:
  1. Load test_set.jsonl  (30 questions + ground truths)
  2. Run each question through the Day-6 RAG bot  (Retriever → Generator)
  3. Score all 4 RAGAS metrics with Gemini-as-judge
  4. Save results.csv
  5. Write eval_report.md  (aggregates, histograms, best/worst, improvements)
"""

import importlib.util
import json
import os
import sys
from pathlib import Path
from statistics import mean

import pandas as pd
from dotenv import load_dotenv
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_google_vertexai import ChatVertexAI, VertexAIEmbeddings

# ── Paths ──────────────────────────────────────────────────────────────────────
EVAL_DIR    = Path(__file__).resolve().parent
RAG_BOT_DIR = (
    EVAL_DIR.parents[1]
    / "Build a RAG chatbot that cites every claim - exactly the pattern behind Meesho Memory and Apollo content search"
    / "rag_bot"
)

load_dotenv(RAG_BOT_DIR / ".env")

PROJECT  = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION", "us-central1")

# ── Load Retriever + Generator directly from their file paths ─────────────────
def _load_module(name, filepath):
    spec = importlib.util.spec_from_file_location(name, filepath)
    mod  = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

Retriever = _load_module("retriever", RAG_BOT_DIR / "retriever.py").Retriever
Generator = _load_module("generator",  RAG_BOT_DIR / "generator.py").Generator

# ── RAGAS: Gemini 2.5 Flash as judge + embedder ───────────────────────────────
judge_llm = LangchainLLMWrapper(
    ChatVertexAI(model_name="gemini-2.5-flash", project=PROJECT, location=LOCATION)
)
judge_emb = LangchainEmbeddingsWrapper(
    VertexAIEmbeddings(model_name="gemini-embedding-001", project=PROJECT, location=LOCATION)
)

METRICS = [faithfulness, answer_relevancy, context_precision, context_recall]
for _m in METRICS:
    _m.llm = judge_llm
    if hasattr(_m, "embeddings"):
        _m.embeddings = judge_emb

METRIC_COLS = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
LABELS = {
    "faithfulness":      "Faithfulness",
    "answer_relevancy":  "Answer Relevance",
    "context_precision": "Context Precision",
    "context_recall":    "Context Recall",
}


# ── Step 1: run RAG bot on every test question ────────────────────────────────
def build_dataset(test_cases: list[dict]) -> Dataset:
    retriever = Retriever()
    generator = Generator()
    rows = {"question": [], "answer": [], "contexts": [], "ground_truth": []}

    for i, tc in enumerate(test_cases, 1):
        print(f"[{i:02d}/{len(test_cases)}] {tc['question'][:70]}…")
        chunks = retriever.retrieve(tc["question"])
        result = generator.generate(tc["question"], chunks)

        rows["question"].append(tc["question"])
        rows["answer"].append(result["answer"])
        rows["contexts"].append([c.text for c in chunks])
        rows["ground_truth"].append(tc["ground_truth"])

    return Dataset.from_dict(rows)


# ── Step 2: score with RAGAS ──────────────────────────────────────────────────
def run_evaluation(dataset: Dataset):
    print("\nRunning RAGAS evaluation…\n")
    return evaluate(dataset, metrics=METRICS)


# ── Step 3: save results.csv ──────────────────────────────────────────────────
def save_results(result, test_cases: list[dict]) -> pd.DataFrame:
    df = result.to_pandas()
    df.insert(0, "question_id", [tc["id"] for tc in test_cases])
    df["avg_score"] = df[METRIC_COLS].mean(axis=1).round(4)

    df.rename(columns={"answer_relevancy": "answer_relevance"}).loc[
        :, ["question_id", "question", "answer",
            "faithfulness", "answer_relevance",
            "context_precision", "context_recall", "avg_score"]
    ].to_csv(EVAL_DIR / "results.csv", index=False)

    print("Saved results.csv")
    return df


# ── Step 4: write eval_report.md ──────────────────────────────────────────────
def _histogram(values: list, bins: int = 5, width: int = 28) -> list[str]:
    counts = [0] * bins
    for v in values:
        counts[min(int(float(v) * bins), bins - 1)] += 1
    max_c = max(counts) or 1
    return [
        f"  {i/bins:.1f}–{(i+1)/bins:.1f}  {'█' * round(c / max_c * width):<{width}}  {c:2d}"
        for i, c in enumerate(counts)
    ]


def write_report(df: pd.DataFrame):
    agg     = df[METRIC_COLS].mean().round(4)
    overall = agg.mean().round(4)

    lines = [
        "# RAG Evaluation Report", "",
        "## 1. Aggregate Scores", "",
        "| Metric | Score |", "|--------|-------|",
        *[f"| {LABELS[m]} | {agg[m]:.4f} |" for m in METRIC_COLS],
        f"| **Overall Average** | **{overall:.4f}** |",
        "", "---", "",
        "## 2. Score Distributions", "",
    ]

    for m in METRIC_COLS:
        lines += [f"### {LABELS[m]}  (mean = {agg[m]:.3f})", "```",
                  *_histogram(df[m].dropna().tolist()), "```", ""]

    lines += ["---", "", "## 3. Top 3 Best Answers", ""]
    for _, r in df.nlargest(3, "avg_score").iterrows():
        lines += [
            f"### [{r['question_id']}]  avg = {r['avg_score']:.4f}",
            f"**Q:** {r['question']}", "",
            f"**A:** {str(r['answer'])[:500]}", "",
            *[f"- **{LABELS[m]}**: {r[m]:.4f}" for m in METRIC_COLS], "",
        ]

    lines += ["---", "", "## 4. Bottom 3 Worst Answers", ""]
    for _, r in df.nsmallest(3, "avg_score").iterrows():
        weak = [LABELS[m] for m in METRIC_COLS if r[m] < 0.5]
        root_cause = "Low: " + ", ".join(weak) if weak else "Marginal across all metrics"
        lines += [
            f"### [{r['question_id']}]  avg = {r['avg_score']:.4f}",
            f"**Q:** {r['question']}", "",
            f"**A:** {str(r['answer'])[:500]}", "",
            *[f"- **{LABELS[m]}**: {r[m]:.4f}" for m in METRIC_COLS],
            f"**Root cause:** {root_cause}", "",
        ]

    lines += ["---", "", "## 5. Prioritized Improvements", ""]
    for m in sorted(METRIC_COLS, key=lambda m: agg[m]):
        s = agg[m]
        status = "CRITICAL — fix first" if s < 0.5 else "needs improvement" if s < 0.7 else "acceptable"
        lines.append(f"- **{LABELS[m]} ({s:.3f})**: {status}")

    (EVAL_DIR / "eval_report.md").write_text("\n".join(lines), encoding="utf-8")
    print("Saved eval_report.md")


# ── Main ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    test_cases = [
        json.loads(line)
        for line in (EVAL_DIR / "test_set.jsonl").read_text().splitlines()
        if line.strip()
    ]
    print(f"Loaded {len(test_cases)} test cases.\n")

    dataset = build_dataset(test_cases)
    result  = run_evaluation(dataset)
    df      = save_results(result, test_cases)
    write_report(df)

    print("\n── Summary ──────────────────────────────────────")
    for m in METRIC_COLS:
        print(f"  {LABELS[m]:<28} {df[m].mean():.4f}")
    print(f"  {'Overall':<28} {df['avg_score'].mean():.4f}")
