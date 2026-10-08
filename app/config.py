from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env", override=True)

CLICKUP_API_TOKEN = os.getenv("CLICKUP_API_TOKEN")
CLICKUP_SPACE_ID = os.getenv("CLICKUP_SPACE_ID")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ZAPIER_DM_WEBHOOK = os.getenv("ZAPIER_DM_WEBHOOK")

# Hour (0-23, UTC) when the daily follow-up sweep runs automatically
FOLLOWUP_HOUR = int(os.getenv("FOLLOWUP_HOUR", "8"))