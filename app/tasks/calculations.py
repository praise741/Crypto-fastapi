from __future__ import annotations

from datetime import datetime


def recalculate_indices() -> None:
    print(f"Recalculating market indices at {datetime.utcnow().isoformat()}")


def recalculate_alerts() -> None:
    print("Re-evaluating alerts conditions against latest data")


def refresh_caches() -> None:
    print("Refreshing cached data for API consumers")
