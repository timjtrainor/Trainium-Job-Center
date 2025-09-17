"""
Unit tests for Brand-Driven Job Search CrewAI functionality.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio

from app.services.crewai.brand_driven_job_search.crew import (
    BrandDrivenJobSearchCrew,
    get_brand_driven_job_search_crew,
    run_brand_driven_job_search
)
from app.services.crewai.brand_driven_job_search.brand_search import BrandSearchHelper


class TestBrandDrivenJobSearchCrew:
    """Test suite for BrandDrivenJobSearchCrew functionality."""
    
    @patch.dict('os.environ', {'CREWAI_MOCK_MODE': 'true'})
    def test_crew_initialization(self):
        """Test that crew initializes properly in mock mode."""
        crew = BrandDrivenJobSearchCrew()
        assert crew is not None
        
        # Test crew assembly
        assembled_crew = crew.crew()
        assert assembled_crew is not None
        assert len(assembled_crew.agents) == 4
        assert len(assembled_crew.tasks) == 4
    
    def test_agent_creation(self):
        """Test that all agents are created properly."""
        crew = BrandDrivenJobSearchCrew()
        
        # Test individual agents
        brand_query_agent = crew.brand_query_generator()
        assert brand_query_agent is not None
        
        search_executor = crew.linkedin_search_executor()
        assert search_executor is not None
        
        alignment_scorer = crew.brand_alignment_scorer()
        assert alignment_scorer is not None
        
        orchestration_manager = crew.orchestration_manager()
        assert orchestration_manager is not None
    
    def test_task_creation(self):
        """Test that all tasks are created properly."""
        crew = BrandDrivenJobSearchCrew()
        
        # Test individual tasks
        brand_queries_task = crew.generate_brand_queries_task()
        assert brand_queries_task is not None
        assert brand_queries_task.async_execution is True
        
        search_task = crew.execute_brand_searches_task()
        assert search_task is not None
        assert search_task.async_execution is True
        
        scoring_task = crew.score_brand_alignment_task()
        assert scoring_task is not None
        assert scoring_task.async_execution is True
        
        compile_task = crew.compile_brand_driven_results_task()
        assert compile_task is not None
        # Final task should be synchronous
        assert compile_task.async_execution is None or compile_task.async_execution is False
    
    @patch('app.services.crewai.brand_driven_job_search.crew.load_mcp_tools_sync')
    def test_tools_loading(self, mock_load_tools):
        """Test LinkedIn and ChromaDB tools loading."""
        mock_linkedin_tools = [MagicMock(name="search_jobs")]
        mock_load_tools.return_value = mock_linkedin_tools
        
        crew = BrandDrivenJobSearchCrew()
        assert hasattr(crew, '_linkedin_tools')
        assert hasattr(crew, '_chroma_tools')
        
        # Verify LinkedIn tools were loaded
        mock_load_tools.assert_called_once_with(["search_jobs"])
    
    def test_singleton_pattern(self):
        """Test that crew factory returns the same instance."""
        crew1 = get_brand_driven_job_search_crew()
        crew2 = get_brand_driven_job_search_crew()
        assert crew1 is crew2
    
    @pytest.mark.asyncio
    @patch('app.services.crewai.brand_driven_job_search.brand_search.brand_search_helper.generate_search_queries')
    async def test_execute_brand_driven_search_success(self, mock_generate_queries):
        """Test successful brand-driven search execution."""
        # Mock brand query generation
        mock_queries = {
            "north_star_vision": {
                "keywords": "leadership strategy",
                "search_terms": ["leadership", "strategy"],
                "brand_section": "north_star_vision"
            }
        }
        mock_generate_queries.return_value = mock_queries
        
        crew = BrandDrivenJobSearchCrew()
        
        # Mock crew execution
        mock_result = {
            "success": True,
            "brand_driven_jobs": [{"title": "Senior Manager", "company": "TestCorp"}],
            "execution_summary": {
                "total_jobs_found": 1,
                "autonomous_search_success": True
            }
        }
        
        with patch.object(crew.crew(), 'kickoff', return_value=mock_result):
            result = await crew.execute_brand_driven_search("test_user_123")
            
            assert result["success"] is True
            assert "brand_driven_jobs" in result
            assert result["execution_summary"]["autonomous_search_success"] is True
    
    @pytest.mark.asyncio
    @patch('app.services.crewai.brand_driven_job_search.brand_search.brand_search_helper.generate_search_queries')
    async def test_execute_search_no_brand_data(self, mock_generate_queries):
        """Test search execution when no brand data is available."""
        # Mock empty brand queries
        mock_generate_queries.return_value = {}
        
        crew = BrandDrivenJobSearchCrew()
        result = await crew.execute_brand_driven_search("user_no_brand")
        
        assert result["success"] is False
        assert "No career brand data found" in result["error"]
        assert result["brand_driven_jobs"] == []
        assert result["execution_summary"]["autonomous_search_success"] is False
    
    @pytest.mark.asyncio
    async def test_execute_search_with_error_handling(self):
        """Test search execution with error handling."""
        crew = BrandDrivenJobSearchCrew()
        
        # Mock brand_search_helper to raise an exception
        with patch('app.services.crewai.brand_driven_job_search.brand_search.brand_search_helper.generate_search_queries', 
                   side_effect=Exception("ChromaDB connection error")):
            result = await crew.execute_brand_driven_search("test_user")
            
            assert result["success"] is False
            assert "ChromaDB connection error" in result["error"]
            assert result["brand_driven_jobs"] == []
    
    def test_get_brand_search_status(self):
        """Test brand search status retrieval."""
        crew = BrandDrivenJobSearchCrew()
        status = crew.get_brand_search_status("test_user")
        
        assert "user_id" in status
        assert "brand_data_available" in status
        assert "brand_sections" in status
        assert "can_execute_search" in status
        assert status["user_id"] == "test_user"
    
    @patch('app.services.crewai.brand_driven_job_search.crew.get_brand_driven_job_search_crew')
    def test_run_brand_driven_job_search_convenience_function(self, mock_get_crew):
        """Test the convenience function for running brand-driven searches."""
        mock_crew = MagicMock()
        mock_get_crew.return_value = mock_crew
        
        # Mock async method
        mock_result = {"success": True, "brand_driven_jobs": []}
        mock_crew.execute_brand_driven_search = AsyncMock(return_value=mock_result)
        
        # Mock asyncio handling
        with patch('asyncio.get_event_loop') as mock_get_loop:
            mock_loop = MagicMock()
            mock_get_loop.return_value = mock_loop
            mock_loop.is_running.return_value = False
            mock_loop.run_until_complete.return_value = mock_result
            
            result = run_brand_driven_job_search("test_user")
            
            assert result["success"] is True
            mock_loop.run_until_complete.assert_called_once()


class TestBrandSearchHelper:
    """Test suite for BrandSearchHelper functionality."""
    
    def test_brand_sections_defined(self):
        """Test that brand sections are properly defined."""
        helper = BrandSearchHelper()
        assert len(helper.BRAND_SECTIONS) == 5
        assert "north_star_vision" in helper.BRAND_SECTIONS
        assert "trajectory_mastery" in helper.BRAND_SECTIONS
        assert "values_compass" in helper.BRAND_SECTIONS
        assert "lifestyle_alignment" in helper.BRAND_SECTIONS
        assert "compensation_philosophy" in helper.BRAND_SECTIONS
    
    def test_extract_keywords_from_content(self):
        """Test keyword extraction from content."""
        helper = BrandSearchHelper()
        content = "I am passionate about software engineering and machine learning technologies"
        keywords = helper._extract_keywords_from_content(content)
        
        assert isinstance(keywords, list)
        assert len(keywords) > 0
        # Should extract meaningful words, not stop words
        assert "passionate" in keywords
        assert "software" in keywords
        assert "engineering" in keywords
        assert "machine" in keywords
        assert "learning" in keywords
        assert "technologies" in keywords
        # Should not include stop words
        assert "am" not in keywords
        assert "about" not in keywords
    
    def test_extract_keywords_empty_content(self):
        """Test keyword extraction with empty content."""
        helper = BrandSearchHelper()
        keywords = helper._extract_keywords_from_content("")
        assert keywords == []
    
    def test_generate_section_query_types(self):
        """Test query generation for different section types."""
        helper = BrandSearchHelper()
        
        brand_data = {
            "keywords": ["leadership", "strategy", "vision", "team"],
            "content": "Leading high-performing teams with strategic vision"
        }
        
        # Test different section types generate different query structures
        north_star_query = helper._generate_section_query("north_star_vision", brand_data)
        assert north_star_query["brand_section"] == "north_star_vision"
        assert "leadership" in north_star_query["job_types"]
        
        trajectory_query = helper._generate_section_query("trajectory_mastery", brand_data)
        assert trajectory_query["brand_section"] == "trajectory_mastery"
        assert "senior" in trajectory_query["job_types"]
        
        lifestyle_query = helper._generate_section_query("lifestyle_alignment", brand_data)
        assert lifestyle_query["brand_section"] == "lifestyle_alignment"
        assert "remote" in lifestyle_query["job_types"] or "hybrid" in lifestyle_query["job_types"]
    
    @pytest.mark.asyncio
    @patch('app.services.crewai.brand_driven_job_search.brand_search.chroma_search_tool')
    async def test_get_brand_section_success(self, mock_chroma_search):
        """Test successful brand section retrieval."""
        # Mock ChromaDB response
        mock_response = {
            "documents": [["Leadership and strategic vision content"]],
            "metadatas": [{"section": "north_star_vision", "user_id": "test_user"}]
        }
        mock_chroma_search.return_value = mock_response
        
        helper = BrandSearchHelper()
        result = await helper.get_brand_section("north_star_vision", "test_user")
        
        assert result["section"] == "north_star_vision"
        assert len(result["content"]) > 0
        assert isinstance(result["keywords"], list)
        assert len(result["keywords"]) > 0
    
    @pytest.mark.asyncio
    @patch('app.services.crewai.brand_driven_job_search.brand_search.chroma_search_tool')
    async def test_get_brand_section_no_results(self, mock_chroma_search):
        """Test brand section retrieval with no results."""
        # Mock empty ChromaDB response
        mock_chroma_search.return_value = {"documents": []}
        
        helper = BrandSearchHelper()
        result = await helper.get_brand_section("nonexistent_section", "test_user")
        
        assert result["section"] == "nonexistent_section"
        assert result["content"] == ""
        assert result["keywords"] == []