#!/usr/bin/env python3
"""
Basic validation script for judge agent implementation.
Tests that configuration files load properly and basic structure is correct.
"""

import sys
from pathlib import Path

# Add the python-service directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "python-service"))

def test_yaml_configs():
    """Test that YAML configuration files are valid."""
    import yaml
    
    base_dir = Path(__file__).parent / "python-service" / "app" / "services" / "crewai" / "job_posting_review" / "config"
    
    # Test agents.yaml
    agents_file = base_dir / "agents.yaml"
    with open(agents_file, 'r') as f:
        agents_config = yaml.safe_load(f)
    
    print(f"✅ agents.yaml: Valid YAML with {len(agents_config)} agents")
    assert "judge" in agents_config, "Judge agent not found"
    
    judge_config = agents_config["judge"]
    assert judge_config["role"] == "Final decision arbiter", "Judge role incorrect"
    print("✅ Judge agent configuration valid")
    
    # Test tasks.yaml  
    tasks_file = base_dir / "tasks.yaml"
    with open(tasks_file, 'r') as f:
        tasks_config = yaml.safe_load(f)
    
    print(f"✅ tasks.yaml: Valid YAML with {len(tasks_config)} tasks")
    assert "judge_aggregation" in tasks_config, "Judge aggregation task not found"
    
    judge_task = tasks_config["judge_aggregation"]
    assert "motivational_verdicts" in judge_task["description"], "Judge task missing verdicts input"
    assert "weights" in judge_task["description"], "Judge task missing weights input"
    assert "guardrails" in judge_task["description"], "Judge task missing guardrails input"
    print("✅ Judge task configuration valid")
    
    # Test crew.yaml
    crew_file = base_dir / "crew.yaml"
    with open(crew_file, 'r') as f:
        crew_config = yaml.safe_load(f)
    
    tasks = crew_config.get("tasks", [])
    assert "judge_aggregation" in tasks, "Judge aggregation not in crew task list"
    
    # Verify judge runs after motivational tasks
    judge_index = tasks.index("judge_aggregation")
    motivational_tasks = ["builder_evaluation", "maximizer_evaluation", "harmonizer_evaluation", 
                         "pathfinder_evaluation", "adventurer_evaluation"]
    
    for task in motivational_tasks:
        if task in tasks:
            task_index = tasks.index(task)
            assert task_index < judge_index, f"{task} should run before judge_aggregation"
    
    print("✅ Crew configuration valid - judge runs after motivational tasks")

def test_weights_guardrails_config():
    """Test that weights and guardrails configuration is valid."""
    import yaml
    
    config_file = Path(__file__).parent / "config" / "weights_guardrails.yml"
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    assert "review_weights" in config, "Missing review_weights in config"
    assert "guardrails" in config, "Missing guardrails in config"
    
    # Test weights structure
    weights = config["review_weights"]
    required_personas = ["builder", "maximizer", "harmonizer", "pathfinder", "adventurer"]
    for persona in required_personas:
        assert persona in weights, f"Missing weight for {persona}"
        assert isinstance(weights[persona], (int, float)), f"Weight for {persona} not numeric"
    
    # Verify weights sum to approximately 1.0
    total_weight = sum(weights.values())
    assert 0.9 <= total_weight <= 1.1, f"Weights should sum to ~1.0, got {total_weight}"
    
    # Test guardrails structure
    guardrails = config["guardrails"]
    required_guardrails = ["comp_floor_enforced", "severe_redflags_block", "tie_bias"]
    for guardrail in required_guardrails:
        assert guardrail in guardrails, f"Missing guardrail {guardrail}"
    
    print("✅ Weights and guardrails configuration valid")

def test_python_imports():
    """Test that Python modules can be imported (basic syntax check)."""
    try:
        # Test basic imports without full initialization
        print("Testing Python imports...")
        
        # This will test the basic syntax without requiring all dependencies
        with open("python-service/app/services/crewai/job_posting_review/crew.py", 'r') as f:
            content = f.read()
        
        # Basic syntax check
        compile(content, "crew.py", "exec")
        print("✅ crew.py syntax valid")
        
        # Check that all required methods are present
        assert "def judge(" in content, "Missing judge agent method"
        assert "def judge_aggregation(" in content, "Missing judge task method"
        assert "_load_weights_guardrails_config" in content, "Missing weights config loader"
        
        print("✅ Required judge methods present in crew.py")
        
    except Exception as e:
        print(f"❌ Python import/syntax error: {e}")
        return False
    
    return True

def main():
    """Run all validation tests."""
    print("🔍 Validating Judge Agent Implementation...")
    print()
    
    try:
        test_yaml_configs()
        print()
        
        test_weights_guardrails_config()
        print()
        
        if test_python_imports():
            print()
            print("🎉 All validation tests passed!")
            print()
            print("Judge agent implementation appears to be correctly configured:")
            print("- ✅ Judge agent defined in agents.yaml")
            print("- ✅ Judge aggregation task defined in tasks.yaml") 
            print("- ✅ Crew execution order includes judge after motivational tasks")
            print("- ✅ Weights and guardrails configuration valid")
            print("- ✅ Python code structure appears correct")
            print()
            print("Next steps: Run full integration tests with dependencies installed")
            return True
        else:
            print("❌ Validation failed")
            return False
            
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)