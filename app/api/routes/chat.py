from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.ai_service import process_business_intelligence_chat

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    session_id: str = "session_default"

@router.post("/chat")
def handle_chat_endpoint(payload: ChatRequest):
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Pesan tidak boleh kosong")
        
    result = process_business_intelligence_chat(
        user_message=payload.message, 
        session_id=payload.session_id
    )
    return result