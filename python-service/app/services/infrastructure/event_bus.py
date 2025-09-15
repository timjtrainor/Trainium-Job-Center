"""Event bus handlers for queue worker lifecycle events."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Optional

from loguru import logger

from .database import get_database_service


def _ensure_event_loop() -> asyncio.AbstractEventLoop:
    """Return an event loop that can run blocking coroutine calls."""

    try:
        return asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


def _normalize_task_key(raw_key: Any) -> Optional[str]:
    """Coerce the raw task key into a string."""

    if raw_key is None:
        return None
    if isinstance(raw_key, bytes):
        try:
            return raw_key.decode()
        except UnicodeDecodeError:
            return None
    return str(raw_key)


def _extract_run_id(task: Any, task_key: str) -> Optional[str]:
    """Derive the run identifier associated with a queue task."""

    # Prefer explicit identifiers if available.
    task_id = getattr(task, "id", None)
    if task_id:
        return str(task_id)

    meta = getattr(task, "meta", None)
    if isinstance(meta, dict):
        run_id = meta.get("run_id")
        if run_id:
            return str(run_id)

    # Fallback to parsing the key used by RQ: ``rq:job:<job_id>``.
    if task_key:
        parts = task_key.split(":")
        if parts:
            return parts[-1] or task_key

    return None


def on_task_started(event: Any) -> None:
    """Handle queue task started events.

    The handler makes a best-effort attempt to update the associated scrape run
    in the database so that dashboards reflect that work has begun. It returns
    quietly when the event does not include a task or task key to avoid raising
    attribute errors from background worker threads.
    """

    if event is None:
        logger.debug("Received task started event without payload")
        return

    task = getattr(event, "task", None)
    if not task:
        logger.debug("Task started event missing task attribute; skipping")
        return

    task_key_raw = getattr(task, "key", None)
    if not task_key_raw:
        logger.debug("Task started event missing task key; skipping")
        return

    task_key = _normalize_task_key(task_key_raw)
    if not task_key:
        logger.debug("Task started event key could not be normalised; skipping")
        return

    run_id = _extract_run_id(task, task_key)
    if not run_id:
        logger.warning(
            "Unable to determine run identifier for started task",
            task_key=task_key,
        )
        return

    loop = _ensure_event_loop()
    db_service = get_database_service()

    try:
        if not db_service.initialized:
            loop.run_until_complete(db_service.initialize())

        started_at = datetime.now(timezone.utc)
        success = loop.run_until_complete(
            db_service.update_scrape_run_status(
                run_id=run_id,
                status="running",
                started_at=started_at,
                task_id=str(run_id),
            )
        )

        if success:
            logger.info(
                "Marked scrape run as running",
                run_id=run_id,
                task_key=task_key,
            )
        else:
            logger.warning(
                "Database did not acknowledge scrape run update",
                run_id=run_id,
                task_key=task_key,
            )
    except Exception as exc:  # pragma: no cover - logging defensive path
        logger.error(
            "Failed to process task started event",
            run_id=run_id,
            task_key=task_key,
            error=str(exc),
        )

