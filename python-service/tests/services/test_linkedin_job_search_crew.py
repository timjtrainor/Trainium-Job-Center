"""
Unit tests for LinkedIn Job Search CrewAI functionality.
"""
import pytest
from unittest.mock import patch, MagicMock
import os

from app.services.crewai.linkedin_job_search.crew import (
    LinkedInJobSearchCrew,
    get_linkedin_job_search_crew,
    run_linkedin_job_search
)


class TestLinkedInJobSearchCrew:
    """Test suite for LinkedInJobSearchCrew functionality."""
    
    @patch.dict('os.environ', {'CREWAI_MOCK_MODE': 'true'})
    def test_crew_initialization(self):
        """Test that crew initializes properly in mock mode."""
        crew = LinkedInJobSearchCrew()
        assert crew is not None
        
        # Test crew assembly
        assembled_crew = crew.crew()
        assert assembled_crew is not None
        assert len(assembled_crew.agents) == 3
        assert len(assembled_crew.tasks) == 3
    
    def test_agent_creation(self):
        """Test that all agents are created properly."""
        crew = LinkedInJobSearchCrew()
        
        # Test individual agents
        search_agent = crew.search_agent()
        assert search_agent is not None
        
        recommendation_agent = crew.recommendation_agent()
        assert recommendation_agent is not None
        
        orchestration_agent = crew.orchestration_agent()
        assert orchestration_agent is not None
    
    def test_task_creation(self):
        """Test that all tasks are created properly."""
        crew = LinkedInJobSearchCrew()
        
        # Test individual tasks
        search_task = crew.search_jobs_task()
        assert search_task is not None
        assert search_task.async_execution is True
        
        recommendations_task = crew.get_recommendations_task()
        assert recommendations_task is not None
        assert recommendations_task.async_execution is True
        
        consolidate_task = crew.consolidate_results_task()
        assert consolidate_task is not None
        # This task should not be async as it waits for context
        assert consolidate_task.async_execution is None or consolidate_task.async_execution is False
    
    @patch('app.services.crewai.linkedin_job_search.crew.load_mcp_tools_sync')
    def test_mcp_tools_loading(self, mock_load_tools):
        """Test MCP tools loading."""
        mock_tools = [MagicMock(name="search_jobs"), MagicMock(name="get_recommended_jobs")]
        mock_load_tools.return_value = mock_tools
        
        crew = LinkedInJobSearchCrew()
        assert hasattr(crew, '_linkedin_tools')
        
        # Verify correct tool names were requested
        mock_load_tools.assert_called_once_with(["search_jobs", "get_recommended_jobs"])
    
    def test_singleton_pattern(self):
        """Test that crew factory returns the same instance."""
        crew1 = get_linkedin_job_search_crew()
        crew2 = get_linkedin_job_search_crew()
        assert crew1 is crew2
    
    @patch('app.services.crewai.linkedin_job_search.crew.LinkedInJobSearchCrew')
    def test_execute_search_success(self, mock_crew_class):
        """Test successful search execution."""
        # Mock crew execution
        mock_crew_instance = MagicMock()
        mock_crew_class.return_value = mock_crew_instance
        
        mock_crew = MagicMock()
        mock_crew_instance.crew.return_value = mock_crew
        
        mock_result = {
            "success": True,
            "consolidated_jobs": [{"title": "Test Job", "company": "Test Co"}],
            "total_jobs": 1
        }
        mock_crew.kickoff.return_value = mock_result
        
        search_params = {"keywords": "python developer", "location": "Remote"}
        result = mock_crew_instance.crew().kickoff(inputs=search_params)
        
        assert result["success"] is True
        assert "consolidated_jobs" in result
        mock_crew.kickoff.assert_called_once_with(inputs=search_params)
    
    def test_execute_search_with_error_handling(self):
        """Test search execution with error handling."""
        crew = LinkedInJobSearchCrew()
        
        # Mock crew.kickoff to raise an exception
        with patch.object(type(crew.crew()), 'kickoff', side_effect=Exception("LinkedIn API error")):
            result = crew.execute_search({"keywords": "test"})
            
            assert result["success"] is False
            assert "error" in result
            assert "LinkedIn API error" in result["error"]
            assert result["consolidated_jobs"] == []
            assert result["total_jobs"] == 0
    
    def test_run_linkedin_job_search_convenience_function(self):
        """Test the convenience function for running searches."""
        with patch('app.services.crewai.linkedin_job_search.crew.get_linkedin_job_search_crew') as mock_get_crew:
            mock_crew = MagicMock()
            mock_get_crew.return_value = mock_crew
            
            mock_result = {"success": True, "total_jobs": 5}
            mock_crew.execute_search.return_value = mock_result
            
            result = run_linkedin_job_search(
                keywords="data scientist",
                location="San Francisco",
                remote=True,
                limit=10
            )
            
            assert result["success"] is True
            assert result["total_jobs"] == 5
            
            # Verify search params were processed correctly
            expected_params = {
                "keywords": "data scientist",
                "location": "San Francisco", 
                "remote": True,
                "limit": 10
            }
            mock_crew.execute_search.assert_called_once_with(expected_params)
    
    def test_parameter_filtering(self):
        """Test that None parameters are filtered out."""
        with patch('app.services.crewai.linkedin_job_search.crew.get_linkedin_job_search_crew') as mock_get_crew:
            mock_crew = MagicMock()
            mock_get_crew.return_value = mock_crew
            mock_crew.execute_search.return_value = {"success": True}
            
            run_linkedin_job_search(
                keywords="engineer",
                location=None,  # Should be filtered out
                job_type=None,  # Should be filtered out
                remote=False
            )
            
            # Verify None values were filtered
            expected_params = {
                "keywords": "engineer",
                "remote": False
            }
            mock_crew.execute_search.assert_called_once_with(expected_params)