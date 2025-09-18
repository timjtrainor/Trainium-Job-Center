"""
API tests for LinkedIn Job Search endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.services.crewai.linkedin_job_search.crew import LinkedInJobSearchCrew

client = TestClient(app)


class TestLinkedInJobSearchAPI:
    """Test suite for LinkedIn Job Search API endpoints."""
    
    @patch('app.services.crewai.linkedin_job_search.crew.get_linkedin_job_search_crew')
    def test_search_linkedin_jobs_success(self, mock_get_crew):
        """Test successful LinkedIn job search API call."""
        # Mock crew response
        mock_crew = MagicMock()
        mock_get_crew.return_value = mock_crew
        
        mock_result = {
            "success": True,
            "consolidated_jobs": [
                {
                    "title": "Software Engineer",
                    "company": "TechCorp",
                    "location": "San Francisco, CA",
                    "job_type": "full-time",
                    "job_url": "https://linkedin.com/jobs/123",
                    "site": "linkedin"
                }
            ],
            "total_jobs": 1,
            "search_jobs_count": 1,
            "recommended_jobs_count": 0,
            "duplicates_removed": 0,
            "consolidation_metadata": {}
        }
        mock_crew.execute_search.return_value = mock_result
        
        # Test API call
        request_data = {
            "keywords": "python developer",
            "location": "Remote",
            "remote": True,
            "limit": 10
        }
        
        response = client.post("/crewai/linkedin-job-search/search", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["total_jobs"] == 1
        assert len(data["data"]["consolidated_jobs"]) == 1
    
    @patch('app.services.crewai.linkedin_job_search.crew.get_linkedin_job_search_crew')
    def test_search_linkedin_jobs_failure(self, mock_get_crew):
        """Test LinkedIn job search API with failure."""
        # Mock crew failure
        mock_crew = MagicMock()
        mock_get_crew.return_value = mock_crew
        
        mock_result = {
            "success": False,
            "error": "LinkedIn API rate limit exceeded",
            "consolidated_jobs": [],
            "total_jobs": 0
        }
        mock_crew.execute_search.return_value = mock_result
        
        request_data = {
            "keywords": "data scientist",
            "limit": 25
        }
        
        response = client.post("/crewai/linkedin-job-search/search", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "LinkedIn job search failed" in data["error"]
    
    @patch('app.services.crewai.linkedin_job_search.crew.get_linkedin_job_search_crew')
    def test_search_with_invalid_request(self, mock_get_crew):
        """Test API with invalid request data."""
        # Missing required keywords field
        request_data = {
            "location": "New York",
            "limit": 10
        }
        
        response = client.post("/crewai/linkedin-job-search/search", json=request_data)
        
        # Should return validation error
        assert response.status_code == 422
    
    @patch('app.services.crewai.linkedin_job_search.crew.get_linkedin_job_search_crew')
    def test_health_check_success(self, mock_get_crew):
        """Test LinkedIn job search health check."""
        mock_crew = MagicMock()
        mock_crew._linkedin_tools = [MagicMock(), MagicMock()]
        mock_assembled_crew = MagicMock()
        mock_assembled_crew.agents = [MagicMock(), MagicMock(), MagicMock()]
        mock_assembled_crew.tasks = [MagicMock(), MagicMock(), MagicMock()]
        mock_crew.crew.return_value = mock_assembled_crew
        mock_get_crew.return_value = mock_crew
        
        response = client.get("/crewai/linkedin-job-search/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["crew_initialized"] is True
        assert data["data"]["linkedin_tools_loaded"] is True
        assert data["data"]["agents_count"] == 3
        assert data["data"]["tasks_count"] == 3
    
    @patch('app.services.crewai.linkedin_job_search.crew.get_linkedin_job_search_crew')
    def test_get_crew_config(self, mock_get_crew):
        """Test crew configuration endpoint."""
        mock_crew = MagicMock()
        mock_crew._linkedin_tools = [MagicMock(), MagicMock()]
        mock_get_crew.return_value = mock_crew
        
        response = client.get("/crewai/linkedin-job-search/config")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["crew_type"] == "linkedin_job_search"
        assert data["data"]["process"] == "sequential"
        assert len(data["data"]["agents"]) == 3
        assert len(data["data"]["tasks"]) == 3
        assert data["data"]["linkedin_tools_available"] == 2
    
    def test_parameter_validation(self):
        """Test request parameter validation."""
        # Test limit validation (too high)
        request_data = {
            "keywords": "engineer",
            "limit": 150  # Max is 100
        }
        
        response = client.post("/crewai/linkedin-job-search/search", json=request_data)
        assert response.status_code == 422
        
        # Test limit validation (too low)
        request_data = {
            "keywords": "engineer", 
            "limit": 0  # Min is 1
        }
        
        response = client.post("/crewai/linkedin-job-search/search", json=request_data)
        assert response.status_code == 422