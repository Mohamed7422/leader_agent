import httpx
from app.config import CLICKUP_API_TOKEN, CLICKUP_SPACE_ID

BASE_URL = "https://api.clickup.com/api/v2"
HEADERS = {
    "Authorization": CLICKUP_API_TOKEN,
    "Content-Type": "application/json"
}


async def get_lists() -> list:

    """Get all lists (folders + folderless) inside the space."""
    lists = []

    async with httpx.AsyncClient() as client:
        # 1. Lists inside folders
        folders_res = await client.get(
            f"{BASE_URL}/space/{CLICKUP_SPACE_ID}/folder",
            headers=HEADERS
        )
        folders = folders_res.json().get("folders", [])

        for folder in folders:
            folder_lists_res = await client.get(
                f"{BASE_URL}/folder/{folder['id']}/list",
                headers=HEADERS
            )
            lists += folder_lists_res.json().get("lists", [])

        # 2. Folderless lists directly in space
        folderless_res = await client.get(
            f"{BASE_URL}/space/{CLICKUP_SPACE_ID}/list",
            headers=HEADERS
        )
        lists += folderless_res.json().get("lists", [])

    return lists


async def get_tasks() -> list:
    """Get all open tasks across all lists in the space."""
    lists = await get_lists()
    all_tasks = []

    async with httpx.AsyncClient() as client:
        for lst in lists:
            res = await client.get(
                f"{BASE_URL}/list/{lst['id']}/task",
                headers=HEADERS,
                params={"include_closed": "false", "subtasks": "true"}
            )
            tasks = res.json().get("tasks", [])
            all_tasks += tasks

    return all_tasks

def format_tasks(raw_tasks: list) -> list:
    """Simplify raw ClickUp response into clean dicts the agent can use."""
    formatted = []

    for t in raw_tasks:
        assignees = t.get("assignees", [])
        assignee_names = [a.get("username") or a.get("email", "unknown") for a in assignees]

        # Calculate days since last update
        import time
        last_updated_ms = int(t.get("date_updated", 0))
        now_ms = int(time.time() * 1000)
        days_stale = round((now_ms - last_updated_ms) / (1000 * 60 * 60 * 24), 1)

        due_date = t.get("due_date")

        formatted.append({
            "id": t.get("id"),
            "name": t.get("name"),
            "status": t.get("status", {}).get("status", "unknown"),
            "assignees": assignee_names,
            "has_assignee": len(assignee_names) > 0,
            "days_stale": days_stale,
            "due_date": due_date,
            "url": t.get("url"),
            "list_name": t.get("list", {}).get("name", ""),
            "description": t.get("description", "")[:300] if t.get("description") else ""
        })

    return formatted