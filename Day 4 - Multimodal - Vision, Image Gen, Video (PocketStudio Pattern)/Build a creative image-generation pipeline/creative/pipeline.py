import os
import json
import csv
import uuid
import time
from pathlib import Path
from dotenv import load_dotenv

from google import genai
from google.genai import types


# =========================
# CONFIG
# =========================

load_dotenv()

client = genai.Client(
    vertexai=True,
    project=os.getenv("PROJECT_ID"),
    location=os.getenv("LOCATION", "us-central1")
)

BASE_DIR = Path(__file__).parent
PRODUCTS_DIR = BASE_DIR / "products"
RUNS_DIR = BASE_DIR / "runs"
RUNS_DIR.mkdir(exist_ok=True)

IMAGE_MODEL = "gemini-2.5-flash-image"
CHECK_MODEL = "gemini-2.5-flash"

STYLE_VARIANTS = [
    "luxury studio lighting",
]


# =========================
# LOAD DATA
# =========================

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)


def load_text(path):
    return open(path).read()


# =========================
# IMAGE GENERATION
# =========================

def generate_image(image_path, prompt, output_path):

    image_bytes = open(image_path, "rb").read()

    response = client.models.generate_content(
        model=IMAGE_MODEL,
        contents=[
            types.Part.from_text(text=prompt),
            types.Part.from_bytes(data=image_bytes, mime_type="image/png")
        ],
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"]
        )
    )

    for part in response.candidates[0].content.parts:
        if part.inline_data:
            open(output_path, "wb").write(part.inline_data.data)
            return


# =========================
# BRAND CHECK
# =========================

def brand_check(image_path, guidelines):

    image_bytes = open(image_path, "rb").read()

    prompt = f"""
            Check this image against brand rules:

            {guidelines}

            Return JSON:
            {{
            "status": "PASS or FAIL",
            "reason": ""
            }}
            """

    response = client.models.generate_content(
        model=CHECK_MODEL,
        contents=[
            types.Part.from_text(text=prompt),
            types.Part.from_bytes(data=image_bytes, mime_type="image/png")
        ]
    )

    return response.text


# =========================
# MAIN PIPELINE
# =========================

def run():

    guidelines = load_text(BASE_DIR / "brand_guidelines.md")

    for sku in PRODUCTS_DIR.iterdir():

        if not sku.is_dir():
            continue

        print("Processing:", sku.name)

        image_path = sku / "input.png"
        brief = load_json(sku / "brief.json")

        run_folder = RUNS_DIR / sku.name
        run_folder.mkdir(exist_ok=True)

        results = []
        run_id = str(uuid.uuid4())

        for i, style in enumerate(STYLE_VARIANTS, start=1):

            prompt = f"""
                        Product: {brief['product']}
                        Mood: {brief['desired_mood']}
                        Background: {brief['desired_background']}
                        Style: {style}
                    """

            out_path = run_folder / f"variant_{i}.png"

            generate_image(image_path, prompt, out_path)
            time.sleep(6)

            review = brand_check(out_path, guidelines)
            time.sleep(6)

            results.append({
                "variant": i,
                "review": review
            })

        # save results
        json.dump(results, open(run_folder / "brand_check.json", "w"), indent=2)

        # cost log (simple)
        with open(BASE_DIR / "cost_log.csv", "a") as f:
            writer = csv.writer(f)
            writer.writerow([run_id, 3, 0.12, 0.006, 0.126])

        print("Done:", sku.name)


if __name__ == "__main__":
    run()