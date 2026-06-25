# Routing Failures Log

Fill this in after running all 10 test queries.
For each case where the orchestrator picked the wrong agent, document it here
and record what prompt change fixed it.

---

## Template

```
## QXX — <short failure description>

**Query:** "<the question>"
**Expected agents:** <sql | rag | both>
**Agents actually called:** <what the trace showed>
**Root cause:** <why the orchestrator misrouted — which keyword was ambiguous?>

**Prompt fix applied (line added to orchestrator instruction):**
> "<exact sentence added>"

**After fix:** <both agents called ✓ | correct agent called ✓>  routing_correct: YES
```

---

<!-- Add entries below as you find failures -->

## Known failure patterns to watch for

### Pattern 1 — Ambiguous "average" question goes to structured when it should go to RAG
Some questions containing "average" or performance metrics are actually asking
about a documented standard, not a BigQuery calculation.

Fix trigger: "If the question asks what the standard or target IS (not what the
actual number was), route to unstructured_data_agent."

### Pattern 2 — "Both" question routes to only one agent
A question with "and" may be interpreted as needing only the first agent.

Fix trigger: "If the question contains 'and [policy/procedure/SLA/rule]' after
a data question, always call both agents."

### Pattern 3 — Vague "compare" goes only to structured
"Compare X against Y" may miss the Y being a documented guideline.

Fix trigger: "Comparison words (exceed, violate, comply, vs, against, below target,
meets the standard) always require BOTH agents."
