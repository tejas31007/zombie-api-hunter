from pydantic import BaseModel
from typing import Optional

class FeedbackRequest(BaseModel):
    """
    Defines the expected data structure for feedback.
    If the dashboard sends anything else, the API will reject it automatically.
    """
    request_id: str
    actual_label: str  # e.g., "safe" or "malicious"
    comments: Optional[str] = None