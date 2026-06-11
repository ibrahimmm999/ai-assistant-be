from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "session_default"

class ChatResponse(BaseModel):
    response: str
    intent: str
    generated_sql: Optional[str] = None