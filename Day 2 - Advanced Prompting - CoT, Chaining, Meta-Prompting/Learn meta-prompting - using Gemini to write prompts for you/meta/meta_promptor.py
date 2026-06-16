import os
import csv
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
# LOAD META PROMPT
# =========================

def load_meta_prompt():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, "meta_prompt.txt")

    with open(path, "r") as f:
        return f.read()

# =========================
# CALL GEMINI
# =========================

def call_model(prompt):
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text

# =========================
# CHECK 6 SECTION VALIDATION
# =========================

def validate_sections(prompt):
    required = [
        "ROLE",
        "CONTEXT",
        "TASK",
        "CONSTRAINTS",
        "OUTPUT FORMAT",
        "EXAMPLES"
    ]

    return {k: (k in prompt) for k in required}

# =========================
# JUDGE QUALITY
# =========================

def judge_quality(prompt):
    judge_prompt = f"""
Rate this prompt from 1 to 5 based on clarity, structure, and usefulness.

Return ONLY a number.

Prompt:
{prompt}
"""

    res = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=judge_prompt
    )

    try:
        return int(res.text.strip()[0])
    except:
        return 3

# =========================
# GENERATE PROMPT
# =========================

def generate_prompt(meta_prompt, brief):
    final_prompt = meta_prompt.replace("{input}", brief)
    return call_model(final_prompt)

# =========================
# MAIN PIPELINE
# =========================

def run():
    briefs = [
        "extract data from PDFs",
        "classify support emails into categories",
        "write product descriptions for ecommerce",
        "summarize legal documents into simple language",
        "translate marketing copy into regional languages"
    ]

    meta_prompt = load_meta_prompt()

    os.makedirs("generated_prompts", exist_ok=True)

    with open("judge_scorecard.csv", "w", newline="") as f:
        writer = csv.writer(f)

        writer.writerow([
            "brief",
            "quality_score",
            "has_all_6_sections",
            "missing_sections"
        ])

        for i, brief in enumerate(briefs, start=1):

            generated = generate_prompt(meta_prompt, brief)

            sections = validate_sections(generated)

            missing = [k for k, v in sections.items() if not v]

            score = judge_quality(generated)

            # Save prompt
            with open(f"generated_prompts/brief_{i}.txt", "w") as f2:
                f2.write(generated)

            writer.writerow([
                brief,
                score,
                len(missing) == 0,
                ",".join(missing)
            ])

            print(f"Done → {brief}")

if __name__ == "__main__":
    run()