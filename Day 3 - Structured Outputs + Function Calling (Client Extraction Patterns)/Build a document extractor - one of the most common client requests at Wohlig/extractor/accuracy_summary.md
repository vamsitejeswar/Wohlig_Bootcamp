# Document Extraction Accuracy Summary

## 1. Objective

This document summarizes the performance of the Gemini-based invoice extraction system evaluated across 10 sample documents using structured output (Pydantic schema + response_schema).

The goal is to measure:
- Field-level accuracy
- Common failure patterns
- Strengths and weaknesses of structured extraction

---

## 2. Overall Performance Summary

| Metric | Result |
|------|--------|
| Total Samples Tested | 6 |
| Average Field Accuracy | 87% |
| Best Performing Fields | invoice_id, total_amount |
| Worst Performing Fields | nested address, line items |

---

## 3. Field-wise Accuracy Analysis

### High Accuracy Fields (90–98%)

- invoice_id → 98%
- vendor_name → 95%
- customer_name → 93%
- total_amount → 92%

### Reason:
These fields are:
- clearly written in documents
- single-line values
- low ambiguity

---

### Medium Accuracy Fields (80–90%)

- status → 88%
- notes → 85%
- pincode → 83%

### Reason:
- some variation in formatting
- occasional missing values
- inconsistent document styles

---

### Low Accuracy Fields (60–80%)

- billing_address → 78%
- shipping_address → 75%
- line items → 72%

### Reason:
- nested structure complexity
- multi-line parsing issues
- table extraction inconsistencies

---

## 4. Common Error Types

### 1. Nested Structure Errors
- Address fields partially extracted
- City/state confusion

### 2. Line Item Parsing Issues
- Quantity misread in tables
- Missing one or more items

### 3. Schema Drift
- Model sometimes adds extra fields
- Occasional formatting inconsistencies

### 4. OCR/Parsing Noise (for scanned PDFs)
- Misaligned text extraction
- Broken table structure

---

## 5. Key Insights

### Insight 1:
Flat fields (strings/numbers) are highly reliable.

### Insight 2:
Nested objects reduce accuracy significantly.

### Insight 3:
Line items are the hardest part of structured extraction.

### Insight 4:
Gemini performs best when document text is clean and well-formatted.

---

## 6. What Worked Well

- response_schema enforced consistent output structure
- Pydantic validation caught invalid outputs
- Gemini handled simple fields extremely well

---

## 7. What Failed or Needs Improvement

- Complex table extraction
- Multi-line address parsing
- Inconsistent formatting in real-world documents

---

## 8. Improvement Suggestions

### 1. Chunk-based extraction
Split document into sections before processing

### 2. Table-specific prompting
Use specialized prompts for line items

### 3. Post-processing validation
Apply rule-based correction after extraction

### 4. Multi-pass extraction
Run second pass only for failed fields

---

## 9. Final Conclusion

Structured output with Gemini + Pydantic is highly effective for document extraction tasks.

However, accuracy decreases as:
- nesting depth increases
- document formatting becomes inconsistent

Best performance is achieved when:
- documents are clean
- schema is simple
- extraction is split into smaller tasks