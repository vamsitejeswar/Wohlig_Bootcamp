import csv
import json
import time
from pathlib import Path
from collections import Counter

import google.genai as genai

BASE_DIR = Path(__file__).parent

client = genai.Client(
    vertexai=True,
    project="wohlig",
    location="us-central1"
)

MODEL = "gemini-2.5-flash"

# Approximate Gemini Flash pricing
INPUT_COST_PER_M = 0.30
OUTPUT_COST_PER_M = 2.50

PROMPTS_DIR = BASE_DIR / "prompts"

direct_prompt = (PROMPTS_DIR / "direct.txt").read_text()
cot_prompt = (PROMPTS_DIR / "cot.txt").read_text()
sc_prompt = (PROMPTS_DIR / "sc.txt").read_text()

scenarios = []

with open(BASE_DIR / "scenarios.jsonl") as f:
    for line in f:

        line = line.strip()

        if not line:
            continue

        scenarios.append(json.loads(line))


def estimate_cost(prompt, output):

    input_tokens = len(prompt.split()) * 1.3
    output_tokens = len(output.split()) * 1.3

    cost = (
        input_tokens / 1_000_000 * INPUT_COST_PER_M
        +
        output_tokens / 1_000_000 * OUTPUT_COST_PER_M
    )

    return round(cost, 8)


def ask(prompt, temperature=0):

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    return response.text.strip()


def normalize(text):

    text = text.lower()

    if "yes" in text:
        return "Yes"

    return "No"


def run_direct(scenario):

    prompt = direct_prompt.replace(
        "{scenario}",
        scenario
    )

    answer = normalize(
        ask(prompt)
    )

    cost = estimate_cost(
        prompt,
        answer
    )

    return answer, cost


def run_cot(scenario):

    prompt = cot_prompt.replace(
        "{scenario}",
        scenario
    )

    answer = normalize(
        ask(prompt)
    )

    cost = estimate_cost(
        prompt,
        answer
    )

    return answer, cost


def run_self_consistency(scenario):

    prompt = sc_prompt.replace(
        "{scenario}",
        scenario
    )

    answers = []

    total_cost = 0

    for _ in range(5):

        ans = normalize(
            ask(prompt)
        )

        answers.append(ans)

        total_cost += estimate_cost(
            prompt,
            ans
        )

    majority = Counter(
        answers
    ).most_common(1)[0][0]

    return majority, round(total_cost, 8)


rows = []

for item in scenarios:

    scenario_id = item["scenario_id"]

    scenario = item["scenario"]

    gt = item["ground_truth"]

    print(f"Scenario {scenario_id}")

    direct_ans, direct_cost = run_direct(
        scenario
    )

    cot_ans, cot_cost = run_cot(
        scenario
    )

    sc_ans, sc_cost = run_self_consistency(
        scenario
    )

    rows.append([
        scenario_id,

        direct_ans,
        direct_ans == gt,

        cot_ans,
        cot_ans == gt,

        sc_ans,
        sc_ans == gt,

        direct_cost,
        cot_cost,
        sc_cost
    ])

    time.sleep(1)


with open(BASE_DIR / "results.csv", "w", newline="") as f:

    writer = csv.writer(f)

    writer.writerow([
        "scenario_id",

        "direct_answer",
        "direct_correct",

        "cot_answer",
        "cot_correct",

        "sc_answer",
        "sc_correct",

        "direct_cost_usd",
        "cot_cost_usd",
        "sc_cost_usd"
    ])

    writer.writerows(rows)

print("results.csv generated")


# Accuracy

total = len(rows)

direct_correct = sum(r[2] for r in rows)
cot_correct = sum(r[4] for r in rows)
sc_correct = sum(r[6] for r in rows)

direct_acc = direct_correct / total * 100
cot_acc = cot_correct / total * 100
sc_acc = sc_correct / total * 100

direct_total_cost = sum(r[7] for r in rows)
cot_total_cost = sum(r[8] for r in rows)
sc_total_cost = sum(r[9] for r in rows)

print("\nAccuracy")

print(f"Direct: {direct_acc:.1f}%")
print(f"CoT: {cot_acc:.1f}%")
print(f"Self Consistency: {sc_acc:.1f}%")

print("\nCost per Correct")

print(
    "Direct:",
    direct_total_cost / direct_correct
)

print(
    "CoT:",
    cot_total_cost / cot_correct
)

print(
    "SC:",
    sc_total_cost / sc_correct
)