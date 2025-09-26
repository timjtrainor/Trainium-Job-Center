import asyncio
import os
from unittest.mock import AsyncMock, Mock, patch

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

from app.services.infrastructure.scheduler import SchedulerService


def test_malformed_payload_marks_run_failed_and_releases_lock():
    async def run_test():
        mock_db_service = Mock()
        mock_db_service.initialize = AsyncMock(return_value=True)
        mock_db_service.get_enabled_site_schedules = AsyncMock(return_value=[{
            "site_name": "ExampleSite",
            "id": "schedule-1",
            "payload": "{not-json",
            "interval_minutes": 30,
        }])
        mock_db_service.check_site_lock = AsyncMock(return_value=False)
        mock_db_service.create_scrape_run = AsyncMock(return_value="scrape-run-db-id")
        mock_db_service.update_scrape_run_status = AsyncMock(return_value=True)
        mock_db_service.update_site_schedule_next_run = AsyncMock(return_value=True)

        mock_queue_service = Mock()
        mock_queue_service.initialize = AsyncMock(return_value=True)
        mock_queue_service.get_queue_info = Mock(return_value={})
        mock_queue_service.check_redis_lock = Mock(return_value=False)
        mock_queue_service.acquire_redis_lock = Mock(return_value=True)
        mock_queue_service.release_redis_lock = Mock()
        mock_queue_service.enqueue_scraping_job = Mock()
        mock_queue_service.enqueue_linkedin_job_search = Mock()

        fake_uuid = Mock(hex="cafebabe12345678")

        with patch("app.services.infrastructure.scheduler.get_database_service", return_value=mock_db_service), \
             patch("app.services.infrastructure.scheduler.get_queue_service", return_value=mock_queue_service), \
             patch("app.services.infrastructure.scheduler.uuid.uuid4", return_value=fake_uuid):

            scheduler = SchedulerService()
            scheduler.initialized = True

            jobs_enqueued = await scheduler.process_scheduled_sites()

        assert jobs_enqueued == 0

        mock_queue_service.acquire_redis_lock.assert_called_once()
        mock_queue_service.release_redis_lock.assert_called_once()
        lock_args = mock_queue_service.release_redis_lock.call_args[0]
        assert lock_args[0] == "scrape_lock:ExampleSite"
        assert lock_args[1].startswith("sched_cafebabe")

        mock_db_service.create_scrape_run.assert_awaited_once()
        mock_db_service.update_scrape_run_status.assert_awaited_once()
        status_call = mock_db_service.update_scrape_run_status.await_args_list[0]
        assert status_call.kwargs["run_id"].startswith("sched_cafebabe")
        assert status_call.kwargs["status"] == "failed"
        assert "Failed to parse payload JSON" in status_call.kwargs["message"]

        mock_queue_service.enqueue_scraping_job.assert_not_called()
        mock_queue_service.enqueue_linkedin_job_search.assert_not_called()

    asyncio.run(run_test())
