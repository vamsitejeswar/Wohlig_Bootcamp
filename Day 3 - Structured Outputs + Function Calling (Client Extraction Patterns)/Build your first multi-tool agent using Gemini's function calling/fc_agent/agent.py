from google.adk.agents import Agent
from dotenv import load_dotenv
import os

from .tools import (
    get_order,
    get_shipping,
    check_refund_policy,
    escalate_to_human
)
load_dotenv()

MODEL_NAME = os.getenv(
    "MODEL_NAME",
    "gemini-2.5-flash"
)

SYSTEM_PROMPT = """
You are a customer support AI agent.

Responsibilities:
- Order lookup
- Shipping tracking
- Refund questions
- Escalation handling

Rules:
1. Use tools whenever information is needed.
2. Never make up order details.
3. Escalate when:
   - User is angry
   - User threatens legal action
   - Refund dispute is unresolved
   - User asks for a manager
4. Be professional and concise.
"""

root_agent = Agent(
    name="customer_support_agent",
    model=MODEL_NAME,
    description="Customer support AI agent",
    instruction=SYSTEM_PROMPT,
    tools=[
        get_order,
        get_shipping,
        check_refund_policy,
        escalate_to_human
    ]
)

agent = root_agent