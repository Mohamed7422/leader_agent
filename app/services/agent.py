import anthropic
from app.config import ANTHROPIC_API_KEY
from app.services.clickup import get_tasks, format_tasks

client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

def build_system_prompt(tasks: list) -> str:
    task_lines = []

    for t in tasks:
        assignees = ", ".join(t["assignees"]) if t["assignees"] else "NO ASSIGNEE"
        stale_note = f"STALE {t['days_stale']} days" if t["days_stale"] >= 2 else f"updated {t['days_stale']}d ago"
        due = f"due: {t['due_date']}" if t["due_date"] else "no due date"
        task_lines.append(
            f"[{t['id']}] {t['name']} | status: {t['status']} | "
            f"assignee: {assignees} | {stale_note} | {due} | "
            f"list: {t['list_name']} | url: {t['url']}"
        )

    tasks_block = "\n".join(task_lines)

    return f"""You are a Leader Agent — an autonomous project management AI.
You monitor tasks, identify blockers, and help leaders follow up with their teams.

Here are all current open tasks from the team's ClickUp space:

{tasks_block}

Rules:
- Always reference task IDs when discussing specific tasks
- Flag any task with NO ASSIGNEE as urgent — it needs to be assigned or announced
- Flag any task stale 2+ days as needing a follow-up
- When asked to draft a Slack message, write the actual message text ready to send
- Be direct and specific — you are a leader's assistant, not a narrator
- If asked about overall health, summarize risks clearly and concisely
"""


async def chat(messages: list) -> str:
    """
    messages: list of {"role": "user"/"assistant", "content": "..."}
    Returns the agent's reply as a string.
    """
    # Always load fresh task data on each chat call
    raw = await get_tasks()
    tasks = format_tasks(raw)

    system_prompt = build_system_prompt(tasks)

    response = await client.messages.create(
        model="claude-opus-4-7",
        max_tokens=1000,
        system=system_prompt,
        messages=messages
    )

    return response.content[0].text