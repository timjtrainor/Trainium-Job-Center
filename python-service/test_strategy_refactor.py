import httpx
import asyncio
import json

BASE_URL = "http://localhost:8180/api/interview-strategy"

async def test_application_strategy():
    print("Testing /application-strategy...")
    payload = {
        "job_description": "We are looking for a Senior Software Engineer to help us build a scalable AI platform. You should have experience with Python, FastAPI, and React.",
        "company_data": {
            "company_name": "TestAI Corp",
            "mission": {"text": "To democratize AI.", "source": "website"}
        },
        "career_dna": {
            "positioning_statement": "Expert engineer with a passion for AI scaling.",
            "master_career_dna": {
                "mission": "Build better tools.",
                "stories": []
            }
        },
        "vocabulary_mirror": ["scalable", "AI platform", "FastAPI"]
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{BASE_URL}/application-strategy", json=payload, timeout=60.0)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print("Success! Result preview:")
                print(json.dumps(response.json(), indent=2)[:500] + "...")
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"Exception: {e}")

async def test_blueprint():
    print("\nTesting /blueprint...")
    payload = {
        "job_description": "Senior Software Engineer role.",
        "company_data": {"company_name": "TestAI Corp"},
        "career_dna": {"positioning_statement": "Expert engineer."},
        "job_problem_analysis": {
            "diagnostic_intel": {
                "failure_state_portfolio": "Inefficient scaling",
                "composite_antidote_persona": "The Scalability Architect",
                "experience_anchoring": "Built 10x platforms",
                "mandate_quadrant": "Improve",
                "functional_gravity_stack": ["Backend", "Infra"],
                "strategic_friction_hooks": ["Lack of modularity"]
            }
        },
        "interviewer_profiles": [
            {"name": "John Doe", "role": "Hiring Manager", "persona_type": "The Owner"}
        ]
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{BASE_URL}/blueprint", json=payload, timeout=60.0)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print("Success! Result preview:")
                print(json.dumps(response.json(), indent=2)[:500] + "...")
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_application_strategy())
    asyncio.run(test_blueprint())
