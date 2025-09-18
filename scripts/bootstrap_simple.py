"""Bootstrap script to fetch live data and generate Prophet predictions."""

from __future__ import annotations

import logging

from dotenv import load_dotenv

from app.core.database import init_db
from app.tasks.ingestion import bootstrap_all


def main() -> None:
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    logging.info("Initializing database")
    init_db()
    logging.info("Bootstrapping market data and predictions")
    bootstrap_all()
    logging.info("Bootstrap complete. Start the API with `uvicorn app.main:app --host 0.0.0.0 --port 8000`.")


if __name__ == "__main__":
    main()
