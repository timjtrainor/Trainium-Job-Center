"""
Test cases for the poller service.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from uuid import uuid4

from python_service.app.services.infrastructure.poller import PollerService


class TestPollerService:
    """Test cases for the PollerService."""

    @pytest.fixture
    def poller_service(self):
        """Create a PollerService instance for testing."""
        with patch('python_service.app.services.infrastructure.poller.get_database_service') as mock_db_service, \
             patch('python_service.app.services.infrastructure.poller.get_queue_service') as mock_queue_service:
            
            # Setup mock services
            mock_db_service.return_value.initialize = AsyncMock(return_value=True)
            mock_queue_service.return_value.initialize = AsyncMock(return_value=True)
            
            poller = PollerService()
            return poller

    @pytest.mark.asyncio
    async def test_initialization(self, poller_service):
        """Test that the poller service initializes correctly."""
        # Test successful initialization
        result = await poller_service.initialize()
        assert result is True
        assert poller_service.initialized is True

    @pytest.mark.asyncio 
    async def test_get_pending_review_jobs(self, poller_service):
        """Test fetching jobs with pending_review status."""
        # Setup
        await poller_service.initialize()
        
        # Mock data
        mock_jobs = [
            {
                'id': uuid4(),
                'title': 'Senior Python Developer',
                'company': 'Tech Corp',
                'site': 'indeed',
                'job_url': 'https://example.com/job1',
                'ingested_at': datetime.now(timezone.utc)
            }
        ]
        
        # Mock database response
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = [MagicMock(**job) for job in mock_jobs]
        
        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        poller_service.db_service.pool = mock_pool
        
        # Test
        jobs = await poller_service.get_pending_review_jobs()
        
        # Assertions
        assert len(jobs) == 1
        assert jobs[0]['title'] == 'Senior Python Developer'
        
        # Verify query was called
        mock_conn.fetch.assert_called_once()
        call_args = mock_conn.fetch.call_args[0][0]
        assert "status = 'pending_review'" in call_args

    @pytest.mark.asyncio
    async def test_update_job_status(self, poller_service):
        """Test updating job status."""
        # Setup
        await poller_service.initialize()
        job_id = str(uuid4())
        
        # Mock database connection
        mock_conn = AsyncMock()
        mock_conn.execute.return_value = "UPDATE 1"
        
        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        poller_service.db_service.pool = mock_pool
        
        # Test successful update
        result = await poller_service.update_job_status(job_id, "in_review")
        
        # Assertions
        assert result is True
        mock_conn.execute.assert_called_once()

    def test_enqueue_job_review(self, poller_service):
        """Test enqueuing a job for review."""
        # Setup
        poller_service.initialized = True
        job_id = str(uuid4())
        job_data = {
            'id': job_id,
            'title': 'Test Job',
            'company': 'Test Company', 
            'site': 'test_site',
            'job_url': 'https://example.com/test',
            'ingested_at': datetime.now(timezone.utc)
        }
        
        # Mock queue service
        mock_task_id = "task_123"
        poller_service.queue_service.enqueue_job_review = MagicMock(return_value=mock_task_id)
        
        # Test
        result = poller_service.enqueue_job_review(job_id, job_data)

        # Assertions
        assert result == mock_task_id
        poller_service.queue_service.enqueue_job_review.assert_called_once_with(job_id)

    @pytest.mark.asyncio
    async def test_poll_and_enqueue_jobs_empty(self, poller_service):
        """Test polling when no jobs are pending review."""
        # Setup
        await poller_service.initialize()
        
        # Mock empty result
        poller_service.get_pending_review_jobs = AsyncMock(return_value=[])
        
        # Test
        result = await poller_service.poll_and_enqueue_jobs()
        
        # Assertions
        assert result == 0
        poller_service.get_pending_review_jobs.assert_called_once()