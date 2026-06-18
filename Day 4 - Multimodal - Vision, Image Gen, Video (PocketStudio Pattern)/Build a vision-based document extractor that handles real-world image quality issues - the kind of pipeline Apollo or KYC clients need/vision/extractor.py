import os
import csv
import json
from pathlib import Path
import cv2
import numpy as np

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import Optional
from pathlib import Path

BASE_DIR = Path(__file__).parent


# ==========================================
# CONFIG
# ==========================================

load_dotenv()

client = genai.Client(
    vertexai=True,
    project=os.getenv("PROJECT_ID"),
    location=os.getenv("LOCATION", "us-central1")
)

MODEL = "gemini-2.5-flash"


# ==========================================
# SCHEMA
# ==========================================

class PANExtraction(BaseModel):

    pan_number: Optional[str] = None

    full_name: Optional[str] = None

    father_name: Optional[str] = None

    dob: Optional[str] = None

    confidence: float = 0.0


# ==========================================
# PREPROCESSING
# ==========================================

def auto_rotate(image):

    h, w = image.shape[:2]

    if h > w:
        image = cv2.rotate(
            image,
            cv2.ROTATE_90_CLOCKWISE
        )

    return image


def fix_brightness(image):

    hsv = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2HSV
    )

    h, s, v = cv2.split(hsv)

    if np.mean(v) < 80:
        v = cv2.equalizeHist(v)

    hsv = cv2.merge([h, s, v])

    return cv2.cvtColor(
        hsv,
        cv2.COLOR_HSV2BGR
    )


def preprocess(image_path):

    image = cv2.imread(str(image_path))

    image = auto_rotate(image)

    image = fix_brightness(image)

    processed_path = str(BASE_DIR / "processed_temp.jpg")

    cv2.imwrite(
        processed_path,
        image
    )

    return processed_path


# ==========================================
# GEMINI EXTRACTION
# ==========================================

PROMPT = """
You are a KYC extraction system.

Extract:

1. PAN Number
2. Full Name
3. Father Name
4. Date of Birth

Return JSON only.

If any field is unreadable return null.

Also provide confidence score
between 0 and 1.
"""


def extract_document(image_path):

    processed_image = preprocess(
        image_path
    )

    image_bytes = open(
        processed_image,
        "rb"
    ).read()

    response = client.models.generate_content(
        model=MODEL,
        contents=[
            types.Part.from_text(
                text=PROMPT
            ),
            types.Part.from_bytes(
                data=image_bytes,
                mime_type="image/jpeg"
            )
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=PANExtraction
        )
    )

    return response.parsed


# ==========================================
# EVALUATION
# ==========================================

def load_ground_truth():

    gt = {}

    with open(BASE_DIR / "ground_truth.jsonl", "r") as f:

        for line in f:

            row = json.loads(line)

            key = row["sample"].strip().lower()
            gt[key] = row

    return gt


def normalize(value):

    if value is None:
        return ""

    return str(value).strip().lower()


def compare(prediction, truth):

    fields = [
        "pan_number",
        "full_name",
        "father_name",
        "dob"
    ]

    correct = 0

    for field in fields:

        predicted_value = getattr(
            prediction,
            field
        )

        if normalize(
            predicted_value
        ) == normalize(
            truth[field]
        ):
            correct += 1

    return correct, len(fields)


def get_quality(sample_name):

    sample_name = sample_name.lower()

    if "clean" in sample_name:
        return "clean"

    if "rotated" in sample_name:
        return "rotated"

    if "dark" in sample_name:
        return "dark"

    if "blurry" in sample_name:
        return "blurry"

    return "unknown"


def evaluate():

    gt = load_ground_truth()

    results = []

    samples_dir = BASE_DIR / "samples"

    for image in samples_dir.rglob("*"):
        if image.suffix.lower() not in [".jpg", ".jpeg", ".png"]:
            continue

        sample_name = image.name.lower()

        if sample_name not in gt:
            print(f"Missing GT for: {sample_name}")
            continue

        print(f"Processing {sample_name}")

        prediction = extract_document( str(image))

        correct, total = compare( prediction, gt[sample_name])

        results.append([
            sample_name,
            get_quality(sample_name),
            total,
            correct,
            total - correct,
            prediction.confidence
        ])

    with open( BASE_DIR / "results.csv", "w", newline="" ) as f:

        writer = csv.writer(f)

        writer.writerow([
            "sample_id",
            "image_quality",
            "fields_extracted",
            "fields_correct",
            "fields_missed",
            "confidence"
        ])

        writer.writerows(results)

    print("results.csv generated")


# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":
    evaluate()

