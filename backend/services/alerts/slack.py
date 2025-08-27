import os, requests

WEBHOOK = os.getenv("SLACK_WEBHOOK_URL")  # e.g. https://hooks.slack.com/services/...

def send_slack(text: str, blocks=None) -> bool:
    """Send a simple Slack message via incoming webhook."""
    if not WEBHOOK:
        return False
    payload = {"text": text}
    if blocks:
        payload["blocks"] = blocks
    r = requests.post(WEBHOOK, json=payload, timeout=10)
    r.raise_for_status()
    return True
