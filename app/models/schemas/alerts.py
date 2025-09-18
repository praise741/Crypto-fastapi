from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class AlertCondition(BaseModel):
    operator: str
    value: float | None = None
    check_interval: str | None = None


class AlertNotification(BaseModel):
    channels: List[str]
    webhook_url: Optional[str] = None
    message_template: Optional[str] = None


class AlertCreate(BaseModel):
    type: str
    symbol: Optional[str] = None
    condition: AlertCondition
    notification: AlertNotification
    active: bool = True


class AlertResponse(BaseModel):
    id: str
    user_id: str
    type: str
    symbol: Optional[str] = None
    condition: dict
    notification: dict
    active: bool
    created_at: datetime
    updated_at: datetime


class NotificationResponse(BaseModel):
    id: str
    user_id: str
    alert_id: Optional[str] = None
    channel: str
    payload: dict
    read: bool
    created_at: datetime
    updated_at: datetime


class NotificationStats(BaseModel):
    total: int
    unread: int
    channels: dict
