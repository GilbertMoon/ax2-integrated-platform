import os

import requests
from dotenv import load_dotenv

load_dotenv()


def send_slack_message(*, title, message="", link=""):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")

    if not webhook_url:
        return False

    text = f"*{title}*"

    if message:
        text += f"\n{message}"

    if link:
        text += f"\n<{link}|상세 보기>"

    try:
        response = requests.post(
            webhook_url,
            json={"text": text},
            timeout=5,
        )
        response.raise_for_status()
    except requests.RequestException:
        return False

    return True
