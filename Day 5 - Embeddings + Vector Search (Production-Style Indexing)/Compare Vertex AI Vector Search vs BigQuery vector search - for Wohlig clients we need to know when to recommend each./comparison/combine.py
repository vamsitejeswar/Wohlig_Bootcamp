# =========================================================
# combine.py
# Merge VSS + BQ benchmark results into results.csv
# Run after: vss_eval.py and bq_vector/query.py
# =========================================================

import csv
import sys
from pathlib import Path

# =========================================================
# PATHS
# =========================================================

BASE_DIR   = Path(__file__).parent

VSS_FILE   = BASE_DIR / "results_vss.csv"
BQ_FILE    = BASE_DIR / "results_bq.csv"
OUTPUT_CSV = BASE_DIR / "results.csv"

# =========================================================
# LOAD CSV
# =========================================================

def load_csv(path):

    if not path.exists():

        sys.exit(
            f"\nMissing: {path}"
            f"\nRun the corresponding eval script first."
        )

    rows = {}

    with open(path, "r", newline="") as f:

        for row in csv.DictReader(f):

            qid = row["question_id"].strip().lower()

            rows[qid] = row

    return rows

# =========================================================
# MERGE
# =========================================================

def main():

    vss = load_csv(VSS_FILE)
    bq  = load_csv(BQ_FILE)

    all_ids = sorted(
        set(vss) | set(bq),
        key=lambda x: int(x.lstrip("q"))
    )

    rows = []

    for qid in all_ids:

        v = vss.get(qid, {})
        b = bq.get(qid, {})

        rows.append({
            "question_id":    qid,
            "vss_latency_ms": v.get("vss_latency_ms", ""),
            "bq_latency_ms":  b.get("bq_latency_ms", ""),
            "vss_recall_10":  v.get("vss_recall_10", ""),
            "bq_recall_10":   b.get("bq_recall_10", ""),
            "bytes_processed": b.get("bytes_processed", ""),
            "cost_usd":       b.get("cost_usd", "")
        })

    # =====================================================
    # WRITE
    # =====================================================

    fieldnames = [
        "question_id",
        "vss_latency_ms",
        "bq_latency_ms",
        "vss_recall_10",
        "bq_recall_10",
        "bytes_processed",
        "cost_usd"
    ]

    with open(OUTPUT_CSV, "w", newline="") as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(rows)

    # =====================================================
    # SUMMARY
    # =====================================================

    vss_lats = [
        float(r["vss_latency_ms"])
        for r in rows
        if r["vss_latency_ms"]
    ]

    bq_lats = [
        float(r["bq_latency_ms"])
        for r in rows
        if r["bq_latency_ms"]
    ]

    vss_recalls = [
        float(r["vss_recall_10"])
        for r in rows
        if r["vss_recall_10"]
    ]

    bq_recalls = [
        float(r["bq_recall_10"])
        for r in rows
        if r["bq_recall_10"]
    ]

    print(
        f"\nSaved {len(rows)} rows to {OUTPUT_CSV}"
    )

    print(
        "\n==================================="
    )

    print(
        f"\n{'Metric':<28} {'VSS':>10} {'BigQuery':>10}"
    )

    print("-" * 50)

    if vss_lats and bq_lats:

        print(
            f"\n{'Avg latency (ms)':<28} "
            f"{sum(vss_lats)/len(vss_lats):>10.1f} "
            f"{sum(bq_lats)/len(bq_lats):>10.1f}"
        )

        print(
            f"\n{'Min latency (ms)':<28} "
            f"{min(vss_lats):>10.1f} "
            f"{min(bq_lats):>10.1f}"
        )

        print(
            f"\n{'Max latency (ms)':<28} "
            f"{max(vss_lats):>10.1f} "
            f"{max(bq_lats):>10.1f}"
        )

    if vss_recalls and bq_recalls:

        print(
            f"\n{'Avg recall@10':<28} "
            f"{sum(vss_recalls)/len(vss_recalls):>10.3f} "
            f"{sum(bq_recalls)/len(bq_recalls):>10.3f}"
        )

    print(
        "\n==================================="
    )

# =========================================================
# ENTRY
# =========================================================

if __name__ == "__main__":

    main()
