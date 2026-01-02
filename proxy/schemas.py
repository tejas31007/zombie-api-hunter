# proxy/schemas.py
from pydantic import BaseModel

class FeedbackRequest(BaseModel):
    request_id: str
    actual_label: str  # e.g., "safe", "malicious"
    comments: str = ""