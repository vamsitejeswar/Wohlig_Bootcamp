import os
import csv
import time

from google import genai
from pydantic import ValidationError

from schema import ContactCard


# -----------------------------
# GEMINI CLIENT
# -----------------------------
client = genai.Client(
    vertexai=True,
    project="wohlig",
    location="global"
)

MODEL = "gemini-2.5-flash"


# -----------------------------
# GEMINI CALL
# -----------------------------
def call_gemini(prompt: str) -> str:
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )
    return response.text


# -----------------------------
# PROMPT BUILD
# -----------------------------
def build_prompt(text: str) -> str:
    return f"""
Extract contact info from this messy text:

{text}

Return ONLY valid JSON matching this schema:
{ContactCard.model_json_schema()}
"""


# -----------------------------
# REPAIR PROMPT
# -----------------------------
def repair_prompt(original, bad_output, error):
    return f"""
Your previous JSON was INVALID.

INPUT:
{original}

OUTPUT:
{bad_output}

ERROR:
{error}

Fix it and return ONLY valid JSON:
{ContactCard.model_json_schema()}
"""


# -----------------------------
# SELF REPAIR LOOP
# -----------------------------
def run_repair_loop(text: str, max_retries: int = 3):
    prompt = build_prompt(text)

    first_try_valid = False
    errors = []
    total_cost = 0

    for attempt in range(max_retries):

        raw = call_gemini(prompt)

        # simple cost estimation
        total_cost += 0.00001 * (len(prompt) + len(raw))

        try:
            parsed = ContactCard.model_validate_json(raw)

            return {
                "first_try_valid": attempt == 0,
                "final_valid": True,
                "num_retries": attempt + 1,
                "errors_seen": "; ".join(errors),
                "total_cost": total_cost,
                "data": parsed.model_dump()
            }

        except ValidationError as e:
            errors.append(str(e))
            prompt = repair_prompt(text, raw, str(e))
            time.sleep(1)

    return {
        "first_try_valid": False,
        "final_valid": False,
        "num_retries": max_retries,
        "errors_seen": "; ".join(errors),
        "total_cost": total_cost,
        "data": None
    }


# -----------------------------
# LOAD INPUT FILES
# -----------------------------
def load_inputs(folder="inputs"):
    base_dir = os.path.dirname(__file__)
    input_path = os.path.join(base_dir, folder)

    inputs = []

    for file in sorted(os.listdir(input_path)):
        if file.endswith(".txt"):
            with open(os.path.join(input_path, file), "r") as f:
                inputs.append((file, f.read()))

    return inputs


# -----------------------------
# MAIN
# -----------------------------
def main():
    inputs = load_inputs()

    with open("results.csv", "w", newline="") as f:

        writer = csv.DictWriter(f, fieldnames=[
            "input_id",
            "first_try_valid",
            "final_valid",
            "num_retries",
            "errors_seen",
            "total_cost"
        ])

        writer.writeheader()

        for file, text in inputs:
            print(f"Processing {file}")

            result = run_repair_loop(text)

            writer.writerow({
                "input_id": file,
                "first_try_valid": result["first_try_valid"],
                "final_valid": result["final_valid"],
                "num_retries": result["num_retries"],
                "errors_seen": result["errors_seen"],
                "total_cost": round(result["total_cost"], 6)
            })

    print("\nDONE → results.csv generated")


if __name__ == "__main__":
    main()