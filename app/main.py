import logging
from contextlib import asynccontextmanager
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config import FOLLOWUP_HOUR
from app.services.clickup import get_tasks, format_tasks
from app.services.followup import run_followup_sweep
from app.services.zapier import send_dm
from app.routers import chat

logger = logging.getLogger(__name__)


async def _scheduled_followup():
    try:
        log = await run_followup_sweep(dry_run=False)
        logger.info("Scheduled follow-up sweep sent %d messages.", len(log))
    except Exception:
        logger.exception("Scheduled follow-up sweep failed.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        _scheduled_followup,
        trigger="cron",
        hour=FOLLOWUP_HOUR,
        minute=0,
        id="daily_followup",
    )
    scheduler.start()
    logger.info("Scheduler started — follow-up sweep runs daily at %02d:00 UTC.", FOLLOWUP_HOUR)
    yield
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(chat.router)


@app.get("/tasks")
async def tasks():
    raw = await get_tasks()
    return format_tasks(raw)


@app.get("/followup/schedule")
async def followup_schedule():
    """Return scheduler configuration so the UI can display it."""
    return {"hour": FOLLOWUP_HOUR, "label": f"daily at {FOLLOWUP_HOUR:02d}:00 UTC"}


@app.post("/followup/run")
async def trigger_followup(
    dry_run: bool = True,
    task_id: Optional[str] = None,
    assignee: Optional[str] = None,
):
    """
    Run a follow-up sweep.
      dry_run=true   → generate messages, do NOT send
      dry_run=false  → generate and send via Zapier
      task_id        → single task only (staleness check skipped)
      assignee       → all stale tasks for that person
    """
    log = await run_followup_sweep(dry_run=dry_run, task_id=task_id, assignee=assignee)
    return {"dry_run": dry_run, "tasks_found": len(log), "log": log}


class SendRequest(BaseModel):
    assignee: str
    task_url: str
    message: str


@app.post("/followup/send")
async def send_followup(body: SendRequest):
    """Send a single pre-generated follow-up message via Zapier."""
    success = await send_dm(
        assignee_name=body.assignee,
        assignee_email=body.assignee,
        message=body.message,
        task_url=body.task_url,
    )
    return {"sent": success}
