"""
Test 3 prompting styles against 30 support tickets using Gemini.
"""
import csv
import time
from pathlib import Path
import google.genai as genai
from google.genai import errors

DIR = Path(__file__).parent
CATEGORIES = ["Refund", "Shipping", "Login", "Payment", "Account", "Product Quality", "Order Change", "Other"]

tickets = list(csv.DictReader(open(DIR / "tickets.csv")))

zero_shot = (DIR / "prompts/zero_shot.txt").read_text()
few_shot  = (DIR / "prompts/few_shot.txt").read_text()
role_base = (DIR / "prompts/role_based.txt").read_text()

client = genai.Client(vertexai=True, project="wohlig", location="us-central1")
MODEL = "gemini-2.5-flash"

def classify(name, template):
    preds = []
    for i, t in enumerate(tickets):
        prompt = template.replace("{ticket_text}", t["ticket_text"])
        for attempt in range(5):
            try:
                resp = client.models.generate_content(model=MODEL, contents=prompt)
                break
            except errors.ClientError as e:
                if "429" in str(e):
                    wait = 2 ** attempt
                    print(f"  Rate limited, waiting {wait}s...")
                    time.sleep(wait)
                else:
                    raise
        raw = resp.text.strip().lower()
        match = next((c for c in CATEGORIES if c.lower() == raw), raw.title())
        preds.append(match)
        tick = "✓" if match == t["ground_truth"] else "✗"
        print(f"  #{t['ticket_id']} GT={t['ground_truth']:15s} Pred={match:20s} {tick}")
        time.sleep(0.5)
    return preds

all_preds = {}
for name, tpl in [("Zero-shot", zero_shot), ("Few-shot", few_shot), ("Role-based", role_base)]:
    print(f"\n--- {name} ---")
    all_preds[name] = classify(name, tpl)

# Accuracy summary
acc = {}
for name in ["Zero-shot", "Few-shot", "Role-based"]:
    correct = sum(p == t["ground_truth"] for p, t in zip(all_preds[name], tickets))
    acc[name] = correct / len(tickets) * 100
    print(f"  >>> {name}: {correct}/{len(tickets)} = {acc[name]:.1f}%")

with open(DIR / "accuracy_summary.txt", "w") as f:
    for name in ["Zero-shot", "Few-shot", "Role-based"]:
        f.write(f"{name}: {acc[name]:.1f}%\n")

# Per-ticket CSV
with open(DIR / "styles_eval.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["ticket_id", "ticket_text", "ground_truth",
                "zero_shot_pred", "few_shot_pred", "role_based_pred",
                "zero_correct", "few_correct", "role_correct"])
    for i, t in enumerate(tickets):
        w.writerow([
            t["ticket_id"], t["ticket_text"], t["ground_truth"],
            all_preds["Zero-shot"][i], all_preds["Few-shot"][i], all_preds["Role-based"][i],
            all_preds["Zero-shot"][i] == t["ground_truth"],
            all_preds["Few-shot"][i] == t["ground_truth"],
            all_preds["Role-based"][i] == t["ground_truth"],
        ])
