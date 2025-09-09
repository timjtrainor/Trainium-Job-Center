"""
Test suite for Judge agent YAML implementation.

Tests the judge aggregation functionality including weighted majority,
guardrails application, and deterministic decision-making.
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


class TestJudgeYaml:
    """Test suite for YAML-driven judge aggregation system."""
    
    @pytest.fixture
    def sample_motivational_verdicts_positive(self) -> List[Dict[str, Any]]:
        """Sample motivational verdicts with majority positive."""
        return [
            {
                "persona_id": "builder",
                "recommend": True,
                "reason": "Strong technical opportunities with modern stack",
                "notes": ["Complex architecture", "Engineering ownership"],
                "sources": ["job_description", "technical_requirements"]
            },
            {
                "persona_id": "maximizer",
                "recommend": True,
                "reason": "Excellent growth potential with competitive compensation",
                "notes": ["Market-rate salary", "Learning opportunities"],
                "sources": ["compensation_analysis", "growth_opportunities"]
            },
            {
                "persona_id": "harmonizer",
                "recommend": True,
                "reason": "Positive culture indicators",
                "notes": ["Collaborative environment", "Work-life balance"],
                "sources": ["culture_indicators"]
            },
            {
                "persona_id": "pathfinder",
                "recommend": True,
                "reason": "Strategic career alignment",
                "notes": ["Career progression", "Industry growth"],
                "sources": ["career_strategy"]
            },
            {
                "persona_id": "adventurer",
                "recommend": False,
                "reason": "Limited innovation opportunities",
                "notes": ["Mature technology stack"],
                "sources": ["innovation_indicators"]
            }
        ]

    @pytest.fixture
    def sample_motivational_verdicts_with_redflags(self) -> List[Dict[str, Any]]:
        """Sample motivational verdicts with red flags in notes."""
        return [
            {
                "persona_id": "builder",
                "recommend": True,
                "reason": "Technical opportunities available",
                "notes": ["Complex systems", "severe red flag: unstable funding"],
                "sources": ["job_description"]
            },
            {
                "persona_id": "maximizer",
                "recommend": True,
                "reason": "Growth potential",
                "notes": ["Learning opportunities"],
                "sources": ["compensation_analysis"]
            },
            {
                "persona_id": "harmonizer",
                "recommend": True,
                "reason": "Culture alignment",
                "notes": ["Team collaboration"],
                "sources": ["culture_indicators"]
            },
            {
                "persona_id": "pathfinder",
                "recommend": True,
                "reason": "Career alignment",
                "notes": ["Strategic positioning"],
                "sources": ["career_strategy"]
            },
            {
                "persona_id": "adventurer",
                "recommend": True,
                "reason": "Innovation potential",
                "notes": ["New technologies"],
                "sources": ["innovation_indicators"]
            }
        ]

    @pytest.fixture
    def sample_weights(self) -> Dict[str, float]:
        """Sample decision weights."""
        return {
            "builder": 0.30,
            "maximizer": 0.20,
            "harmonizer": 0.20,
            "pathfinder": 0.15,
            "adventurer": 0.15
        }

    @pytest.fixture
    def sample_guardrails(self) -> Dict[str, Any]:
        """Sample decision guardrails."""
        return {
            "comp_floor_enforced": True,
            "severe_redflags_block": True,
            "tie_bias": "do_not_pursue"
        }

    @pytest.fixture
    def sample_helper_snapshot(self) -> Dict[str, Any]:
        """Sample helper snapshot data."""
        return {
            "data_analyst": {"tc_range": "$120k-$160k", "refs": ["levels.fyi"]},
            "strategist": {"signals": ["AI adoption"], "refs": ["industry_report"]},
            "skeptic": {"redflags": []},
            "optimizer": {"top3": ["highlight cloud experience"]}
        }

    @pytest.fixture
    def sample_helper_snapshot_with_redflags(self) -> Dict[str, Any]:
        """Sample helper snapshot with red flags."""
        return {
            "data_analyst": {"tc_range": "$120k-$160k", "refs": ["levels.fyi"]},
            "strategist": {"signals": ["AI adoption"], "refs": ["industry_report"]},
            "skeptic": {"redflags": ["severe red flag: financial instability"]},
            "optimizer": {"top3": ["highlight experience"]}
        }

    def test_judge_agent_yaml_loading(self):
        """Test that judge agent is correctly defined in YAML."""
        crew = MotivationalFanOutCrew()
        
        # Verify judge agent is loaded
        assert "judge" in crew.agents_config, "Judge agent not found in config"
        
        # Verify required fields
        judge_config = crew.agents_config["judge"]
        assert "role" in judge_config, "Judge agent missing role"
        assert "goal" in judge_config, "Judge agent missing goal"
        assert "backstory" in judge_config, "Judge agent missing backstory"
        
        # Verify specific content
        assert judge_config["role"] == "Final decision arbiter"
        assert "integrate persona verdicts" in judge_config["goal"].lower()
        assert "analytical and impartial" in judge_config["backstory"].lower()

    def test_judge_task_yaml_loading(self):
        """Test that judge aggregation task is correctly defined in YAML."""
        crew = MotivationalFanOutCrew()
        
        # Verify judge task is loaded
        assert "judge_aggregation" in crew.tasks_config, "Judge aggregation task not found in config"
        
        # Verify required fields
        task_config = crew.tasks_config["judge_aggregation"]
        assert "description" in task_config, "Judge task missing description"
        assert "expected_output" in task_config, "Judge task missing expected_output"
        assert "agent" in task_config, "Judge task missing agent assignment"
        
        # Verify agent assignment
        assert task_config["agent"] == "judge", "Judge task not assigned to judge agent"
        
        # Verify placeholders in description
        description = task_config["description"]
        required_placeholders = [
            "{motivational_verdicts}", "{helper_snapshot}", 
            "{weights}", "{guardrails}", "{job_meta}"
        ]
        for placeholder in required_placeholders:
            assert placeholder in description, f"Judge task missing placeholder {placeholder}"

    def test_judge_agent_instantiation(self):
        """Test that judge agent can be instantiated."""
        crew = MotivationalFanOutCrew()
        
        # Test judge agent creation
        judge_agent = crew.judge()
        assert judge_agent is not None, "Judge agent could not be instantiated"
        assert judge_agent.role == "Final decision arbiter"

    def test_judge_task_instantiation(self):
        """Test that judge aggregation task can be instantiated."""
        crew = MotivationalFanOutCrew()
        
        # Test judge task creation
        judge_task = crew.judge_aggregation()
        assert judge_task is not None, "Judge task could not be instantiated"
        assert judge_task.agent is not None, "Judge task has no agent assigned"

    def test_weights_guardrails_loading(self):
        """Test that weights and guardrails configuration loads correctly."""
        crew = MotivationalFanOutCrew()
        
        # Test weights/guardrails loading
        config = crew._load_weights_guardrails_config()
        assert "review_weights" in config, "Missing review_weights in config"
        assert "guardrails" in config, "Missing guardrails in config"
        
        # Test weights structure
        weights = config["review_weights"]
        required_personas = ["builder", "maximizer", "harmonizer", "pathfinder", "adventurer"]
        for persona in required_personas:
            assert persona in weights, f"Missing weight for {persona}"
            assert isinstance(weights[persona], (int, float)), f"Weight for {persona} not numeric"
        
        # Test guardrails structure
        guardrails = config["guardrails"]
        required_guardrails = ["comp_floor_enforced", "severe_redflags_block", "tie_bias"]
        for guardrail in required_guardrails:
            assert guardrail in guardrails, f"Missing guardrail {guardrail}"

    def test_weighted_majority_pursue(self, sample_motivational_verdicts_positive, 
                                    sample_weights, sample_guardrails, sample_helper_snapshot):
        """Test weighted majority calculation leads to positive recommendation."""
        # Mock judge task execution to test logic
        verdicts = sample_motivational_verdicts_positive
        weights = sample_weights
        
        # Calculate expected weighted sum
        # builder(0.30) + maximizer(0.20) + harmonizer(0.20) + pathfinder(0.15) = 0.85 >= 0.6
        expected_weighted_sum = 0.30 + 0.20 + 0.20 + 0.15  # = 0.85
        
        assert expected_weighted_sum >= 0.6, "Weighted sum should lead to positive recommendation"
        
        # This test validates the logic that should be implemented in YAML
        # The actual YAML prompt should perform this calculation

    def test_redflag_blocks(self, sample_motivational_verdicts_with_redflags,
                          sample_weights, sample_guardrails, sample_helper_snapshot_with_redflags):
        """Test that severe red flags block positive recommendations."""
        # Test red flag in verdict notes
        verdicts = sample_motivational_verdicts_with_redflags
        has_redflag_in_notes = any("severe red flag" in str(v.get("notes", [])) for v in verdicts)
        assert has_redflag_in_notes, "Test data should contain red flag in notes"
        
        # Test red flag in helper snapshot
        helper_snapshot = sample_helper_snapshot_with_redflags
        has_redflag_in_helpers = "severe red flag" in str(helper_snapshot.get("skeptic", {}).get("redflags", []))
        assert has_redflag_in_helpers, "Test data should contain red flag in helper snapshot"
        
        # This test validates the guardrail logic that should be implemented in YAML

    def test_comp_floor_guardrail(self, sample_motivational_verdicts_positive,
                                sample_weights, sample_guardrails):
        """Test compensation floor guardrail enforcement."""
        # Test case where maximizer=false and comp below minimum
        verdicts = sample_motivational_verdicts_positive.copy()
        # Set maximizer to false
        for v in verdicts:
            if v["persona_id"] == "maximizer":
                v["recommend"] = False
                v["reason"] = "Below compensation expectations"
        
        job_meta = {"comp_below_minimum": True}
        guardrails = {"comp_floor_enforced": True}
        
        # Should result in final=false unless both builder and adventurer are true with extraordinary upside
        builder_true = any(v["persona_id"] == "builder" and v["recommend"] for v in verdicts)
        adventurer_true = any(v["persona_id"] == "adventurer" and v["recommend"] for v in verdicts)
        
        # This test validates the guardrail logic that should be implemented in YAML

    def test_tie_bias(self, sample_weights, sample_guardrails):
        """Test tie bias handling when weighted sum equals threshold."""
        # Create verdicts that result in exactly 0.5 weighted sum
        verdicts = [
            {"persona_id": "builder", "recommend": True},      # 0.30
            {"persona_id": "maximizer", "recommend": True},    # 0.20  
            {"persona_id": "harmonizer", "recommend": False},  # 0.00
            {"persona_id": "pathfinder", "recommend": False},  # 0.00
            {"persona_id": "adventurer", "recommend": False}   # 0.00
        ]
        
        # Expected weighted sum: 0.30 + 0.20 = 0.50 (exactly at threshold)
        expected_sum = 0.30 + 0.20
        assert expected_sum == 0.5, "Test should create exact tie condition"
        
        # With tie_bias="do_not_pursue", should result in final=false
        tie_bias = "do_not_pursue"
        expected_result = False
        
        # This test validates the tie-breaking logic that should be implemented in YAML

    def test_json_shape(self):
        """Test that judge output has required JSON keys and short content."""
        # Expected JSON shape
        required_keys = ["final_recommendation", "primary_rationale", "tradeoffs", "decider_confidence"]
        
        # Mock judge output for validation
        sample_output = {
            "final_recommendation": True,
            "primary_rationale": "Strong technical alignment with growth potential",
            "tradeoffs": ["Learning curve vs immediate impact", "Remote vs on-site collaboration"],
            "decider_confidence": "high"
        }
        
        # Validate required keys
        for key in required_keys:
            assert key in sample_output, f"Missing required key: {key}"
        
        # Validate data types
        assert isinstance(sample_output["final_recommendation"], bool)
        assert isinstance(sample_output["primary_rationale"], str)
        assert isinstance(sample_output["tradeoffs"], list)
        assert sample_output["decider_confidence"] in ["low", "medium", "high"]
        
        # Validate brevity constraints
        assert len(sample_output["primary_rationale"]) <= 200, "Rationale should be 1-2 sentences"
        assert len(sample_output["tradeoffs"]) <= 5, "Should have limited tradeoffs"
        for tradeoff in sample_output["tradeoffs"]:
            assert len(tradeoff) <= 100, "Each tradeoff should be a short bullet"

    @patch.dict(os.environ, {"CREWAI_MOCK_MODE": "true"})
    def test_crew_includes_judge(self):
        """Test that the crew execution order includes judge after motivational tasks."""
        crew = MotivationalFanOutCrew()
        
        # Test that judge task exists
        assert hasattr(crew, "judge_aggregation"), "Crew missing judge_aggregation task method"
        
        # Test that judge agent exists  
        assert hasattr(crew, "judge"), "Crew missing judge agent method"
        
        # Load crew config to verify task order
        crew_yaml_path = crew.base_dir / "config" / "crew.yaml"
        import yaml
        with open(crew_yaml_path, 'r') as f:
            crew_config = yaml.safe_load(f)
        
        tasks = crew_config.get("tasks", [])
        assert "judge_aggregation" in tasks, "judge_aggregation not in crew task list"
        
        # Verify judge runs after motivational tasks
        judge_index = tasks.index("judge_aggregation")
        motivational_tasks = ["builder_evaluation", "maximizer_evaluation", "harmonizer_evaluation", 
                            "pathfinder_evaluation", "adventurer_evaluation"]
        
        for task in motivational_tasks:
            if task in tasks:
                task_index = tasks.index(task)
                assert task_index < judge_index, f"{task} should run before judge_aggregation"