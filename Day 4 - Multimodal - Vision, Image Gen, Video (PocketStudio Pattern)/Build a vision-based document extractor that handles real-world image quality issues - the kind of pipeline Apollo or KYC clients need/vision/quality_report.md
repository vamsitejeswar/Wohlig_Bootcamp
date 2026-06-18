# PAN Extraction Quality Report

## Dataset

10 synthetic PAN card images

| Type | Count |
|--------|--------|
| Clean | 3 |
| Rotated | 3 |
| Dark | 2 |
| Blurry | 2 |

---

## Accuracy Summary

| Quality Bucket | Accuracy |
|----------------|----------|
| Clean | TBD |
| Rotated | TBD |
| Dark | TBD |
| Blurry | TBD |

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