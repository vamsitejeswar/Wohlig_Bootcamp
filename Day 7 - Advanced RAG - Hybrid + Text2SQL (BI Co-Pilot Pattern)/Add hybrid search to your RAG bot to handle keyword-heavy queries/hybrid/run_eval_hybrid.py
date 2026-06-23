"""
run_eval_hybrid.py
Compare dense-only vs hybrid on 40 questions.
Gemini Flash judges each answer on 4 metrics.
Saves results.csv and prints a summary table.
"""

import importlib.util
import json
import os
import re
import sys
import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from google import genai

_HERE = Path(__file__).resolve().parent
RAG_BOT_DIR = (
    _HERE.parents[2]
    / "Day 6 - RAG with Grounding + Eval (Production-Grade)"
    / "Build a RAG chatbot that cites every claim - exactly the pattern behind Meesho Memory and Apollo content search"
    / "rag_bot"
)
load_dotenv(RAG_BOT_DIR / ".env")

PROJECT  = os.getenv("PROJECT_ID", "wohlig")
LOCATION = os.getenv("LOCATION", "us-central1")
sys.path.insert(0, str(_HERE))


# ── Load Day-6 modules ─────────────────────────────────────────────────────────
def _load(name, path):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    mod  = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

DenseRetriever = _load("retriever", RAG_BOT_DIR / "retriever.py").Retriever
Generator      = _load("generator",  RAG_BOT_DIR / "generator.py").Generator

from retriever_hybrid import HybridRetriever


# ── Gemini judge ───────────────────────────────────────────────────────────────
judge = genai.Client(vertexai=True, project=PROJECT, location=LOCATION)

PROMPTS = {
    "faithfulness": """Score 0.0-1.0: how faithful is the answer to the context?
1.0=all claims in context, 0.0=contradicts context
CONTEXT: {context}
ANSWER: {answer}
Reply with a single number only.""",

    "answer_relevancy": """Score 0.0-1.0: how well does the answer address the question?
1.0=complete answer, 0.0=off-topic
QUESTION: {question}
ANSWER: {answer}
Reply with a single number only.""",

    "context_precision": """Score 0.0-1.0: how relevant are the retrieved chunks to the question?
1.0=all chunks useful, 0.0=no chunks useful
QUESTION: {question}
CONTEXT: {context}
Reply with a single number only.""",

    "context_recall": """Score 0.0-1.0: how much of the ground truth is covered by the context?
1.0=context covers everything, 0.0=context covers nothing
GROUND TRUTH: {ground_truth}
CONTEXT: {context}
Reply with a single number only.""",
}


def judge_score(prompt):
    for attempt in range(3):
        try:
            resp = judge.models.generate_content(model="gemini-2.5-flash", contents=prompt)
            m = re.search(r"\d+\.?\d*", resp.text or "")
            return round(min(max(float(m.group()), 0.0), 1.0), 4) if m else 0.0
        except Exception as e:
            print(f"      [retry {attempt+1}] {e}")
            time.sleep(10 * (attempt + 1))
    return 0.0


def score_question(question, answer, contexts, ground_truth):
    ctx = "\n\n".join(f"[{i+1}] {c}" for i, c in enumerate(contexts))
    time.sleep(2)   # avoid 429
    return {
        "faithfulness":      judge_score(PROMPTS["faithfulness"].format(context=ctx, answer=answer)),
        "answer_relevancy":  judge_score(PROMPTS["answer_relevancy"].format(question=question, answer=answer)),
        "context_precision": judge_score(PROMPTS["context_precision"].format(question=question, context=ctx)),
        "context_recall":    judge_score(PROMPTS["context_recall"].format(ground_truth=ground_truth, context=ctx)),
    }


# ── Run one retriever config on all questions ──────────────────────────────────
METRICS = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]

def run_config(retriever, generator, test_cases, label):
    rows = []
    print(f"\n{'='*55}\nConfig: {label}\n{'='*55}")
    for i, tc in enumerate(test_cases, 1):
        print(f"  [{i:02d}/{len(test_cases)}] [{tc['query_type']:8s}] {tc['question'][:55]}…")
        chunks  = retriever.retrieve(tc["question"])
        result  = generator.generate(tc["question"], chunks)
        scores  = score_question(
            tc["question"], result["answer"],
            [c.text for c in chunks], tc["ground_truth"]
        )
        rows.append(scores)
        print(f"           F={scores['faithfulness']}  R={scores['answer_relevancy']}  "
              f"P={scores['context_precision']}  Rec={scores['context_recall']}")
    return pd.DataFrame(rows)


# ── Summary ────────────────────────────────────────────────────────────────────
def print_summary(combined):
    def pct(n, b): return f"{(n-b)/b*100:+.1f}%" if b else "N/A"

    print(f"\n{'='*65}")
    print(f"{'Query type':<12} {'Metric':<22} {'Dense':>7} {'Hybrid':>7} {'Lift':>8}")
    print(f"{'-'*65}")

    for qtype in ["semantic", "keyword", "ALL"]:
        mask = combined["query_type"] == qtype if qtype != "ALL" else [True]*len(combined)
        sub  = combined[mask]
        for m in METRICS + ["avg"]:
            dcol = f"dense_{m}"  if m != "avg" else "dense_avg"
            hcol = f"hybrid_{m}" if m != "avg" else "hybrid_avg"
            d = sub[dcol].mean()
            h = sub[hcol].mean()
            label = m if m != "avg" else "OVERALL"
            print(f"  {qtype:<10} {label:<22} {d:>7.4f} {h:>7.4f} {pct(h,d):>8}")
        print()


# ── Main ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    test_cases = [
        json.loads(l) for l in
        (_HERE / "test_set_extended.jsonl").read_text().splitlines() if l.strip()
    ]
    print(f"Loaded {len(test_cases)} questions "
          f"({sum(1 for t in test_cases if t['query_type']=='semantic')} semantic, "
          f"{sum(1 for t in test_cases if t['query_type']=='keyword')} keyword)\n")

    generator = Generator()

    dense_df  = run_config(DenseRetriever(), generator, test_cases, "DENSE-ONLY")
    hybrid_df = run_config(HybridRetriever(), generator, test_cases, "HYBRID (Dense + BM25 + RRF)")

    # Build results CSV
    combined = pd.DataFrame({
        "question_id": [t["id"]         for t in test_cases],
        "query_type":  [t["query_type"] for t in test_cases],
        "question":    [t["question"]   for t in test_cases],
    })
    for m in METRICS:
        combined[f"dense_{m}"]  = dense_df[m].values
        combined[f"hybrid_{m}"] = hybrid_df[m].values

    combined["dense_avg"]  = dense_df[METRICS].mean(axis=1).round(4)
    combined["hybrid_avg"] = hybrid_df[METRICS].mean(axis=1).round(4)
    combined["lift"]       = (combined["hybrid_avg"] - combined["dense_avg"]).round(4)

    combined.to_csv(_HERE / "results.csv", index=False)
    print(f"\nSaved results.csv")

    print_summary(combined)
