"""
run_eval.py — Compare 4 RAG configurations using Gemini as a manual judge.

Configs : naive | reranked | contextual | both
Metrics : faithfulness | answer_relevancy | context_precision | context_recall
Outputs : results.csv, lift_report.md
"""

import importlib.util
import json
import os
import re
import sys
import time
from pathlib import Path
from statistics import mean

import pandas as pd
from dotenv import load_dotenv
from google import genai

# ── Paths ─────────────────────────────────────────────────────────────────────
PROD_DIR    = Path(__file__).resolve().parent
RAG_BOT_DIR = (
    PROD_DIR.parents[1]
    / "Build a RAG chatbot that cites every claim - exactly the pattern behind Meesho Memory and Apollo content search"
    / "rag_bot"
)
EVAL_DIR = (
    PROD_DIR.parents[1]
    / "Build a RAG evaluation harness - the #1 most valuable skill for client work. Anyone can build a RAG demo; almost nobody measures it properly"
    / "eval"
)

load_dotenv(RAG_BOT_DIR / ".env")
PROJECT  = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION", "us-central1")

# ── Load RAG modules ──────────────────────────────────────────────────────────
def _load_module(name, filepath):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, filepath)
    mod  = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

Retriever = _load_module("retriever", RAG_BOT_DIR / "retriever.py").Retriever
Generator = _load_module("generator",  RAG_BOT_DIR / "generator.py").Generator

sys.path.insert(0, str(PROD_DIR))
from reranker       import ReRankingRetriever   # noqa: E402
from contextualizer import ContextualRetriever  # noqa: E402

# ── Gemini judge ──────────────────────────────────────────────────────────────
judge       = genai.Client(vertexai=True, project=PROJECT, location=LOCATION)
JUDGE_MODEL = "gemini-2.5-flash"

METRIC_COLS = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
LABELS = {
    "faithfulness":      "Faithfulness",
    "answer_relevancy":  "Answer Relevance",
    "context_precision": "Context Precision",
    "context_recall":    "Context Recall",
}

# ── Judge prompts (each returns a 0.0–1.0 score) ─────────────────────────────
PROMPTS = {
    "faithfulness": """\
Score how faithful the answer is to the context (0.0–1.0).
1.0 = every claim is supported by the context
0.5 = some claims are not in the context
0.0 = answer contradicts or ignores the context

CONTEXT:
{context}

ANSWER:
{answer}

Reply with a single number only.""",

    "answer_relevancy": """\
Score how well the answer addresses the question (0.0–1.0).
1.0 = directly and completely answers the question
0.5 = partial or vague answer
0.0 = off-topic

QUESTION: {question}
ANSWER:   {answer}

Reply with a single number only.""",

    "context_precision": """\
Score how relevant the retrieved context chunks are to the question (0.0–1.0).
1.0 = every chunk is useful for answering the question
0.5 = mix of relevant and irrelevant chunks
0.0 = chunks are not useful

QUESTION: {question}

CONTEXT:
{context}

Reply with a single number only.""",

    "context_recall": """\
Score how much of the ground-truth answer is covered by the context (0.0–1.0).
1.0 = context contains all information needed to produce the ground truth
0.5 = context covers roughly half the ground truth
0.0 = context is missing most ground truth information

GROUND TRUTH: {ground_truth}

CONTEXT:
{context}

Reply with a single number only.""",
}

# ── Scoring ───────────────────────────────────────────────────────────────────
def _score(prompt: str) -> float:
    """Call Gemini, extract and return the float score."""
    try:
        resp  = judge.models.generate_content(model=JUDGE_MODEL, contents=prompt)
        match = re.search(r"\d+\.?\d*", resp.text or "")
        return round(min(max(float(match.group()), 0.0), 1.0), 4) if match else 0.0
    except Exception as e:
        print(f"    [judge error] {e}")
        return 0.0


def score_row(question, answer, contexts, ground_truth) -> dict:
    ctx = "\n\n".join(f"[{i+1}] {c}" for i, c in enumerate(contexts))
    scores = {
        "faithfulness":      _score(PROMPTS["faithfulness"].format(context=ctx, answer=answer)),
        "answer_relevancy":  _score(PROMPTS["answer_relevancy"].format(question=question, answer=answer)),
        "context_precision": _score(PROMPTS["context_precision"].format(question=question, context=ctx)),
        "context_recall":    _score(PROMPTS["context_recall"].format(ground_truth=ground_truth, context=ctx)),
    }
    time.sleep(0.5)  # rate-limit buffer
    return scores


# ── Run one config ────────────────────────────────────────────────────────────
def run_config(retriever, generator, test_cases) -> pd.DataFrame:
    rows = []
    for i, tc in enumerate(test_cases, 1):
        print(f"  [{i:02d}/{len(test_cases)}] {tc['question'][:65]}…")
        chunks = retriever.retrieve(tc["question"])
        result = generator.generate(tc["question"], chunks)
        scores = score_row(tc["question"], result["answer"], [c.text for c in chunks], tc["ground_truth"])
        rows.append(scores)
        print(f"           faith={scores['faithfulness']}  rel={scores['answer_relevancy']}  "
              f"prec={scores['context_precision']}  rec={scores['context_recall']}")
    return pd.DataFrame(rows)


# ── Lift report ───────────────────────────────────────────────────────────────
def _pct(new_val, base_val) -> str:
    if base_val == 0:
        return "N/A"
    v = (new_val - base_val) / base_val * 100
    return f"{'+' if v >= 0 else ''}{v:.1f}%"


def write_lift_report(combined: pd.DataFrame):
    configs = ["reranked", "contextual", "both"]
    agg = {}
    for cfg in ["naive"] + configs:
        agg[cfg] = {m: combined[f"{cfg}_{m}"].mean() for m in METRIC_COLS}
        agg[cfg]["avg"] = mean(list(agg[cfg].values()))

    lines = [
        "# Production RAG: Lift Report", "",
        "> Judge: Gemini Flash scoring faithfulness / relevancy / precision / recall", "",
        "## 1. Aggregate Scores", "",
        "| Metric | Naive | +Reranker | +Contextual | +Both |",
        "|--------|-------|-----------|-------------|-------|",
    ]
    for m in METRIC_COLS + ["avg"]:
        label = LABELS.get(m, "Overall Average")
        lines.append("| " + label + " | " + " | ".join(f"{agg[c][m]:.4f}" for c in ["naive"] + configs) + " |")

    lines += ["", "## 2. Lift vs Naive", "",
              "| Metric | +Reranker | +Contextual | +Both |",
              "|--------|-----------|-------------|-------|"]
    for m in METRIC_COLS + ["avg"]:
        label = LABELS.get(m, "Overall Average")
        lines.append("| " + label + " | " + " | ".join(_pct(agg[c][m], agg["naive"][m]) for c in configs) + " |")

    best = max(configs, key=lambda c: agg[c]["avg"])
    lines += [
        "", "## 3. Recommendation", "",
        f"**Ship `{best}`** — {_pct(agg[best]['avg'], agg['naive']['avg'])} overall lift.", "",
        f"- Reranker   : {_pct(agg['reranked']['avg'],   agg['naive']['avg'])} — no prep, tiny per-query cost",
        f"- Contextual : {_pct(agg['contextual']['avg'], agg['naive']['avg'])} — one-time prep, zero per-query cost",
        f"- Both       : {_pct(agg['both']['avg'],       agg['naive']['avg'])} — compounds both gains",
    ]

    (PROD_DIR / "lift_report.md").write_text("\n".join(lines), encoding="utf-8")
    print("Saved lift_report.md")


# ── Main ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    test_cases = [json.loads(l) for l in (EVAL_DIR / "test_set.jsonl").read_text().splitlines() if l.strip()]
    print(f"Loaded {len(test_cases)} test cases.\n")

    generator = Generator()
    CONFIGS = [
        ("naive",      Retriever()),
        ("reranked",   ReRankingRetriever(fetch_k=20, final_k=5)),
        ("contextual", ContextualRetriever()),
        ("both",       ReRankingRetriever(base_retriever=ContextualRetriever(), fetch_k=20, final_k=5)),
    ]

    dfs = {}
    for cfg_name, retriever in CONFIGS:
        print(f"\n{'='*55}\nConfig: {cfg_name.upper()}\n{'='*55}")
        dfs[cfg_name] = run_config(retriever, generator, test_cases)
        print(f"  → avg: {dfs[cfg_name][METRIC_COLS].mean().mean():.4f}")

    # Wide CSV: one row per question, columns = {config}_{metric}
    combined = pd.DataFrame({"question_id": [tc["id"] for tc in test_cases]})
    for cfg_name, df in dfs.items():
        for m in METRIC_COLS:
            combined[f"{cfg_name}_{m}"] = df[m].values
    combined.to_csv(PROD_DIR / "results.csv", index=False)
    print(f"\nSaved results.csv  ({len(combined)} rows × {len(combined.columns)} cols)")

    write_lift_report(combined)

    # Summary table
    print(f"\n{'Metric':<24}", end="")
    for cfg_name, _ in CONFIGS:
        print(f"  {cfg_name:>12}", end="")
    print()
    for m in METRIC_COLS:
        print(f"  {LABELS[m]:<22}", end="")
        for cfg_name, _ in CONFIGS:
            print(f"  {dfs[cfg_name][m].mean():>12.4f}", end="")
        print()
    print(f"  {'Overall':<22}", end="")
    for cfg_name, _ in CONFIGS:
        print(f"  {dfs[cfg_name][METRIC_COLS].mean().mean():>12.4f}", end="")
    print()
