"""
Test suite for motivational fan-out YAML implementation.

Tests the YAML-driven CrewAI system for the five motivational evaluators:
builder, maximizer, harmonizer, pathfinder, adventurer.
"""

import pytest
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch
from typing import Dict, Any, List

# Import the crew implementation
from app.services.crewai.job_posting_review.crew import (
    MotivationalFanOutCrew, 
    run_crew,
    _format_crew_result
)
from app.services.crewai import base


class TestMotivationalFanOutYaml:
    """Test suite for YAML-driven motivational fan-out system."""
    
    @pytest.fixture
    def sample_job_posting(self) -> Dict[str, Any]:
        """Sample job posting data for testing."""
        return {
            "title": "Senior Software Engineer",
            "company": "TechCorp Inc",
            "location": "San Francisco, CA",
            "description": "We're looking for a senior software engineer to join our team building scalable systems using Python, React, and AWS. You'll work on designing distributed architectures and mentoring junior developers.",
            "url": "https://techcorp.com/jobs/senior-engineer"
        }
    
    @pytest.fixture
    def sample_inputs(self, sample_job_posting) -> Dict[str, Any]:
        """Sample inputs for crew execution."""
        return {
            "job_posting_data": sample_job_posting,
            "career_brand_digest": "Experienced software engineer with expertise in distributed systems and team leadership. Passionate about scalable architecture and mentoring.",
            "options": {"priority": "growth", "location_preference": "remote"}
        }
    
    def test_agents_yaml_loading(self):
        """Test that agents.yaml loads correctly with all required agents."""
        crew = MotivationalFanOutCrew()
        
        # Verify all five agents are loaded
        required_agents = ["builder", "maximizer", "harmonizer", "pathfinder", "adventurer"]
        for agent_name in required_agents:
            assert agent_name in crew.agents_config, f"Agent {agent_name} not found in config"
            
            # Verify required fields
            agent_config = crew.agents_config[agent_name]
            assert "role" in agent_config, f"Agent {agent_name} missing role"
            assert "goal" in agent_config, f"Agent {agent_name} missing goal"
            assert "backstory" in agent_config, f"Agent {agent_name} missing backstory"
            
            # Verify non-empty values
            assert agent_config["role"], f"Agent {agent_name} has empty role"
            assert agent_config["goal"], f"Agent {agent_name} has empty goal"
            assert agent_config["backstory"], f"Agent {agent_name} has empty backstory"
    
    def test_tasks_yaml_loading(self):
        """Test that tasks.yaml loads correctly with all required tasks."""
        crew = MotivationalFanOutCrew()
        
        # Verify all five tasks are loaded
        required_tasks = [
            "builder_evaluation", "maximizer_evaluation", "harmonizer_evaluation",
            "pathfinder_evaluation", "adventurer_evaluation"
        ]
        for task_name in required_tasks:
            assert task_name in crew.tasks_config, f"Task {task_name} not found in config"
            
            # Verify required fields
            task_config = crew.tasks_config[task_name]
            assert "description" in task_config, f"Task {task_name} missing description"
            assert "expected_output" in task_config, f"Task {task_name} missing expected_output"
            assert "agent" in task_config, f"Task {task_name} missing agent assignment"
    
    def test_placeholder_resolution(self):
        """Test that placeholders in tasks are correctly structured."""
        crew = MotivationalFanOutCrew()
        
        # Required placeholders that should appear in task descriptions
        required_placeholders = [
            "{job_title}", "{job_company}", "{job_location}", 
            "{job_description}", "{career_brand_digest}", "{options}"
        ]
        
        for task_name, task_config in crew.tasks_config.items():
            description = task_config["description"]
            
            # Verify all required placeholders are present
            for placeholder in required_placeholders:
                assert placeholder in description, f"Task {task_name} missing placeholder {placeholder}"
            
            # Verify JSON structure requirement is mentioned
            assert "JSON" in description or "json" in description, f"Task {task_name} doesn't specify JSON output"
            assert "persona_id" in description, f"Task {task_name} doesn't specify persona_id in output"
            assert "recommend" in description, f"Task {task_name} doesn't specify recommend field"
    
    @patch.dict(os.environ, {"CREWAI_MOCK_MODE": "true"})
    def test_crew_instantiation_mock_mode(self, sample_inputs):
        """Test crew can be instantiated and executed in mock mode."""
        crew = MotivationalFanOutCrew()
        
        # Test agent creation methods exist and work
        assert hasattr(crew, "builder_agent")
        assert hasattr(crew, "maximizer_agent") 
        assert hasattr(crew, "harmonizer_agent")
        assert hasattr(crew, "pathfinder_agent")
        assert hasattr(crew, "adventurer_agent")
        
        # Test task creation methods exist
        assert hasattr(crew, "builder_evaluation_task")
        assert hasattr(crew, "maximizer_evaluation_task")
        assert hasattr(crew, "harmonizer_evaluation_task") 
        assert hasattr(crew, "pathfinder_evaluation_task")
        assert hasattr(crew, "adventurer_evaluation_task")
        
        # Test crew creation
        crew_instance = crew.motivational_fanout()
        assert crew_instance is not None
        
        # Test input preparation
        prepared_inputs = crew.prepare_inputs(sample_inputs)
        assert "job_title" in prepared_inputs
        assert "job_company" in prepared_inputs
        assert "job_description" in prepared_inputs
        assert "career_brand_digest" in prepared_inputs
        assert "options" in prepared_inputs
        assert prepared_inputs["mock_mode"] is True
    
    @patch.dict(os.environ, {"CREWAI_MOCK_MODE": "true"})
    def test_mock_mode_verdict_structure(self, sample_inputs):
        """Test that mock mode returns correctly structured verdicts."""
        crew = MotivationalFanOutCrew()
        
        # Execute in mock mode
        result = crew.process_verdicts({"mock_mode": True})
        
        assert "motivational_verdicts" in result
        verdicts = result["motivational_verdicts"]
        assert len(verdicts) == 5, "Should return exactly 5 motivational verdicts"
        
        # Test each verdict structure
        expected_personas = ["builder", "maximizer", "harmonizer", "pathfinder", "adventurer"]
        actual_personas = [v["id"] for v in verdicts]

        for expected_persona in expected_personas:
            assert expected_persona in actual_personas, f"Missing persona {expected_persona}"

        # Test verdict structure
        for verdict in verdicts:
            assert "id" in verdict, "Verdict missing id"
            assert "recommend" in verdict, "Verdict missing recommend"
            assert "reason" in verdict, "Verdict missing reason"
            assert "notes" in verdict, "Verdict missing notes"
            assert "sources" in verdict, "Verdict missing sources"
            
            # Test data types
            assert isinstance(verdict["recommend"], bool), "recommend should be boolean"
            assert isinstance(verdict["reason"], str), "reason should be string"
            assert isinstance(verdict["notes"], list), "notes should be list"
            assert isinstance(verdict["sources"], list), "sources should be list"
            
            # Test content quality
            assert len(verdict["reason"]) > 0, "reason should not be empty"
            assert len(verdict["notes"]) > 0, "notes should not be empty"
            assert len(verdict["sources"]) > 0, "sources should not be empty"
    
    def test_task_failure_handling(self):
        """Test handling of failed tasks with insufficient signal."""
        crew = MotivationalFanOutCrew()
        
        # Mock task outputs with one failure
        mock_task_outputs = {
            "builder_evaluation": '{"persona_id": "builder", "recommend": true, "reason": "Good tech stack", "notes": ["Python", "AWS"], "sources": ["job_description"]}',
            "maximizer_evaluation": "",  # Empty output simulates failure
            "harmonizer_evaluation": '{"persona_id": "harmonizer", "recommend": false, "reason": "Culture unclear", "notes": ["Remote unclear"], "sources": ["job_description"]}',
            "pathfinder_evaluation": "invalid json{",  # Invalid JSON
            "adventurer_evaluation": '{"persona_id": "adventurer", "recommend": true, "reason": "Learning opportunities", "notes": ["New tech"], "sources": ["job_description"]}'
        }
        
        with patch.object(crew, '_extract_task_outputs', return_value=mock_task_outputs):
            result = crew.process_verdicts({"task_outputs": mock_task_outputs})
            
            verdicts = result["motivational_verdicts"]
            assert len(verdicts) == 5, "Should return verdicts for all 5 personas even with failures"
            
            # Check successful parsing
            builder_verdict = next(v for v in verdicts if v["id"] == "builder")
            assert builder_verdict["recommend"] is True
            assert "Good tech stack" in builder_verdict["reason"]
            
            # Check failure handling
            maximizer_verdict = next(v for v in verdicts if v["id"] == "maximizer")
            assert maximizer_verdict["recommend"] is False
            assert "insufficient signal" in maximizer_verdict["reason"]
            
            pathfinder_verdict = next(v for v in verdicts if v["id"] == "pathfinder")
            assert pathfinder_verdict["recommend"] is False
            assert "insufficient signal" in pathfinder_verdict["reason"]
    
    @patch.dict(os.environ, {"CREWAI_MOCK_MODE": "true"})
    def test_run_crew_integration(self, sample_job_posting):
        """Test full integration via run_crew function."""
        result = run_crew(
            job_posting_data=sample_job_posting,
            options={"test": True},
            correlation_id="test-123"
        )
        
        # Test result structure matches expected schema
        assert "job_id" in result
        assert "final" in result
        assert "personas" in result
        
        # Test final recommendation structure
        final = result["final"]
        assert "recommend" in final
        assert "rationale" in final
        assert "confidence" in final
        assert isinstance(final["recommend"], bool)
        
        # Test personas are actually motivational verdicts
        personas = result["personas"]
        assert len(personas) >= 5, "Should include all motivational evaluators"
        
        # Verify persona structure
        persona_ids = [p.get("id") for p in personas]
        expected_personas = ["builder", "maximizer", "harmonizer", "pathfinder", "adventurer"]
        for expected in expected_personas:
            assert expected in persona_ids, f"Missing {expected} in personas"
    
    def test_format_crew_result_aggregation(self, sample_job_posting):
        """Test _format_crew_result properly aggregates motivational verdicts."""
        # Test case: majority positive recommendations
        mock_verdicts = [
            {"persona_id": "builder", "recommend": True, "reason": "Good tech", "notes": [], "sources": ["job_desc"]},
            {"persona_id": "maximizer", "recommend": True, "reason": "Good growth", "notes": [], "sources": ["growth"]},
            {"persona_id": "harmonizer", "recommend": False, "reason": "Culture unclear", "notes": [], "sources": ["culture"]},
            {"persona_id": "pathfinder", "recommend": True, "reason": "Good path", "notes": [], "sources": ["career"]},
            {"persona_id": "adventurer", "recommend": True, "reason": "Innovation", "notes": [], "sources": ["tech"]}
        ]
        
        crew_result = {"motivational_verdicts": mock_verdicts}
        formatted = _format_crew_result(crew_result, sample_job_posting, "test-123")
        
        # Test aggregation logic
        assert formatted["final"]["recommend"] is True, "Should recommend with 4/5 positive"
        assert "4/5" in formatted["final"]["rationale"], "Should mention vote count"
        assert formatted["final"]["confidence"] in ["medium", "high"], "Should have medium/high confidence"
        
        # Test case: majority negative recommendations
        negative_verdicts = [v.copy() for v in mock_verdicts]
        for v in negative_verdicts[:4]:  # Make first 4 negative
            v["recommend"] = False
            
        crew_result_negative = {"motivational_verdicts": negative_verdicts}
        formatted_negative = _format_crew_result(crew_result_negative, sample_job_posting, "test-123")
        
        assert formatted_negative["final"]["recommend"] is False, "Should not recommend with 1/5 positive"
        assert "1/5" in formatted_negative["final"]["rationale"], "Should mention vote count"
    
    def test_yaml_agent_binding_names(self):
        """Test that YAML agent names match Python method names for proper binding."""
        crew = MotivationalFanOutCrew()
        
        # Agent names in YAML should match method names (without _agent suffix)
        yaml_agents = list(crew.agents_config.keys())
        expected_methods = [f"{name}_agent" for name in yaml_agents]
        
        for method_name in expected_methods:
            assert hasattr(crew, method_name), f"Missing method {method_name} for YAML agent binding"
            
        # Task names in YAML should match method names (without _task suffix)  
        yaml_tasks = list(crew.tasks_config.keys())
        expected_task_methods = [f"{name}_task" for name in yaml_tasks]
        
        for method_name in expected_task_methods:
            assert hasattr(crew, method_name), f"Missing method {method_name} for YAML task binding"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])