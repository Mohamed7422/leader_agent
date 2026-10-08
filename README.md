Leader Agent

Leader Agent is a small FastAPI project designed to help a team lead stay on top of tasks, stale work, and follow-ups. It connects to ClickUp, reads open tasks, uses Anthropic to reason about team progress, and can send follow-up direct messages through Zapier.

What this project does

- Pulls tasks from a ClickUp space and normalizes the data for easier review
- Identifies stale tasks and highlights when a task has not been updated for a while
- Uses an AI assistant to talk about project health and task status
- Generates short follow-up messages for assignees
- Can send those messages through a Zapier webhook
- Exposes a simple API that a UI or front-end app can use

Main features

- Task overview from ClickUp
- AI chat endpoint for leadership questions about active work
- Follow-up sweep for stale tasks
- Daily scheduled follow-up runs
- Direct message delivery via Zapier

Project structure

- app/main.py: FastAPI app and API routes
- app/config.py: environment variables and configuration
- app/routers/chat.py: chat endpoint for sending messages to the assistant
- app/services/agent.py: Anthropic-based reasoning layer
- app/services/clickup.py: ClickUp API integration and formatting
- app/services/followup.py: stale task detection and message generation
- app/services/zapier.py: webhook for sending follow-up messages
- index.html: simple front-end interface for testing the app
- requirements.txt: project dependencies

Tech stack

- Python
- FastAPI
- Anthropic API
- ClickUp API
- Zapier webhook
- APScheduler

Setup

1. Create a virtual environment

   python -m venv venv
   venv\Scripts\activate

2. Install dependencies

   pip install -r requirements.txt

3. Create a .env file in the project root with your secret values

   CLICKUP_API_TOKEN=your_clickup_token
   CLICKUP_SPACE_ID=your_clickup_space_id
   ANTHROPIC_API_KEY=your_anthropic_key
   ZAPIER_DM_WEBHOOK=your_zapier_webhook_url
   FOLLOWUP_HOUR=8

4. Start the app

   uvicorn app.main:app --reload

5. Open the app in the browser

   http://localhost:8000

Available API routes

- GET /tasks
  Returns all current open tasks from ClickUp in a simplified format

- GET /followup/schedule
  Returns the configured daily follow-up hour

- POST /followup/run
  Runs a follow-up sweep and optionally sends messages

- POST /followup/send
  Sends a single prepared follow-up message through Zapier

- POST /chat
  Sends a conversation to the AI assistant and returns the response

Use cases

This project is useful for leaders who want an AI assistant to help with:

- spotting blocked work
- checking whether tasks are stale
- drafting short follow-up messages
- keeping team communication active without manual routine checking

Notes

- The .env file should stay local and should not be pushed to a public repository
- Keep your API secrets in environment variables only
- The app is designed for team operations and leadership workflow support

License

This project is for internal or personal use unless a different license is added later.
