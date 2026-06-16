import os
from typing import List, Optional, Literal
from pydantic import BaseModel
from google import genai
from google.genai import types
import json
import csv

# =========================
# VERTEX CLIENT
# =========================

client = genai.Client(
    vertexai=True,
    project="wohlig",
    location="global"
)

# =========================
# PYDANTIC SCHEMA (INSIDE MAIN FILE)
# =========================

class Address(BaseModel):
    street: str
    city: str
    state: str
    pincode: str

class LineItem(BaseModel):
    item_name: str
    quantity: int
    unit_price: float
    total_price: float

class InvoiceSchema(BaseModel):
    invoice_id: str
    vendor_name: str
    customer_name: str

    billing_address: Address
    shipping_address: Address

    items: List[LineItem]

    total_amount: float

    status: Literal["PAID", "UNPAID", "PENDING"]

    notes: Optional[str] = None


# =========================
# PROMPT (INLINE HERE)
# =========================

PROMPT = """
Extract structured invoice data from the document.

Rules:
- Follow schema strictly
- Do not hallucinate missing values
- Use null for missing optional fields
"""

# =========================
# LOAD FILE
# =========================

def load_file(file_path):
    with open(file_path, "rb") as f:
        return f.read()

# =========================
# EXTRACTION FUNCTION
# =========================

def extract_invoice(file_path):
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    prompt = """
    Extract structured invoice data from this document.

    Rules:
    - Follow schema strictly
    - Do not hallucinate missing values
    - Use null for missing optional fields
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            prompt,
            types.Part.from_bytes(
                data=file_bytes,
                mime_type="application/pdf"
            )
        ],
        config={
            "response_mime_type": "application/json",
            "response_schema": InvoiceSchema
        }
    )

    return response.text

def load_ground_truth():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, "ground_truth.jsonl")

    gt = {}

    with open(path, "r") as f:
        for line in f:
            obj = json.loads(line)

            key = obj.get("sample_id")
            gt[key] = obj

    return gt

def flatten(invoice):
    return {
        "invoice_id": invoice.get("invoice_id"),
        "vendor_name": invoice.get("vendor_name"),
        "customer_name": invoice.get("customer_name"),
        "total_amount": invoice.get("total_amount"),
        "status": invoice.get("status")
    }

# =========================
# RUN PIPELINE
# =========================

def run():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    folder = os.path.join(base_dir, "samples")

    ground_truth = load_ground_truth()

    csv_file = open("field_accuracy.csv", "w", newline="")
    writer = csv.writer(csv_file)

    writer.writerow([
        "file",
        "field",
        "extracted",
        "ground_truth",
        "match"
    ])

    for file in os.listdir(folder):
        path = os.path.join(folder, file)

        print(f"Processing: {file}")

        extracted_raw = extract_invoice(path)
        extracted = json.loads(extracted_raw)

        gt = ground_truth.get(file, {})

        extracted_flat = flatten(extracted)

        for field in extracted_flat:
            writer.writerow([
                file,
                field,
                extracted_flat[field],
                gt.get(field),
                extracted_flat[field] == gt.get(field)
            ])

    csv_file.close()
    print("Evaluation complete → field_accuracy.csv generated")

# =========================
# ENTRY POINT
# =========================

if __name__ == "__main__":
    run()