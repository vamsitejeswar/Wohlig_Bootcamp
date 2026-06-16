# Escalation Logic

## Purpose

The customer support agent should escalate conversations that cannot be safely or appropriately handled automatically.

---

## Escalation Triggers

### 1. Angry or Abusive Customer

Examples:

- "I am extremely angry."
- "Your service is terrible."
- "Nobody is helping me."

Action:

- Call escalate_to_human(reason)

Reason:

High customer dissatisfaction requires human intervention.

---

### 2. Legal Threats

Examples:

- "I will sue your company."
- "My lawyer will contact you."
- "I am filing a legal complaint."

Action:

- Call escalate_to_human(reason)

Reason:

Legal matters must be handled by trained support staff.

---

### 3. Refund Disputes

Examples:

- Customer disagrees with refund decision.
- Customer repeatedly requests exceptions.
- Refund policy does not resolve the issue.

Action:

- Call escalate_to_human(reason)

Reason:

Manual review may be required.

---

### 4. Explicit Human-Agent Request

Examples:

- "Connect me to a manager."
- "I want to talk to a person."
- "Transfer me to support."

Action:

- Call escalate_to_human(reason)

Reason:

Customer explicitly requested human assistance.

---

## Context Passed During Escalation

The following information should be included:

### Customer Message

Original customer request that triggered escalation.

Example:

"I want to sue your company because of order 1004."

---

### Order Information

Retrieved using:

- get_order(order_id)

Example:

- Order ID
- Product
- Status
- Refund Eligibility

---

### Shipping Information

Retrieved using:

- get_shipping(order_id)

Example:

- Current shipping status
- Delivery information

---

### Previous Tool Results

Any information already gathered before escalation.

Example:

- Order lookup results
- Refund policy lookup results
- Shipping status

---

### Escalation Reason

Examples:

- Angry customer
- Legal threat
- Refund dispute
- Human agent requested

---

## Escalation Tool

```python
escalate_to_human(reason: str)