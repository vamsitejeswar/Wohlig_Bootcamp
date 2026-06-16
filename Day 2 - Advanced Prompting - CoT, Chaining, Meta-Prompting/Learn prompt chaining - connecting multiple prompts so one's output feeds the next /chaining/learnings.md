# Learnings from Prompt Chaining

## 1. Key Observation

Breaking a complex task into 3 steps significantly improves reliability compared to a single large prompt.

---

## 2. What worked well

- Step 1 (Extraction) produced structured output most of the time
- Step 2 (Generation) worked well when Step 1 output was clean JSON
- Step 3 (Selection) was effective in enforcing brand rules

---

## 3. What broke

When Step 1 returned:
- missing keys
- invalid JSON
- extra text

Step 2 often failed or produced low-quality ads because it depended heavily on structured input.

---

## 4. Key Insight

Prompt chaining introduces dependency risk:

> If Step 1 is wrong → all downstream steps degrade.

---

## 5. Fixes applied

- Added strict JSON output requirement in Step 1
- Added fallback logic (manual retry in debugging)
- Reduced ambiguity in prompts

---

## 6. Final Conclusion

Prompt chaining improves quality and modularity, but requires strong validation between steps to prevent error propagation.