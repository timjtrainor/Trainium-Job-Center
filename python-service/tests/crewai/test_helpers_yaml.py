"""
Test suite for helper agents YAML implementation.

Tests the helper agents system including data_analyst, strategist, stakeholder,
technical_leader, recruiter, skeptic, and optimizer agents.
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
)
from app.services.crewai.job_posting_review import _format_crew_result
from app.services.crewai import base


class TestHelpersYaml:
    """Test suite for YAML-driven helper agents system."""
    
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
    def sample_inputs_with_helpers(self, sample_job_posting) -> Dict[str, Any]:
        """Sample inputs with helpers enabled."""
        return {
            "job_posting_data": sample_job_posting,
            "options": {"use_helpers": True, "priority": "growth"}
        }
    
    @pytest.fixture
    def sample_inputs_without_helpers(self, sample_job_posting) -> Dict[str, Any]:
        """Sample inputs with helpers disabled."""
        return {
            "job_posting_data": sample_job_posting,
            "options": {"use_helpers": False, "priority": "growth"}
        }
    
    def test_helper_agents_yaml_loading(self):
        """Test that all helper agents are loaded correctly from YAML."""
        crew = MotivationalFanOutCrew()
        
        # Verify all seven helper agents are loaded
        required_helpers = [
            "data_analyst", "strategist", "stakeholder", "technical_leader",
            "recruiter", "skeptic", "optimizer"
        ]
        
        for helper_name in required_helpers:
            assert helper_name in crew.agents_config, f"Helper agent {helper_name} not found in config"
            
            # Verify required fields
            helper_config = crew.agents_config[helper_name]
            assert "role" in helper_config, f"Helper {helper_name} missing role"
            assert "goal" in helper_config, f"Helper {helper_name} missing goal"
            assert "backstory" in helper_config, f"Helper {helper_name} missing backstory"
            
            # Verify non-empty values
            assert helper_config["role"], f"Helper {helper_name} has empty role"
            assert helper_config["goal"], f"Helper {helper_name} has empty goal"
            assert helper_config["backstory"], f"Helper {helper_name} has empty backstory"
            
            # Verify helper-specific timeouts (should be faster than motivational agents)
            assert helper_config.get("max_execution_time", 45) <= 30, f"Helper {helper_name} should have faster execution time"
            assert helper_config.get("max_iter", 2) <= 1, f"Helper {helper_name} should have fewer iterations"
    
    def test_helper_tasks_yaml_loading(self):
        """Test that all helper tasks are loaded correctly from YAML."""
        crew = MotivationalFanOutCrew()
        
        # Verify all helper tasks plus aggregation task are loaded
        required_helper_tasks = [
            "data_analyst_task", "strategist_task", "stakeholder_task", 
            "technical_leader_task", "recruiter_task", "skeptic_task", "optimizer_task",
            "helper_snapshot"
        ]
        
        for task_name in required_helper_tasks:
            assert task_name in crew.tasks_config, f"Helper task {task_name} not found in config"
            
            # Verify required fields
            task_config = crew.tasks_config[task_name]
            assert "description" in task_config, f"Task {task_name} missing description"
            assert "expected_output" in task_config, f"Task {task_name} missing expected_output"
            assert "agent" in task_config, f"Task {task_name} missing agent assignment"
            
            # Verify compact output requirement for individual helpers
            if task_name != "helper_snapshot":
                description = task_config["description"]
                assert "600 chars" in description or "≤600" in description, f"Task {task_name} should specify 600 char limit"
                assert "JSON" in description, f"Task {task_name} should specify JSON output"
    
    def test_helper_output_structure_specifications(self):
        """Test that helper tasks specify correct compact JSON structure."""
        crew = MotivationalFanOutCrew()
        
        # Expected output structures for each helper
        expected_structures = {
            "data_analyst_task": ["tc_range", "refs"],
            "strategist_task": ["signals", "refs"],
            "stakeholder_task": ["partners", "risks"],
            "technical_leader_task": ["notes"],
            "recruiter_task": ["keyword_gaps"],
            "skeptic_task": ["redflags"],
            "optimizer_task": ["top3"]
        }
        
        for task_name, expected_keys in expected_structures.items():
            task_config = crew.tasks_config[task_name]
            description = task_config["description"]
            
            # Verify expected keys are mentioned in the description
            for key in expected_keys:
                assert key in description, f"Task {task_name} should specify {key} in output structure"
            
            # Verify fallback empty structure is specified
            assert "insufficient signal" in description.lower() or "empty" in description.lower(), \
                   f"Task {task_name} should specify fallback for insufficient data"
    
    def test_helper_snapshot_aggregation_task(self):
        """Test helper_snapshot task specification."""
        crew = MotivationalFanOutCrew()
        
        snapshot_config = crew.tasks_config["helper_snapshot"]
        description = snapshot_config["description"]
        
        # Verify conditional logic for use_helpers
        assert "use_helpers" in description, "helper_snapshot should check use_helpers option"
        assert "false" in description and "true" in description, "helper_snapshot should handle both true/false cases"
        
        # Verify size constraint
        assert "1.5 KB" in description or "1536" in description, "helper_snapshot should specify size limit"
        
        # Verify it merges all helper outputs
        helper_names = ["data_analyst", "strategist", "stakeholder", "technical_leader", "recruiter", "skeptic", "optimizer"]
        for helper_name in helper_names:
            assert helper_name in description, f"helper_snapshot should reference {helper_name}"
    
    @patch.dict(os.environ, {"CREWAI_MOCK_MODE": "true"})
    def test_helpers_disabled_returns_empty_snapshot(self, sample_inputs_without_helpers):
        """Test with use_helpers=false: crew run produces helper_snapshot = {} and motivational tasks still complete."""
        crew = MotivationalFanOutCrew()
        
        # Prepare inputs
        prepared_inputs = crew.prepare_inputs(sample_inputs_without_helpers)
        
        # Verify use_helpers is false
        assert prepared_inputs["options"].get("use_helpers") is False
        
        # Execute in mock mode
        result = crew.process_verdicts({"mock_mode": True, "options": {"use_helpers": False}})
        
        # Verify helper_snapshot is empty or missing
        helper_snapshot = result.get("helper_snapshot", {})
        assert helper_snapshot == {} or not helper_snapshot, "Should return empty helper_snapshot when use_helpers=false"
        
        # Verify motivational verdicts still work
        assert "motivational_verdicts" in result
        verdicts = result["motivational_verdicts"]
        assert len(verdicts) == 5, "Should still return 5 motivational verdicts"
        
        # Verify verdicts are well-formed
        for verdict in verdicts:
            assert "id" in verdict
            assert "recommend" in verdict
            assert "reason" in verdict
    
    @patch.dict(os.environ, {"CREWAI_MOCK_MODE": "true"})
    def test_helpers_enabled_returns_compact_snapshot(self, sample_inputs_with_helpers):
        """Test with use_helpers=true: crew run returns helper_snapshot containing keys with valid small JSON."""
        crew = MotivationalFanOutCrew()
        
        # Prepare inputs
        prepared_inputs = crew.prepare_inputs(sample_inputs_with_helpers)
        
        # Verify use_helpers is true
        assert prepared_inputs["options"].get("use_helpers") is True
        
        # Execute in mock mode
        result = crew.process_verdicts({"mock_mode": True, "options": {"use_helpers": True}})
        
        # Verify helper_snapshot contains data
        assert "helper_snapshot" in result
        helper_snapshot = result["helper_snapshot"]
        assert isinstance(helper_snapshot, dict), "helper_snapshot should be a dict"
        assert len(helper_snapshot) > 0, "helper_snapshot should contain helper data when enabled"
        
        # Verify key helpers are present
        required_helpers = ["data_analyst", "skeptic"]  # Minimum required by acceptance criteria
        for helper_name in required_helpers:
            assert helper_name in helper_snapshot, f"helper_snapshot should contain {helper_name}"
            assert isinstance(helper_snapshot[helper_name], dict), f"{helper_name} should be a dict"
        
        # Verify size constraint ≤1.5 KB
        serialized = json.dumps(helper_snapshot)
        assert len(serialized) <= 1536, f"helper_snapshot too large: {len(serialized)} chars > 1536"
        
        # Verify motivational verdicts still work
        assert "motivational_verdicts" in result
        verdicts = result["motivational_verdicts"]
        assert len(verdicts) == 5, "Should return 5 motivational verdicts with helpers enabled"
    
    def test_helper_task_failure_handling(self):
        """Test simulate a helper task failure and verify fallback to empty JSON while overall run succeeds."""
        crew = MotivationalFanOutCrew()
        
        # Mock helper snapshot output with some failures
        mock_helper_output = '''
        {
            "data_analyst": {"tc_range": "$120k-$160k", "refs": ["levels.fyi"]},
            "strategist": {"signals": [], "refs": []},
            "stakeholder": {},
            "technical_leader": {"notes": ["good architecture"]},
            "recruiter": {"keyword_gaps": []},
            "skeptic": {"redflags": []},
            "optimizer": {"top3": ["highlight experience"]}
        }
        '''
        
        # Test helper snapshot parsing with partial failures
        parsed_snapshot = crew._parse_helper_snapshot(mock_helper_output)
        
        assert isinstance(parsed_snapshot, dict), "Should return valid dict even with failures"
        assert "data_analyst" in parsed_snapshot, "Should include successful helper outputs"
        assert "technical_leader" in parsed_snapshot, "Should include successful helper outputs"
        
        # Test invalid JSON handling
        invalid_output = "invalid json structure {"
        parsed_invalid = crew._parse_helper_snapshot(invalid_output)
        assert parsed_invalid == {}, "Should return empty dict for invalid JSON"
        
        # Test oversized output handling
        oversized_output = '{"data": "' + "x" * 2000 + '"}'
        parsed_oversized = crew._parse_helper_snapshot(oversized_output)
        assert len(json.dumps(parsed_oversized)) <= 1536, "Should truncate oversized output"
    
    def test_helper_agent_method_binding(self):
        """Test that helper agent names match Python method names for proper YAML binding."""
        crew = MotivationalFanOutCrew()
        
        # Helper agent names in YAML should match method names
        helper_agents = ["data_analyst", "strategist", "stakeholder", "technical_leader", "recruiter", "skeptic", "optimizer"]
        
        for agent_name in helper_agents:
            # Agent should exist in YAML config
            assert agent_name in crew.agents_config, f"Missing YAML config for {agent_name}"
            
            # Method should exist in crew class
            assert hasattr(crew, agent_name), f"Missing method {agent_name} for YAML agent binding"
            
            # Method should be callable
            method = getattr(crew, agent_name)
            assert callable(method), f"Method {agent_name} should be callable"
    
    def test_helper_task_method_binding(self):
        """Test that helper task names match Python method names for proper YAML binding."""
        crew = MotivationalFanOutCrew()
        
        # Helper task names in YAML should match method names
        helper_tasks = [
            "data_analyst_task", "strategist_task", "stakeholder_task", 
            "technical_leader_task", "recruiter_task", "skeptic_task", "optimizer_task",
            "helper_snapshot"
        ]
        
        for task_name in helper_tasks:
            # Task should exist in YAML config
            assert task_name in crew.tasks_config, f"Missing YAML config for {task_name}"
            
            # Method should exist in crew class
            assert hasattr(crew, task_name), f"Missing method {task_name} for YAML task binding"
            
            # Method should be callable
            method = getattr(crew, task_name)
            assert callable(method), f"Method {task_name} should be callable"
    
    @patch.dict(os.environ, {"CREWAI_MOCK_MODE": "true"})
    def test_full_integration_with_helpers(self, sample_inputs_with_helpers):
        """Test full integration via run_crew function with helpers enabled."""
        result = run_crew(
            job_posting_data=sample_inputs_with_helpers["job_posting_data"],
            options=sample_inputs_with_helpers["options"],
            correlation_id="test-helpers-123"
        )
        
        # Test result structure
        assert "job_id" in result
        assert "final" in result
        assert "personas" in result
        
        # Test that helper insights may be referenced in motivational verdicts
        personas = result["personas"]
        assert len(personas) >= 5, "Should include all motivational evaluators"
        
        # Check if any motivational verdict references helper insights
        helper_referenced = False
        for persona in personas:
            reason = persona.get("reason", "")
            sources = persona.get("sources", [])
            if "helper" in reason.lower() or "helper_insights" in sources:
                helper_referenced = True
                break
        
        # In mock mode, we expect helper references
        assert helper_referenced, "At least one motivational verdict should reference helper insights in mock mode"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])