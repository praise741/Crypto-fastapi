from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel


class IndexComponent(BaseModel):
    name: str
    value: float


class IndexResponse(BaseModel):
    index: str
    value: float
    classification: Optional[str] = None
    components: Dict[str, float] | None = None
    timestamp: datetime
    change_24h: float | None = None


class IndexHistoryItem(BaseModel):
    timestamp: datetime
    value: float
    change_24h: float | None = None
    components: Dict[str, float] | None = None


class IndexHistoryResponse(BaseModel):
    index: str
    items: List[IndexHistoryItem]
