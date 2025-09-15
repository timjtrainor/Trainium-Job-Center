"""Tests for infrastructure event bus handlers."""

import os
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

from app.services.infrastructure.event_bus import on_task_started


def test_on_task_started_with_none_task():
    """Ensure handler exits early when the task payload is missing."""

    event = SimpleNamespace(task=None)

    with patch("app.services.infrastructure.event_bus.get_database_service") as mock_get_db:
        on_task_started(event)
        mock_get_db.assert_not_called()
