"""
End-to-end test suite for judge aggregation path.

Tests the complete workflow from job posting input through motivational verdicts
to final judge decision, ensuring deterministic behavior.
"""

import pytest
import json
import os
import uuid
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

# Import the crew implementation
from app.services.crewai.job_posting_review.crew import (
    MotivationalFanOutCrew, 
    run_crew,
    _format_crew_result
)
from app.services.crewai import base


class TestEndToEndJudgePath:
    """Test suite for end-to-end judge aggregation workflow."""
    
    @pytest.fixture
    def sample_job_posting(self) -> Dict[str, Any]:
        """Sample job posting for end-to-end testing."""
        return {
            "title": "Senior Software Engineer",
            "company": "TechCorp Inc",
            "location": "San Francisco, CA",
            "description": "We're looking for a senior software engineer to join our team building scalable systems using Python, React, and AWS. Competitive salary $140k-$180k. You'll work on designing distributed architectures and mentoring junior developers.",
            "url": "https://techcorp.com/jobs/senior-engineer"
        }

    @pytest.fixture
    def sample_options_with_helpers(self) -> Dict[str, Any]:
        """Sample options with helpers enabled."""
        return {
            "use_helpers": True,
            "priority": "growth",
            "location_preference": "remote"
        }

    @pytest.fixture
    def sample_options_without_helpers(self) -> Dict[str, Any]:
        """Sample options with helpers disabled."""
        return {
            "use_helpers": False,
            "priority": "growth"
        }

    @pytest.fixture
    def mock_motivational_verdicts_deterministic(self) -> List[Dict[str, Any]]:
        """Deterministic motivational verdicts for testing."""
        return [
            {
                "persona_id": "builder",
                "recommend": True,
                "reason": "Strong technical building opportunities with modern stack",
                "notes": ["Complex system architecture", "Engineering ownership"],
                "sources": ["job_description", "technical_requirements"]
            },
            {
                "persona_id": "maximizer",
                "recommend": True,
                "reason": "Excellent growth potential with competitive $140k-$180k range",
                "notes": ["Market-rate salary", "Learning opportunities"],
                "sources": ["compensation_analysis", "growth_opportunities"]
            },
            {
                "persona_id": "harmonizer",
                "recommend": True,
                "reason": "Positive team collaboration and mentoring culture",
                "notes": ["Mentoring opportunities", "Collaborative environment"],
                "sources": ["culture_indicators", "work_environment"]
            },
            {
                "persona_id": "pathfinder",
                "recommend": False,
                "reason": "Limited strategic positioning in traditional tech stack",
                "notes": ["Mature technology", "Standard career path"],
                "sources": ["career_strategy", "industry_analysis"]
            },
            {
                "persona_id": "adventurer",
                "recommend": True,
                "reason": "Good balance of proven tech with system design challenges",
                "notes": ["Architecture challenges", "Scalability problems"],
                "sources": ["innovation_indicators", "learning_opportunities"]
            }
        ]

    @pytest.fixture
    def mock_helper_snapshot_deterministic(self) -> Dict[str, Any]:
        """Deterministic helper snapshot for testing."""
        return {
            "data_analyst": {
                "tc_range": "$140k-$180k aligns with market", 
                "refs": ["levels.fyi", "glassdoor"]
            },
            "strategist": {
                "signals": ["cloud adoption", "python demand"], 
                "refs": ["stack_overflow_survey"]
            },
            "stakeholder": {
                "partners": ["engineering", "product"],
                "risks": ["mentoring overhead"]
            },
            "technical_leader": {
                "notes": ["scalable systems", "distributed architecture"]
            },
            "recruiter": {
                "keyword_gaps": ["kubernetes", "microservices"]
            },
            "skeptic": {
                "redflags": []
            },
            "optimizer": {
                "top3": ["highlight Python experience", "emphasize scalability projects", "mention mentoring skills"]
            }
        }

    def test_crew_instantiation_with_judge(self):
        """Test that crew can be instantiated with judge configuration."""
        crew = MotivationalFanOutCrew()
        
        # Verify judge components exist
        assert hasattr(crew, "judge"), "Crew missing judge agent method"
        assert hasattr(crew, "judge_aggregation"), "Crew missing judge task method"
        
        # Verify judge is in agents config
        assert "judge" in crew.agents_config, "Judge not in agents config"
        assert "judge_aggregation" in crew.tasks_config, "Judge task not in tasks config"

    @patch.dict(os.environ, {"CREWAI_MOCK_MODE": "true"})
    def test_run_crew_with_judge_mock_mode(self, sample_job_posting, sample_options_with_helpers):
        """Test end-to-end crew execution in mock mode includes judge decision."""
        correlation_id = str(uuid.uuid4())
        
        # Execute crew with judge
        result = run_crew(
            job_posting_data=sample_job_posting,
            options=sample_options_with_helpers,
            correlation_id=correlation_id
        )
        
        # Verify result structure
        assert "job_id" in result, "Missing job_id in result"
        assert "final" in result, "Missing final decision in result"
        assert "personas" in result, "Missing personas in result"
        
        # Verify final decision structure
        final = result["final"]
        assert "recommend" in final, "Missing recommend in final decision"
        assert "rationale" in final, "Missing rationale in final decision"
        assert "confidence" in final, "Missing confidence in final decision"
        
        # Verify personas are present (motivational verdicts)
        personas = result["personas"]
        assert len(personas) == 5, "Should have 5 motivational persona verdicts"
        
        persona_ids = {p["persona_id"] for p in personas}
        expected_personas = {"builder", "maximizer", "harmonizer", "pathfinder", "adventurer"}
        assert persona_ids == expected_personas, "Missing expected persona IDs"

    def test_deterministic_behavior_identical_inputs(self, sample_job_posting, sample_options_with_helpers):
        """Test that identical inputs produce deterministic results."""
        correlation_id = str(uuid.uuid4())
        
        # Mock the crew execution to control verdicts
        with patch.object(MotivationalFanOutCrew, 'process_verdicts') as mock_process:
            mock_result = {
                "motivational_verdicts": [
                    {"persona_id": "builder", "recommend": True, "reason": "Test reason", "notes": [], "sources": []},
                    {"persona_id": "maximizer", "recommend": True, "reason": "Test reason", "notes": [], "sources": []},
                    {"persona_id": "harmonizer", "recommend": True, "reason": "Test reason", "notes": [], "sources": []},
                    {"persona_id": "pathfinder", "recommend": False, "reason": "Test reason", "notes": [], "sources": []},
                    {"persona_id": "adventurer", "recommend": True, "reason": "Test reason", "notes": [], "sources": []}
                ],
                "helper_snapshot": {}
            }
            mock_process.return_value = mock_result
            
            # Execute twice with identical inputs
            result1 = run_crew(
                job_posting_data=sample_job_posting,
                options=sample_options_with_helpers,
                correlation_id=correlation_id
            )
            
            result2 = run_crew(
                job_posting_data=sample_job_posting,
                options=sample_options_with_helpers,
                correlation_id=correlation_id
            )
            
            # Results should be identical (deterministic)
            assert result1["final"]["recommend"] == result2["final"]["recommend"]
            assert result1["final"]["confidence"] == result2["final"]["confidence"]
            # Note: rationale might vary slightly due to LLM, but recommendation should be consistent

    def test_weights_injection_in_prepare_inputs(self, sample_job_posting):
        """Test that weights and guardrails are properly injected into inputs."""
        crew = MotivationalFanOutCrew()
        
        # Prepare inputs
        raw_inputs = {
            "job_posting_data": sample_job_posting,
            "career_brand_digest": "Test career context",
            "options": {"priority": "growth"}
        }
        
        prepared_inputs = crew.prepare_inputs(raw_inputs)
        
        # Verify weights and guardrails are injected
        assert "weights" in prepared_inputs, "Missing weights in prepared inputs"
        assert "guardrails" in prepared_inputs, "Missing guardrails in prepared inputs"
        assert "job_meta" in prepared_inputs, "Missing job_meta in prepared inputs"
        
        # Verify weights structure
        weights = prepared_inputs["weights"]
        expected_personas = ["builder", "maximizer", "harmonizer", "pathfinder", "adventurer"]
        for persona in expected_personas:
            assert persona in weights, f"Missing weight for {persona}"
        
        # Verify guardrails structure
        guardrails = prepared_inputs["guardrails"]
        expected_guardrails = ["comp_floor_enforced", "severe_redflags_block", "tie_bias"]
        for guardrail in expected_guardrails:
            assert guardrail in guardrails, f"Missing guardrail {guardrail}"

    def test_task_execution_order(self):
        """Test that judge task is configured to run after motivational tasks."""
        crew = MotivationalFanOutCrew()
        
        # Load crew configuration
        crew_yaml_path = crew.base_dir / "config" / "crew.yaml"
        import yaml
        with open(crew_yaml_path, 'r') as f:
            crew_config = yaml.safe_load(f)
        
        tasks = crew_config.get("tasks", [])
        
        # Find positions
        judge_pos = tasks.index("judge_aggregation") if "judge_aggregation" in tasks else -1
        helper_pos = tasks.index("helper_snapshot") if "helper_snapshot" in tasks else -1
        
        motivational_positions = []
        motivational_tasks = ["builder_evaluation", "maximizer_evaluation", "harmonizer_evaluation", 
                            "pathfinder_evaluation", "adventurer_evaluation"]
        for task in motivational_tasks:
            if task in tasks:
                motivational_positions.append(tasks.index(task))
        
        # Verify execution order
        assert judge_pos > -1, "judge_aggregation task not found in crew configuration"
        assert helper_pos > -1, "helper_snapshot task not found in crew configuration"
        assert len(motivational_positions) > 0, "No motivational tasks found in crew configuration"
        
        # Judge should run after helper and motivational tasks
        assert judge_pos > helper_pos, "judge_aggregation should run after helper_snapshot"
        for pos in motivational_positions:
            assert judge_pos > pos, "judge_aggregation should run after motivational tasks"

    @patch.dict(os.environ, {"CREWAI_MOCK_MODE": "false"})
    def test_error_handling_in_judge_path(self, sample_job_posting):
        """Test error handling when judge aggregation fails."""
        correlation_id = str(uuid.uuid4())
        
        # Mock crew execution failure
        with patch.object(MotivationalFanOutCrew, 'motivational_fanout') as mock_crew:
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.side_effect = Exception("Simulated crew failure")
            mock_crew.return_value = mock_crew_instance
            
            # Should raise exception
            with pytest.raises(Exception, match="Simulated crew failure"):
                run_crew(
                    job_posting_data=sample_job_posting,
                    options={"priority": "growth"},
                    correlation_id=correlation_id
                )

    def test_judge_input_validation(self, sample_job_posting):
        """Test that judge receives properly formatted inputs."""
        crew = MotivationalFanOutCrew()
        
        # Test input preparation
        raw_inputs = {
            "job_posting_data": sample_job_posting,
            "career_brand_digest": "Test context",
            "options": {"use_helpers": True}
        }
        
        prepared = crew.prepare_inputs(raw_inputs)
        
        # Verify all judge placeholders are prepared
        judge_placeholders = [
            "motivational_verdicts", "helper_snapshot", 
            "weights", "guardrails", "job_meta"
        ]
        
        for placeholder in judge_placeholders:
            assert placeholder in prepared, f"Missing placeholder {placeholder} for judge"
        
        # Verify data types
        assert isinstance(prepared["weights"], dict), "Weights should be dict"
        assert isinstance(prepared["guardrails"], dict), "Guardrails should be dict"
        assert isinstance(prepared["job_meta"], dict), "Job meta should be dict"

    def test_configuration_loading_resilience(self):
        """Test that system handles missing configuration gracefully."""
        crew = MotivationalFanOutCrew()
        
        # Test weights/guardrails loading with fallback
        config = crew._load_weights_guardrails_config()
        
        # Should always return valid structure
        assert "review_weights" in config, "Should provide fallback weights"
        assert "guardrails" in config, "Should provide fallback guardrails"
        
        # Weights should sum to reasonable total
        weights = config["review_weights"]
        total_weight = sum(weights.values())
        assert 0.9 <= total_weight <= 1.1, f"Weights should sum to ~1.0, got {total_weight}"

    @patch.dict(os.environ, {"CREWAI_MOCK_MODE": "true"})
    def test_full_pipeline_with_helpers_enabled(self, sample_job_posting, sample_options_with_helpers):
        """Test complete pipeline with helpers enabled."""
        correlation_id = str(uuid.uuid4())
        
        # Execute full pipeline
        result = run_crew(
            job_posting_data=sample_job_posting,
            options=sample_options_with_helpers,
            correlation_id=correlation_id
        )
        
        # Verify complete result structure
        required_keys = ["job_id", "final", "personas", "tradeoffs", "actions", "sources"]
        for key in required_keys:
            assert key in result, f"Missing required key {key} in result"
        
        # Verify final decision is well-formed
        final = result["final"]
        assert isinstance(final["recommend"], bool), "Recommend should be boolean"
        assert isinstance(final["rationale"], str), "Rationale should be string"
        assert final["confidence"] in ["low", "medium", "high"], "Invalid confidence level"
        
        # Verify personas (should be motivational verdicts)
        personas = result["personas"]
        assert len(personas) == 5, "Should have exactly 5 persona verdicts"
        
        for persona in personas:
            assert "persona_id" in persona, "Missing persona_id"
            assert "recommend" in persona, "Missing recommend"
            assert "reason" in persona, "Missing reason"

    @patch.dict(os.environ, {"CREWAI_MOCK_MODE": "true"})
    def test_full_pipeline_with_helpers_disabled(self, sample_job_posting, sample_options_without_helpers):
        """Test complete pipeline with helpers disabled."""
        correlation_id = str(uuid.uuid4())
        
        # Execute pipeline without helpers
        result = run_crew(
            job_posting_data=sample_job_posting,
            options=sample_options_without_helpers,
            correlation_id=correlation_id
        )
        
        # Should still work without helpers
        assert "final" in result, "Missing final decision"
        assert "personas" in result, "Missing personas"
        
        # Final decision should be present
        final = result["final"]
        assert isinstance(final["recommend"], bool), "Recommend should be boolean"
        assert isinstance(final["rationale"], str), "Rationale should be string"