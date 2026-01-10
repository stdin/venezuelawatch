from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class ForecastPoint(BaseModel):
    ds: datetime
    yhat: float
    yhat_lower: float
    yhat_upper: float


class ForecastResponse(BaseModel):
    status: str  # "ready", "generating", "insufficient_data"
    forecast: Optional[List[ForecastPoint]] = None
    generated_at: Optional[datetime] = None
    horizon_days: int
    message: Optional[str] = None  # For "insufficient_data" explanation
