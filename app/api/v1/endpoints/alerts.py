from __future__ import annotations

from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_current_active_user, get_db
from app.core.responses import success_response
from app.models.database.user import User
from app.models.schemas.alerts import AlertCreate
from app.services import alerts as alert_service

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("")
def list_user_alerts(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = [alert.model_dump() for alert in alert_service.list_alerts(db, current_user.id)]
    return success_response({"alerts": data})


@router.post("")
def create_alert(payload: AlertCreate, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    alert = alert_service.create_alert(db, current_user.id, payload)
    return success_response(alert.model_dump())


@router.get("/{alert_id}")
def read_alert(alert_id: str, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    alert = alert_service.get_alert(db, current_user.id, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return success_response(alert_service.serialize_alert(alert).model_dump())


@router.put("/{alert_id}")
def update_alert(alert_id: str, payload: AlertCreate, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    alert = alert_service.get_alert(db, current_user.id, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    updated = alert_service.update_alert(db, alert, payload)
    return success_response(updated.model_dump())


@router.delete("/{alert_id}")
def delete_alert(alert_id: str, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    alert = alert_service.get_alert(db, current_user.id, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert_service.delete_alert(db, alert)
    return success_response({"message": "Alert deleted"})


@router.get("/notifications")
def list_notifications(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    notifications = [n.model_dump() for n in alert_service.list_notifications(db, current_user.id)]
    return success_response({"notifications": notifications})


@router.post("/notifications/mark-read")
def mark_notifications(notification_ids: List[str] = Body(...), current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    updated = alert_service.mark_notifications_read(db, current_user.id, notification_ids)
    return success_response({"updated": updated})


@router.get("/notifications/stats")
def notification_stats(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    stats = alert_service.get_notification_stats(db, current_user.id)
    return success_response(stats.model_dump())
