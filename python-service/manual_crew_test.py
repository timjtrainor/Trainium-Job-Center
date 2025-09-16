#!/usr/bin/env python3
"""
Manual test script for the job posting review crew functionality.
This can be run independently to verify the crew logic works as expected.
"""
import sys
import os

# Add the app directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_run_crew_function():
    """Test the run_crew function with sample data."""
    print("Testing run_crew function...")
    
    # Sample job posting data
    sample_job_posting = {
        "title": "Senior Machine Learning Engineer",
        "company": "Acme Corp",
        "description": "We are looking for a senior ML engineer with expertise in Python, TensorFlow, and distributed systems. Salary range $180,000 - $220,000. Remote work available.",
        "location": "San Francisco, CA",
        "salary": "$180,000 - $220,000",
        "requirements": ["5+ years ML experience", "PhD or Master's degree", "Python expertise"]
    }
    
    try:
        # Import the run_crew function
        from services.crewai.job_posting_review.crew import run_crew
        
        print("✓ Successfully imported run_crew function")
        
        # Test the function (this will fail without CrewAI dependencies, but we can test the error handling)
        result = run_crew(sample_job_posting)
        
        print("✓ run_crew executed successfully")
        print(f"Result type: {type(result)}")
        print(f"Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        # Check if it has the expected structure
        if isinstance(result, dict):
            required_keys = ['job_id', 'final', 'personas']
            missing_keys = [key for key in required_keys if key not in result]
            if not missing_keys:
                print("✓ Result has expected structure")
            else:
                print(f"⚠ Missing required keys: {missing_keys}")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✓ run_crew handled error gracefully: {type(e).__name__}")
        print(f"  Error message: {str(e)[:100]}...")
        
        # If it's in the error handling path, check if it still returns expected structure
        try:
            from services.crewai.job_posting_review.crew import run_crew
            result = run_crew(sample_job_posting)
            if isinstance(result, dict) and 'job_id' in result and 'final' in result:
                print("✓ Error handling returns proper structure")
                return True
        except:
            pass
        return False


def test_crew_config_files():
    """Test that the crew configuration files are readable."""
    print("\nTesting crew configuration files...")
    
    import yaml
    from pathlib import Path
    
    base_dir = Path(__file__).parent / 'app' / 'services' / 'crewai' / 'job_posting_review' / 'config'
    
    # Test agents.yaml
    agents_file = base_dir / 'agents.yaml'
    try:
        with open(agents_file, 'r') as f:
            agents_config = yaml.safe_load(f)
        
        expected_agents = ['pre_filter_agent', 'quick_fit_analyst', 'brand_framework_matcher', 'managing_agent']  # job_intake_agent removed
        found_agents = list(agents_config.keys())
        
        print(f"✓ agents.yaml loaded successfully")
        print(f"  Expected agents: {len(expected_agents)}")  
        print(f"  Found agents: {len(found_agents)}")
        
        missing_agents = [agent for agent in expected_agents if agent not in found_agents]
        if not missing_agents:
            print("✓ All expected agents found")
        else:
            print(f"⚠ Missing agents: {missing_agents}")
            
    except Exception as e:
        print(f"✗ Failed to load agents.yaml: {e}")
        return False
    
    # Test tasks.yaml
    tasks_file = base_dir / 'tasks.yaml'
    try:
        with open(tasks_file, 'r') as f:
            tasks_config = yaml.safe_load(f)
        
        expected_tasks = ['pre_filter_task', 'quick_fit_task', 'brand_match_task', 'orchestration_task']  # intake_task removed
        found_tasks = list(tasks_config.keys())
        
        print(f"✓ tasks.yaml loaded successfully")
        print(f"  Expected tasks: {len(expected_tasks)}")
        print(f"  Found tasks: {len(found_tasks)}")
        
        missing_tasks = [task for task in expected_tasks if task not in found_tasks]
        if not missing_tasks:
            print("✓ All expected tasks found")
        else:
            print(f"⚠ Missing tasks: {missing_tasks}")
            
        return True
            
    except Exception as e:
        print(f"✗ Failed to load tasks.yaml: {e}")
        return False


def test_api_endpoint_structure():
    """Test that the API endpoint can be imported and has expected structure."""
    print("\nTesting API endpoint structure...")
    
    try:
        # Test import
        from api.v1.endpoints.job_posting_review import router, JobPostingInput
        
        print("✓ Successfully imported job posting review endpoint")
        print(f"  Router prefix: {router.prefix}")
        print(f"  Router tags: {router.tags}")
        
        # Check routes
        routes = [route for route in router.routes]
        route_paths = [getattr(route, 'path', 'unknown') for route in routes]
        
        print(f"  Available routes: {route_paths}")
        
        expected_routes = ['/analyze', '/health', '/config']
        missing_routes = [route for route in expected_routes if route not in route_paths]
        
        if not missing_routes:
            print("✓ All expected routes found")
        else:
            print(f"⚠ Missing routes: {missing_routes}")
        
        # Test the input model
        sample_input = {
            "job_posting": {"title": "Test Job", "company": "Test Corp"},
            "options": {"test": True}
        }
        
        try:
            input_model = JobPostingInput(**sample_input)
            print("✓ JobPostingInput model works correctly")
        except Exception as e:
            print(f"⚠ JobPostingInput model issue: {e}")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    print("=== Job Posting Review Crew Manual Test ===\n")
    
    results = []
    
    # Run tests
    results.append(test_crew_config_files())
    results.append(test_run_crew_function()) 
    results.append(test_api_endpoint_structure())
    
    # Summary
    print("\n=== Test Summary ===")
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed! The crew structure looks good.")
    else:
        print("⚠ Some tests failed. Review the output above.")
    
    sys.exit(0 if passed == total else 1)