# PAN Extraction Quality Report

## Dataset

10 synthetic PAN card images

| Type | Count |
|--------|--------|
| Clean | 1 |
| Rotated | 1 |
| Dark | 1 |
| Blurry | 1 |

---

## Accuracy Summary

| Quality Bucket | Accuracy |
|----------------|----------|
| Clean | 75 |
| Rotated | 75 |
| Dark | 50 |
| Blurry | 100 |

---

## Observations

### Clean
Highest extraction accuracy.

### Rotated
Auto-rotation improved performance.

### Dark
Brightness correction improved readability.

### Blurry
Lowest confidence scores and most extraction failures.

---

## Most Effective Preprocessing

1. Auto rotation
2. Histogram equalization

---

## Failure Modes

- Severe blur
- Heavy cropping
- Shadow-covered PAN number
- Partially visible cards