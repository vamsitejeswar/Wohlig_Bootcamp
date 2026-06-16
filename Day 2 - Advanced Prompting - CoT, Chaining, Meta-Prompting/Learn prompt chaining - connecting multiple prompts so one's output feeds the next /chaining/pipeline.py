import os
import json
from google import genai

# =========================
# VERTEX CLIENT
# =========================

client = genai.Client(
    vertexai=True,
    project="wohlig",
    location="global"
)

# =========================
# LOAD PROMPTS
# =========================

import os

def load_prompt(path):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_dir, path)

    with open(full_path, "r") as f:
        return f.read()

# =========================
# CALL MODEL
# =========================

def call_model(prompt):
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text

# =========================
# STEP 1 - EXTRACT
# =========================

def step1_extract(brief):
    prompt = load_prompt("prompts/extract.txt").replace("{{input}}", brief)
    return call_model(prompt)

# =========================
# STEP 2 - GENERATE
# =========================

def step2_generate(attributes_json):
    prompt = load_prompt("prompts/generate.txt").replace("{{input}}", attributes_json)
    return call_model(prompt)

# =========================
# STEP 3 - SELECT
# =========================

def step3_select(variants_json):
    prompt = load_prompt("prompts/select.txt").replace("{{input}}", variants_json)
    return call_model(prompt)

# =========================
# SAVE RUN
# =========================

def save_run(run_id, brief, step1, step2, step3):
    run_path = f"runs/run_{run_id}"
    os.makedirs(run_path, exist_ok=True)

    with open(f"{run_path}/input_brief.txt", "w") as f:
        f.write(brief)

    with open(f"{run_path}/step1_attributes.json", "w") as f:
        f.write(step1)

    with open(f"{run_path}/step2_variants.json", "w") as f:
        f.write(step2)

    with open(f"{run_path}/step3_winner.json", "w") as f:
        f.write(step3)

# =========================
# PIPELINE RUNNER
# =========================

def run_pipeline():
    briefs = [
        "Smartwatch by ZenithTech that tracks health, sleep, and fitness for young professionals.",
        "EcoClean detergent that is plant-based and safe for baby clothes.",
        "AquaPure water purifier designed for Indian households with low maintenance.",
        "FitFuel protein shake for gym beginners who want affordable nutrition.",
        "TravelLite backpack designed for students and digital nomads."
    ]

    for i, brief in enumerate(briefs, start=1):

        print(f"\nRunning pipeline for brief {i}")

        # Step 1
        step1 = step1_extract(brief)

        # Step 2
        step2 = step2_generate(step1)

        # Step 3
        step3 = step3_select(step2)

        # Save everything
        save_run(i, brief, step1, step2, step3)

        print(f"Completed run {i}")

# =========================
# ENTRY
# =========================

if __name__ == "__main__":
    run_pipeline()