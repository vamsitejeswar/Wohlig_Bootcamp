import json

# STUBBED — prints to console instead of calling the real Slack API

def send_slack_message(channel: str, message: str) -> str:
    """Send a message to a Slack channel. (Stubbed — prints to console only.)"""
    if not channel or not message:
        return json.dumps({"error": True, "code": "INVALID_INPUT", "message": "channel and message are required."})

    print(f"[SLACK] #{channel}: {message}")
    return json.dumps({"error": False, "channel": channel, "message": message, "status": "sent (stubbed)"})
