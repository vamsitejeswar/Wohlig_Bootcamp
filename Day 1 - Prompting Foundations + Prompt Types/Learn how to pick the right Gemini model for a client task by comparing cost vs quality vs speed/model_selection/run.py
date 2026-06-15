import json
import os
import csv
import time
from google import genai

# =========================
# VERTEX AI CLIENT
# =========================

client = genai.Client(
    vertexai=True,
    project="wohlig",
    location="global"
)

# =========================
# MODELS
# =========================

MODELS = [
    "gemini-3.1-pro-preview",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite"
]

# =========================
# PRICING (update if needed)
# =========================

PRICING = {
    "gemini-3.1-pro-preview": {"in": 0.00001, "out": 0.00003},
    "gemini-2.5-flash": {"in": 0.000005, "out": 0.000015},
    "gemini-2.5-flash-lite": {"in": 0.000002, "out": 0.000006}
}

# =========================
# LOAD INPUTS
# =========================

def load_inputs():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, "inputs", "data.json")

    with open(path, "r") as f:
        return json.load(f)

# =========================
# PROMPT
# =========================

def build_prompt(text):
    return f"""
Summarize into exactly 3 bullet points.

Rules:
- Only 3 bullets
- No extra text
- Be concise and factual

Text:
{text}
"""

# =========================
# CALL MODEL
# =========================

def call_model(model, prompt):
    start = time.time()

    response = client.models.generate_content(
        model=model,
        contents=prompt
    )

    latency_ms = (time.time() - start) * 1000
    usage = response.usage_metadata

    return {
        "text": response.text,
        "latency_ms": latency_ms,
        "input_tokens": usage.prompt_token_count,
        "output_tokens": usage.candidates_token_count
    }

# =========================
# COST CALCULATION
# =========================

def compute_cost(model, in_t, out_t):
    return (
        in_t * PRICING[model]["in"] +
        out_t * PRICING[model]["out"]
    )

# =========================
# JUDGE (LLM AS EVALUATOR)
# =========================

def judge_quality(text):
    judge_prompt = f"""
Rate this summary 1-5 based on accuracy, clarity, completeness.

Return ONLY number.

{text}
"""

    res = client.models.generate_content(
        model="gemini-3.1-pro-preview",
        contents=judge_prompt
    )

    try:
        return int(res.text.strip()[0])
    except:
        return 3

# =========================
# MAIN PIPELINE
# =========================

def run():
    inputs = load_inputs()

    with open("results.csv", "w", newline="") as f:
        writer = csv.writer(f)

        writer.writerow([
            "input_id",
            "model",
            "latency_ms",
            "input_tokens",
            "output_tokens",
            "cost_usd",
            "quality_score"
        ])

        for item in inputs:
            prompt = build_prompt(item["text"])

            for model in MODELS:

                result = call_model(model, prompt)

                cost = compute_cost(
                    model,
                    result["input_tokens"],
                    result["output_tokens"]
                )

                score = judge_quality(result["text"])

                writer.writerow([
                    item["id"],
                    model,
                    round(result["latency_ms"], 2),
                    result["input_tokens"],
                    result["output_tokens"],
                    round(cost, 8),
                    score
                ])

                print(f"Done → {model} | Input {item['id']}")

    print("\n✅ Benchmark complete → results.csv generated")


# =========================
# ENTRY
# =========================

if __name__ == "__main__":
    run()