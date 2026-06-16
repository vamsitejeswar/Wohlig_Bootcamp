# Chain of Thought Decision Rule

## Experiment Results

We tested 3 prompting strategies on insurance claim scenarios:

| Method              | Accuracy |
|--------------------|----------|
| Direct Prompting   | 46.7%    |
| Chain-of-Thought   | 60.0%    |
| Self-Consistency   | 73.3%    |

---

## Cost Analysis

| Method              | Cost per Correct Answer |
|--------------------|--------------------------|
| Direct Prompting   | $0.00005967 |
| Chain-of-Thought   | $0.00005681 |
| Self-Consistency   | $0.00020581 |

---

## Key Insights

### 1. Direct Prompting
- Cheapest per call
- Lowest accuracy
- Poor for multi-rule reasoning tasks

### 2. Chain-of-Thought (CoT)
- Improves reasoning quality
- Slightly better accuracy than direct prompting
- Best balance of cost vs performance

### 3. Self-Consistency
- Highest accuracy (73.3%)
- Most expensive (~3–4x cost)
- Works by running multiple reasoning paths and voting

---

## Final Recommendation

### Use Direct Prompting when:
- Task is simple classification
- Speed and cost are critical

### Use Chain-of-Thought when:
- Task involves multiple rules
- Business logic or reasoning is required
- Best cost-performance balance

### Use Self-Consistency when:
- High accuracy is critical (finance, compliance, insurance approvals)
- Cost is not a primary constraint
- Decision risk is high

---

## Conclusion

Chain-of-Thought improves reasoning quality without significant cost increase, while Self-Consistency provides the highest accuracy at the cost of increased computation.