"""
Run all 3 prompting styles against 30 tickets using Gemini Flash.
Compares predictions to ground truth and outputs accuracy.
"""

import csv
import os
import time
import google.genai as genai
from google.genai import types

# Read tickets
tickets = []
with open("prompting/tickets.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        tickets.append(row)

SAFETY_SETTINGS = [
    types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
    types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
    types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
    types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
]

VALID_CATEGORIES = ["Refund", "Shipping", "Login", "Payment", "Account", "Product Quality", "Order Change", "Other"]

def load_prompt(path, ticket_text):
    with open(path) as f:
        template = f.read()
    return template.replace("{ticket_text}", ticket_text)

zero_shot_tpl = open("prompting/prompts/zero_shot.txt").read()
few_shot_tpl = open("prompting/prompts/few_shot.txt").read()
role_based_tpl = open("prompting/prompts/role_based.txt").read()

client = genai.Client(vertexai=True, project="wohlig", location="us-central1")
MODEL = "gemini-2.5-flash"

def match_category(raw):
    raw = raw.strip().lower().replace("-", " ")
    # Exact match first
    for cat in VALID_CATEGORIES:
        if raw == cat.lower():
            return cat
    # Partial match: check if raw contains a category or vice versa
    for cat in VALID_CATEGORIES:
        cat_lower = cat.lower()
        if cat_lower in raw or raw in cat_lower:
            return cat
    # Token-based match
    words = set(raw.split())
    best_cat = None
    best_overlap = 0
    for cat in VALID_CATEGORIES:
        cat_words = set(cat.lower().split())
        overlap = len(words & cat_words)
        if overlap > best_overlap:
            best_overlap = overlap
            best_cat = cat
    if best_overlap > 0:
        return best_cat
    return raw

def classify(prompt_text, retries=2):
    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt_text,
                config={
                    "temperature": 0.0,
                    "max_output_tokens": 200,
                    "safety_settings": SAFETY_SETTINGS,
                }
            )
            if response.text is None:
                # Check if blocked
                if response.candidates and response.candidates[0].finish_reason:
                    reason = response.candidates[0].finish_reason
                    return f"BLOCKED:{reason}"
                return "NO_RESPONSE"
            raw = response.text.strip()
            return match_category(raw)
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)
            else:
                return f"ERROR:{e}"

def run_style(name, template):
    results = []
    print(f"\n--- Running {name} ---")
    for i, t in enumerate(tickets):
        prompt_text = template.replace("{ticket_text}", t["ticket_text"])
        pred = classify(prompt_text)
        correct = pred == t["ground_truth"]
        results.append({"ticket_id": t["ticket_id"], "pred": pred, "correct": correct})
        check = "✓" if correct else "✗"
        print(f"  #{t['ticket_id']} GT={t['ground_truth']:15s} Pred={pred:20s} {check}")
        if (i + 1) % 5 == 0:
            print()
    return results

results_zs = run_style("Zero-shot", zero_shot_tpl)
results_fs = run_style("Few-shot", few_shot_tpl)
results_rb = run_style("Role-based", role_based_tpl)

# Write combined CSV
os.makedirs("prompting", exist_ok=True)
with open("prompting/styles_eval.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "ticket_id", "ticket_text", "ground_truth",
        "zero_shot_pred", "few_shot_pred", "role_based_pred",
        "zero_correct", "few_correct", "role_correct"
    ])
    for i, t in enumerate(tickets):
        writer.writerow([
            t["ticket_id"], t["ticket_text"], t["ground_truth"],
            results_zs[i]["pred"], results_fs[i]["pred"], results_rb[i]["pred"],
            results_zs[i]["correct"], results_fs[i]["correct"], results_rb[i]["correct"],
        ])

# Calculate accuracy
acc_zs = sum(r["correct"] for r in results_zs) / len(results_zs) * 100
acc_fs = sum(r["correct"] for r in results_fs) / len(results_fs) * 100
acc_rb = sum(r["correct"] for r in results_rb) / len(results_rb) * 100

print(f"\n{'='*50}")
print(f"ACCURACY RESULTS")
print(f"{'='*50}")
print(f"  Zero-shot:  {acc_zs:.1f}%")
print(f"  Few-shot:   {acc_fs:.1f}%")
print(f"  Role-based: {acc_rb:.1f}%")
print(f"{'='*50}")

with open("prompting/accuracy_summary.txt", "w") as f:
    f.write(f"Zero-shot: {acc_zs:.1f}%\n")
    f.write(f"Few-shot: {acc_fs:.1f}%\n")
    f.write(f"Role-based: {acc_rb:.1f}%\n")
