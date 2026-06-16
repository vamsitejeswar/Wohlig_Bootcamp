import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ORDERS_FILE = BASE_DIR / "fake_orders.json"

with open(ORDERS_FILE, "r") as f:
    ORDERS = json.load(f)


def get_order(order_id: str) -> dict:
    """
    Get complete order details.
    """
    for order in ORDERS:
        if order["order_id"] == order_id:
            return order

    return {"error": f"Order {order_id} not found"}


def get_shipping(order_id: str) -> dict:
    """
    Get shipping details.
    """
    for order in ORDERS:
        if order["order_id"] == order_id:
            return {
                "order_id": order_id,
                "shipping_status": order["shipping_status"]
            }

    return {"error": f"Shipping details not found for {order_id}"}


def check_refund_policy(category: str) -> dict:
    """
    Check refund policy by category.
    """

    policies = {
        "electronics": "7-day refund allowed for undamaged products.",
        "fashion": "10-day return window.",
        "furniture": "Replacement only for damaged products.",
        "home-appliances": "5-day replacement policy.",
        "fitness": "7-day return policy.",
        "home-decor": "3-day return policy."
    }

    return {
        "category": category,
        "policy": policies.get(
            category,
            "Standard refund policy applies."
        )
    }


def escalate_to_human(reason: str) -> dict:
    """
    Escalate issue to human support.
    """

    return {
        "status": "ESCALATED",
        "message": "Human support agent will contact customer shortly.",
        "reason": reason
    }