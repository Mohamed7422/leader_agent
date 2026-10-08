import json
import logging

from app.services.clickup import get_tasks, format_tasks
from app.services.zapier import send_dm
from app.services.agent import client

logger = logging.getLogger(__name__)

STALE_THRESHOLD_DAYS = 2


async def generate_followup_messages(tasks: list[dict]) -> dict[str, str]:
    """Single Claude call for all tasks. Returns {task_id: message}."""
    task_lines = [
        f"- id={t['id']} assignee={t['assignees'][0]} "
        f"task=\"{t['name']}\" status={t['status']} "
        f"stale={t['days_stale']}d list={t['list_name']} url={t['url']}"
        for t in tasks
    ]

    prompt = f"""For each task below, write a short Slack DM to the assignee following up.

Tasks:
{chr(10).join(task_lines)}

Rules for each message:
- Direct and friendly, not robotic
- Reference the specific task name
- Ask one concrete question (what's blocking you? any update? do you need help?)
- Maximum 3 sentences
- No subject line — just the message body

Respond with a JSON object mapping each task id to its message, like:
{{"<task_id>": "<message>", ...}}

Return ONLY the JSON object, no explanation.
"""

    response = await client.messages.create(
        model="claude-opus-4-7",
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    return json.loads(raw)


async def run_followup_sweep(
    dry_run: bool = False,
    task_id: str | None = None,
    assignee: str | None = None,
) -> list:
    """
    Finds tasks, generates follow-up messages in one Claude call, optionally sends.

    Filters (mutually exclusive, task_id takes priority):
      task_id  → single specific task, staleness check skipped
      assignee → all stale tasks for that assignee (case-insensitive match)
      neither  → all stale tasks with any assignee
    """
    raw = await get_tasks()
    tasks = format_tasks(raw)

    if task_id:
        target = [t for t in tasks if t["id"] == task_id and t["has_assignee"]]
    elif assignee:
        name_lower = assignee.lower()
        target = [
            t for t in tasks
            if t["has_assignee"]
            and t["days_stale"] >= STALE_THRESHOLD_DAYS
            and any(name_lower in a.lower() for a in t["assignees"])
        ]
    else:
        target = [
            t for t in tasks
            if t["has_assignee"] and t["days_stale"] >= STALE_THRESHOLD_DAYS
        ]

    if not target:
        return []

    messages = await generate_followup_messages(target)

    log = []
    for task in target:
        assignee_name = task["assignees"][0]
        message = messages.get(task["id"], "")

        if not message:
            logger.warning("No message generated for task %s", task["id"])
            continue

        entry = {
            "task_id":   task["id"],
            "task_name": task["name"],
            "task_url":  task["url"],
            "assignee":  assignee_name,
            "days_stale": task["days_stale"],
            "message":   message,
            "sent":      False,
        }

        if not dry_run:
            success = await send_dm(
                assignee_name=assignee_name,
                assignee_email=assignee_name,
                message=message,
                task_url=task["url"],
            )
            entry["sent"] = success

        log.append(entry)

    return log
