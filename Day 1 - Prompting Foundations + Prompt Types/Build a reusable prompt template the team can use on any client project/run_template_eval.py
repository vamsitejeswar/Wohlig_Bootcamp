from pathlib import Path
import google.genai as genai

BASE_DIR = Path(__file__).parent

client = genai.Client(
    vertexai=True,
    project="wohlig",
    location="us-central1"
)

MODEL = "gemini-2.5-flash"


def run_usecase(usecase_name):
    usecase_dir = BASE_DIR / "applied" / usecase_name

    prompt = (usecase_dir / "prompt.txt").read_text()

    inputs_dir = usecase_dir / "inputs"
    outputs_dir = usecase_dir / "outputs"

    outputs_dir.mkdir(exist_ok=True)

    for input_file in sorted(inputs_dir.glob("*.txt")):

        input_text = input_file.read_text()

        final_prompt = f"""
{prompt}

Input:
{input_text}
"""

        response = client.models.generate_content(
            model=MODEL,
            contents=final_prompt
        )

        output_file = outputs_dir / (
            input_file.stem.replace("input", "output")
            + ".txt"
        )
        
        output_file.write_text(response.text)

        print(f"Saved: {output_file}")


run_usecase("claim_summary")
run_usecase("product_rewrite")
run_usecase("email_triage")