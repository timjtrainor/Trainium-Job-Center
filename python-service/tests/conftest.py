import os
from unittest.mock import Mock

import pytest

# Ensure required environment variables are present for tests
os.environ.setdefault("DATABASE_URL", "postgresql://fake:fake@localhost:5432/fake")


@pytest.fixture
def mock_db_service():
    """Return a database service mock with initialization flagged."""
    service = Mock()
    service.initialized = True
    return service


@pytest.fixture
def job_persistence_service(mock_db_service):
    """Provide a JobPersistenceService with its database dependency mocked."""
    from app.services.infrastructure.job_persistence import JobPersistenceService

    service = JobPersistenceService()
    service.db_service = mock_db_service
    return service
