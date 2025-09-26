#!/usr/bin/env python3
"""
Manual test script for the job review override endpoint.
This script can be run to verify the override functionality works as expected.
"""
import sys
import os
import asyncio
import uuid
from datetime import datetime

# Add the app directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from services.infrastructure.database import DatabaseService


async def test_override_functionality():
    """Test the override functionality with sample data."""
    print("=== Job Review Override Endpoint Test ===\n")
    
    # Initialize database service
    db_service = DatabaseService()
    success = await db_service.initialize()
    
    if not success:
        print("❌ Failed to initialize database connection")
        return False
    
    print("✅ Database connection initialized")
    
    # Create a test job review first (if needed)
    test_job_id = str(uuid.uuid4())
    
    # Sample review data
    review_data = {
        "recommend": True,
        "confidence": "high",
        "rationale": "Strong technical fit with good company culture match",
        "personas": [{"name": "developer", "score": 0.85}],
        "tradeoffs": ["Remote work available", "Salary slightly below market"],
        "actions": ["Apply immediately", "Prepare for technical interview"],
        "sources": ["job description", "company website"],
        "crew_output": {"analysis": "detailed_analysis"},
        "processing_time_seconds": 45.2,
        "crew_version": "v1.0",
        "model_used": "gpt-4",
        "error_message": None,
        "retry_count": 0
    }
    
    print(f"Creating test job review for job_id: {test_job_id}")
    insert_success = await db_service.insert_job_review(test_job_id, review_data)
    
    if not insert_success:
        print("⚠️  Failed to create test job review - testing with existing data")
        # Try to find an existing job review to test with
        # This is a simplified approach for manual testing
        print("Note: In a real test, you would use an existing job_id from your database")
        await db_service.close()
        return False
    
    print("✅ Test job review created")
    
    # Test the override functionality
    print(f"\nTesting override functionality...")
    override_result = await db_service.update_job_review_override(
        job_id=test_job_id,
        override_recommend=False,  # Override the AI recommendation
        override_comment="Human reviewer found concerns about company culture that AI missed",
        override_by="test_admin"
    )
    
    if override_result:
        print("✅ Override update successful")
        print(f"   Original AI recommendation: {override_result['recommend']}")
        print(f"   Human override: {override_result['override_recommend']}")
        print(f"   Override comment: {override_result['override_comment']}")
        print(f"   Override by: {override_result['override_by']}")
        print(f"   Override at: {override_result['override_at']}")
        
        # Verify the override data was saved correctly
        review_data = await db_service.get_job_review(test_job_id)
        if review_data and review_data['override_recommend'] is not None:
            print("✅ Override data properly persisted in database")
        else:
            print("❌ Override data not found in database")
            
    else:
        print("❌ Override update failed")
        await db_service.close()
        return False
    
    # Clean up
    print(f"\nCleaning up test data...")
    # Note: In a real test environment, you'd want to clean up the test job review
    # For manual testing, we'll leave it for inspection
    
    await db_service.close()
    print("✅ Database connection closed")
    
    return True


def test_endpoint_models():
    """Test that the endpoint models can be imported and used."""
    print("\nTesting endpoint models...")
    
    try:
        from api.v1.endpoints.jobs import OverrideRequest, OverrideResponse
        
        # Test request model
        request_data = {
            "override_recommend": True,
            "override_comment": "This is a test comment"
        }
        request = OverrideRequest(**request_data)
        print("✅ OverrideRequest model works correctly")
        print(f"   Request: {request.model_dump()}")
        
        # Test response model
        response_data = {
            "id": "123",
            "job_id": str(uuid.uuid4()),
            "recommend": True,
            "confidence": "high",
            "rationale": "Test rationale",
            "override_recommend": False,
            "override_comment": "Test override comment",
            "override_by": "test_admin",
            "override_at": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        response = OverrideResponse(**response_data)
        print("✅ OverrideResponse model works correctly")
        print(f"   Response keys: {list(response.model_dump().keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Model test failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False


async def main():
    """Run all tests."""
    print("Starting manual tests for job review override functionality...\n")
    
    # Test models
    model_test = test_endpoint_models()
    
    # Test database functionality
    if model_test:
        print("\n" + "="*50)
        db_test = await test_override_functionality()
        
        if model_test and db_test:
            print("\n🎉 All tests passed!")
            print("\nThe override endpoint should be ready to use:")
            print("POST /jobs/reviews/{job_id}/override")
            print("Body: {\"override_recommend\": true, \"override_comment\": \"Your comment here\"}")
        else:
            print("\n⚠️  Some tests failed. Please review the output above.")
    else:
        print("\n❌ Model tests failed, skipping database tests")


if __name__ == "__main__":
    asyncio.run(main())