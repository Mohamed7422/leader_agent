from fastapi import APIRouter   
from pydantic import BaseModel
from app.services.agent import chat

router = APIRouter()

class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    messages: list[Message]

@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    messages = [m.model_dump() for m in request.messages]
    reply = await chat(messages)
    return {"reply": reply}