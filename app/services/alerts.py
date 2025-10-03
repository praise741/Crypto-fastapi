from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.database.alert import Alert
from app.models.database.notification import Notification
from app.models.schemas.alerts import (
    AlertCreate,
    AlertResponse,
    NotificationResponse,
    NotificationStats,
)


def serialize_alert(alert: Alert) -> AlertResponse:
    return AlertResponse(
        id=alert.id,
        user_id=alert.user_id,
        type=alert.type,
        symbol=alert.symbol,
        condition=alert.condition,
        notification=alert.notification,
        active=alert.active,
        created_at=alert.created_at,
        updated_at=alert.updated_at,
    )


def list_alerts(db: Session, user_id: str) -> List[AlertResponse]:
    alerts = (
        db.query(Alert)
        .filter(Alert.user_id == user_id)
        .order_by(Alert.created_at.desc())
        .all()
    )
    return [serialize_alert(alert) for alert in alerts]


def create_alert(db: Session, user_id: str, payload: AlertCreate) -> AlertResponse:
    alert = Alert(
        user_id=user_id,
        type=payload.type,
        symbol=payload.symbol,
        condition=payload.condition.model_dump(),
        notification=payload.notification.model_dump(),
        active=payload.active,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return serialize_alert(alert)


def get_alert(db: Session, user_id: str, alert_id: str) -> Alert | None:
    return (
        db.query(Alert).filter(Alert.id == alert_id, Alert.user_id == user_id).first()
    )


def update_alert(db: Session, alert: Alert, payload: AlertCreate) -> AlertResponse:
    alert.type = payload.type
    alert.symbol = payload.symbol
    alert.condition = payload.condition.model_dump()
    alert.notification = payload.notification.model_dump()
    alert.active = payload.active
    alert.updated_at = datetime.utcnow()
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return serialize_alert(alert)


def delete_alert(db: Session, alert: Alert) -> None:
    db.delete(alert)
    db.commit()


def list_notifications(db: Session, user_id: str) -> List[NotificationResponse]:
    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .all()
    )
    return [
        NotificationResponse(
            id=item.id,
            user_id=item.user_id,
            alert_id=item.alert_id,
            channel=item.channel,
            payload=item.payload,
            read=item.read,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
        for item in notifications
    ]


def mark_notifications_read(
    db: Session, user_id: str, notification_ids: List[str]
) -> int:
    updated = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.id.in_(notification_ids))
        .update({Notification.read: True}, synchronize_session=False)
    )
    db.commit()
    return updated


def get_notification_stats(db: Session, user_id: str) -> NotificationStats:
    total = db.query(Notification).filter(Notification.user_id == user_id).count()
    unread = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.read.is_(False))
        .count()
    )
    channels: dict[str, int] = {}
    for channel, count in (
        db.query(Notification.channel, func.count(Notification.id))
        .filter(Notification.user_id == user_id)
        .group_by(Notification.channel)
        .all()
    ):
        channels[channel] = count
    return NotificationStats(total=total, unread=unread, channels=channels)
