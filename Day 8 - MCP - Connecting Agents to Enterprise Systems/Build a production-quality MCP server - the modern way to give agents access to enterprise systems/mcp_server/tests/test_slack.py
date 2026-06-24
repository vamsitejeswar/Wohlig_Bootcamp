import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
from tools.slack_tool import send_slack_message


def test_send_message_happy_path(capsys):
    result = json.loads(send_slack_message("general", "Hello team!"))
    assert result["error"] is False
    assert result["status"] == "sent (stubbed)"
    assert result["channel"] == "general"

    captured = capsys.readouterr()
    assert "#general" in captured.out
    assert "Hello team!" in captured.out


def test_send_message_empty_channel():
    result = json.loads(send_slack_message("", "Hello!"))
    assert result["error"] is True
    assert result["code"] == "INVALID_INPUT"


def test_send_message_empty_message():
    result = json.loads(send_slack_message("general", ""))
    assert result["error"] is True
    assert result["code"] == "INVALID_INPUT"
