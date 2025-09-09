"""
Test suite for motivational agents integration with helper agents.

Tests the integration between helper agents and motivational evaluators,
ensuring motivational verdicts can incorporate helper insights.
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


class TestMotivationalWithHelpersYaml:
    """Test suite for motivational agents integration with helper insights."""
    
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
    def sample_helper_snapshot(self) -> Dict[str, Any]:
        """Sample helper snapshot data."""
        return {
            "data_analyst": {
                "tc_range": "$120k-$160k",
                "refs": ["levels.fyi", "glassdoor"]
            },
            "strategist": {
                "signals": ["AI adoption growing", "cloud-first approach"],
                "refs": ["industry_report"]
            },
            "stakeholder": {
                "partners": ["product", "design", "data"],
                "risks": ["cross-team coordination"]
            },
            "technical_leader": {
                "notes": ["modern architecture", "good scalability patterns"]
            },
            "recruiter": {
                "keyword_gaps": ["Kubernetes", "microservices"]
            },
            "skeptic": {
                "redflags": []
            },
            "optimizer": {
                "top3": ["highlight cloud experience", "emphasize AI projects", "mention team leadership"]
            }
        }
    
    @pytest.fixture
    def sample_inputs_with_helpers(self, sample_job_posting) -> Dict[str, Any]:
        """Sample inputs with helpers enabled."""
        return {
            "job_posting_data": sample_job_posting,
            "career_brand_digest": "Experienced software engineer with expertise in distributed systems and team leadership.",
            "options": {"use_helpers": True, "priority": "growth"}
        }
    
    def test_motivational_tasks_reference_helper_snapshot_placeholder(self):
        """Test that all motivational tasks include {helper_snapshot} placeholder."""
        crew = MotivationalFanOutCrew()
        
        motivational_tasks = [
            "builder_evaluation", "maximizer_evaluation", "harmonizer_evaluation",
            "pathfinder_evaluation", "adventurer_evaluation"
        ]
        
        for task_name in motivational_tasks:
            task_config = crew.tasks_config[task_name]
            description = task_config["description"]
            
            # Verify helper_snapshot placeholder is present
            assert "{helper_snapshot}" in description, f"Task {task_name} should include {{helper_snapshot}} placeholder"
            
            # Verify guidance about using helper insights
            assert "helper_snapshot contains useful keys" in description.lower() or \
                   "helper insights" in description.lower(), \
                   f"Task {task_name} should include guidance about using helper insights"
            
            # Verify graceful handling when helpers are empty
            assert "otherwise proceed without helpers" in description.lower() or \
                   "proceed without helpers" in description.lower(), \
                   f"Task {task_name} should handle empty helper_snapshot gracefully"
    
    @patch.dict(os.environ, {"CREWAI_MOCK_MODE": "true"})
    def test_motivational_verdicts_with_helpers_enabled(self, sample_inputs_with_helpers):
        """Test with use_helpers=true: verify motivational verdict reasons may include brief references to helper_snapshot content."""
        crew = MotivationalFanOutCrew()
        
        # Execute in mock mode with helpers enabled
        result = crew.process_verdicts({"mock_mode": True})
        
        # Verify we have both motivational verdicts and helper snapshot
        assert "motivational_verdicts" in result
        assert "helper_snapshot" in result
        
        verdicts = result["motivational_verdicts"]
        helper_snapshot = result["helper_snapshot"]

        assert len(verdicts) == 5, "Should return 5 motivational verdicts"
        for verdict in verdicts:
            assert "id" in verdict
        assert len(helper_snapshot) > 0, "Should return non-empty helper snapshot"
        
        # Check that some motivational verdicts reference helper insights
        helper_references_found = 0
        for verdict in verdicts:
            reason = verdict.get("reason", "")
            sources = verdict.get("sources", [])
            
            # Look for helper-related content
            if any(keyword in reason.lower() for keyword in ["helper", "market data", "tc range", "trend"]) or \
               "helper_insights" in sources:
                helper_references_found += 1
        
        # In mock mode, we expect some helper references
        assert helper_references_found >= 1, "At least one motivational verdict should reference helper insights"
    
    def test_motivational_verdict_structure_with_helpers(self, sample_helper_snapshot):
        """Test that motivational verdicts maintain proper structure when incorporating helper insights."""
        crew = MotivationalFanOutCrew()
        
        # Mock a verdict that references helper data
        mock_verdict_with_helpers = '''
        {
            "persona_id": "maximizer",
            "recommend": true,
            "reason": "Strong growth potential with competitive TC range ($120k-$160k per market data) and emerging AI adoption trends",
            "notes": ["market-rate compensation", "AI growth opportunity", "career advancement potential"],
            "sources": ["compensation_analysis", "growth_opportunities", "helper_insights"]
        }
        '''
        
        parsed_verdict = crew._parse_verdict(mock_verdict_with_helpers, "maximizer")
        
        # Verify structure is maintained
        required_fields = ["id", "recommend", "reason", "notes", "sources"]
        for field in required_fields:
            assert field in parsed_verdict, f"Verdict should contain {field}"
        
        # Verify data types
        assert isinstance(parsed_verdict["recommend"], bool)
        assert isinstance(parsed_verdict["reason"], str)
        assert isinstance(parsed_verdict["notes"], list)
        assert isinstance(parsed_verdict["sources"], list)
        
        # Verify helper insights are referenced appropriately
        reason = parsed_verdict["reason"]
        assert len(reason) > 0, "Reason should not be empty"
        
        # Check for brief references (not verbose)
        assert len(reason) <= 200, "Reason with helper insights should still be brief"
    
    def test_motivational_verdicts_robust_without_helpers(self):
        """Test that motivational verdicts work robustly when helper_snapshot is empty."""
        crew = MotivationalFanOutCrew()
        
        # Mock a verdict without helper insights (empty helper_snapshot scenario)
        mock_verdict_no_helpers = '''
        {
            "persona_id": "builder",
            "recommend": true,
            "reason": "Strong technical building opportunities with modern stack and architecture challenges",
            "notes": ["Python/React/AWS stack", "distributed architecture", "mentoring opportunities"],
            "sources": ["job_description", "technical_requirements"]
        }
        '''
        
        parsed_verdict = crew._parse_verdict(mock_verdict_no_helpers, "builder")
        
        # Verify it works without helper references
        assert parsed_verdict["id"] == "builder"
        assert parsed_verdict["recommend"] is True
        assert len(parsed_verdict["reason"]) > 0
        assert len(parsed_verdict["notes"]) > 0
        assert len(parsed_verdict["sources"]) > 0
        
        # Verify no helper-specific references (graceful degradation)
        reason = parsed_verdict["reason"]
        sources = parsed_verdict["sources"]
        
        assert "helper" not in reason.lower()
        assert "helper_insights" not in sources
    
    def test_helper_snapshot_integration_in_crew_flow(self):
        """Test that helper_snapshot is properly integrated into the crew workflow."""
        crew = MotivationalFanOutCrew()
        
        # Verify task order in crew configuration
        from pathlib import Path
        import yaml
        
        config_file = Path(crew.base_dir) / "config" / "crew.yaml"
        with open(config_file, 'r') as f:
            crew_config = yaml.safe_load(f)
        
        tasks = crew_config.get("tasks", [])
        
        # Verify helper_snapshot comes before motivational tasks
        assert "helper_snapshot" in tasks, "helper_snapshot task should be in crew workflow"
        
        helper_index = tasks.index("helper_snapshot")
        motivational_tasks = ["builder_evaluation", "maximizer_evaluation", "harmonizer_evaluation", "pathfinder_evaluation", "adventurer_evaluation"]
        
        for motivational_task in motivational_tasks:
            if motivational_task in tasks:
                motivational_index = tasks.index(motivational_task)
                assert helper_index < motivational_index, f"helper_snapshot should come before {motivational_task}"
    
    @patch.dict(os.environ, {"CREWAI_MOCK_MODE": "true"}) 
    def test_format_crew_result_with_helper_insights(self, sample_job_posting, sample_helper_snapshot):
        """Test _format_crew_result properly handles results with helper insights."""
        # Mock crew result with helper snapshot
        mock_crew_result = {
            "motivational_verdicts": [
                {
                    "persona_id": "maximizer",
                    "recommend": True,
                    "reason": "Strong growth potential with competitive TC range and positive market trends",
                    "notes": ["market-rate compensation", "emerging AI opportunities"],
                    "sources": ["compensation_analysis", "helper_insights"]
                },
                {
                    "persona_id": "builder", 
                    "recommend": True,
                    "reason": "Excellent technical building opportunities with modern architecture patterns",
                    "notes": ["distributed systems", "scalable architecture"],
                    "sources": ["job_description", "technical_requirements"]
                },
                {
                    "persona_id": "skeptic",
                    "recommend": True,
                    "reason": "No significant red flags identified in analysis",
                    "notes": ["clean assessment"],
                    "sources": ["risk_analysis"]
                }
            ],
            "helper_snapshot": sample_helper_snapshot
        }
        
        formatted_result = _format_crew_result(mock_crew_result, sample_job_posting, "test-123")
        
        # Verify structure is maintained
        assert "job_id" in formatted_result
        assert "final" in formatted_result
        assert "personas" in formatted_result
        
        # Verify helper insights don't break aggregation logic
        final = formatted_result["final"]
        assert isinstance(final["recommend"], bool)
        assert isinstance(final["rationale"], str)
        assert isinstance(final["confidence"], str)
        
        personas = formatted_result["personas"]
        assert len(personas) >= 3, "Should include all provided personas"
        
        # Verify helper insights are preserved in persona data
        helper_referenced_persona = next(
            (p for p in personas if "helper_insights" in p.get("sources", [])), 
            None
        )
        assert helper_referenced_persona is not None, "Should preserve helper insights in sources"
    
    def test_payload_size_with_helpers(self, sample_helper_snapshot):
        """Test that payload sizes remain reasonable with helper integration."""
        crew = MotivationalFanOutCrew()
        
        # Test helper snapshot size constraint
        serialized_helpers = json.dumps(sample_helper_snapshot)
        assert len(serialized_helpers) <= 1536, f"Helper snapshot too large: {len(serialized_helpers)} chars"
        
        # Test combined payload size (helper + motivational verdicts)
        mock_result = {
            "motivational_verdicts": [
                {
                    "id": f"persona_{i}",
                    "recommend": True,
                    "reason": f"Test reason {i} with helper insights from market data",
                    "notes": [f"note {i}a", f"note {i}b"],
                    "sources": ["job_description", "helper_insights"]
                }
                for i in range(5)
            ],
            "helper_snapshot": sample_helper_snapshot
        }
        
        serialized_total = json.dumps(mock_result)
        
        # Total payload should remain reasonable (≤5KB for typical case)
        assert len(serialized_total) <= 5120, f"Total payload too large: {len(serialized_total)} chars"
    
    def test_conditional_helper_execution(self):
        """Test that helper execution is properly conditional based on options.use_helpers."""
        crew = MotivationalFanOutCrew()
        
        # Test inputs without use_helpers
        inputs_no_helpers = {
            "job_posting_data": {"title": "Test", "company": "Test", "description": "Test"},
            "options": {"use_helpers": False}
        }
        
        prepared_no_helpers = crew.prepare_inputs(inputs_no_helpers)
        assert prepared_no_helpers["options"]["use_helpers"] is False
        
        # Test inputs with use_helpers
        inputs_with_helpers = {
            "job_posting_data": {"title": "Test", "company": "Test", "description": "Test"},
            "options": {"use_helpers": True}
        }
        
        prepared_with_helpers = crew.prepare_inputs(inputs_with_helpers)
        assert prepared_with_helpers["options"]["use_helpers"] is True
        
        # Test missing use_helpers (should default to disabled)
        inputs_default = {
            "job_posting_data": {"title": "Test", "company": "Test", "description": "Test"},
            "options": {}
        }
        
        prepared_default = crew.prepare_inputs(inputs_default)
        assert prepared_default["options"].get("use_helpers") is not True  # Should be None or False
    
    @patch.dict(os.environ, {"CREWAI_MOCK_MODE": "true"})
    def test_full_integration_verdict_quality_with_helpers(self, sample_inputs_with_helpers):
        """Test full integration ensuring verdict quality is maintained with helper integration."""
        result = run_crew(
            job_posting_data=sample_inputs_with_helpers["job_posting_data"],
            options=sample_inputs_with_helpers["options"],
            correlation_id="test-integration-helpers"
        )
        
        # Verify overall result structure
        assert "job_id" in result
        assert "final" in result
        assert "personas" in result
        
        personas = result["personas"]
        assert len(personas) == 5, "Should return exactly 5 motivational verdicts"
        
        # Verify each persona maintains quality standards
        for persona in personas:
            # Required fields
            assert "id" in persona
            assert "recommend" in persona
            assert "reason" in persona
            assert "notes" in persona
            assert "sources" in persona

            # Quality checks
            assert len(persona["reason"]) > 10, f"Reason for {persona['id']} should be meaningful"
            assert len(persona["reason"]) <= 300, f"Reason for {persona['id']} should be concise"
            assert len(persona["notes"]) > 0, f"Notes for {persona['id']} should not be empty"
            assert len(persona["sources"]) > 0, f"Sources for {persona['id']} should not be empty"

            # Persona ID should be valid
            valid_personas = ["builder", "maximizer", "harmonizer", "pathfinder", "adventurer"]
            assert persona["id"] in valid_personas, f"Invalid persona id: {persona['id']}"
        
        # Check for appropriate helper integration
        final_rationale = result["final"]["rationale"]
        assert len(final_rationale) > 0, "Final rationale should not be empty"
        
        # Should work regardless of whether helpers are referenced
        # (this tests robustness of integration)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])