# Test Queries

## Single-Tool Queries

### Query 1
What is the status of order 1001?

Expected Tool:
- get_order

---

### Query 2
Show me the complete details of order 1002.

Expected Tool:
- get_order

---

### Query 3
What is the refund policy for electronics?

Expected Tool:
- check_refund_policy

---

## Multi-Tool Queries

### Query 4
Can I get a refund for order 1001?

Expected Tools:
- get_order
- check_refund_policy

---

### Query 5
Tell me about order 1004 and what options I have.

Expected Tools:
- get_order
- get_shipping
- check_refund_policy (if needed)

---

### Query 6
Check shipping and refund eligibility for order 1003.

Expected Tools:
- get_order
- get_shipping
- check_refund_policy

---

## Multi-Turn Conversations

### Query 7
I need help with order 1006.

Expected Tool:
- get_order

---

### Query 8
When will it arrive?

Expected Tool:
- get_shipping

Note:
This query depends on context from Query 7.

---

## Escalation Queries

### Query 9
I am extremely angry about order 1004 and nobody is helping me.

Expected Tool:
- escalate_to_human

---

### Query 10
I want to sue your company because of order 1004.

Expected Tool:
- escalate_to_human