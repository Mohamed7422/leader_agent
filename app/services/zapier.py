import logging

import httpx

from app.config import ZAPIER_DM_WEBHOOK

logger = logging.getLogger(__name__)


async def send_dm(assignee_name: str, assignee_email: str, message: str, task_url: str):
    """Send a DM via Zapier webhook.

    Zapier field mapping (in the "Send Direct Message" step):
      "To Usernames"  → use `assignee_name`  (must match the Slack username)
      "Message Text"  → use `message`

    IMPORTANT: In the "Catch Hook" step → Configure tab,
    leave "Pick off a Child Key" BLANK. If filled, Zapier
    will silently drop every payload (`_zap_data_was_skipped: true`).
    """
    payload = {
        "assignee_name":  assignee_name,
        "assignee_email": assignee_email,
        "message":        message,
        "task_url":       task_url,
    }

    logger.info("Zapier → POST %s payload=%s", ZAPIER_DM_WEBHOOK, payload)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(ZAPIER_DM_WEBHOOK, json=payload)
        logger.info("Zapier ← %d %s", res.status_code, res.text[:200])
        return res.status_code == 200
    except Exception as e:
        logger.exception("Zapier webhook call failed: %s", e)
        return False
