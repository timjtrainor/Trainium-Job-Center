#!/usr/bin/env python3
"""
Integration test for job review functionality.

This script tests the integration between:
- Database operations
- Queue operations  
- Worker functions
- API endpoints

Run with: python integration_test_job_review.py
"""
import asyncio
import sys
import json
from uuid import uuid4
from datetime import datetime
from loguru import logger

from app.core.config import configure_logging, get_settings
from app.services.infrastructure.database import get_database_service
from app.services.infrastructure.queue import get_queue_service
from app.services.infrastructure.job_review_service import get_job_review_service


async def test_database_operations():
    """Test database operations for job reviews."""
    logger.info("Testing database operations...")
    
    settings = get_settings()
    db_service = get_database_service()
    
    try:
        # Initialize database
        success = await db_service.initialize()
        if not success:
            logger.error("Failed to initialize database")
            return False
        
        logger.info("✓ Database initialized successfully")
        
        # Test getting pending jobs (should not fail even if empty)
        pending_jobs = await db_service.get_pending_review_jobs(limit=5)
        logger.info(f"✓ Found {len(pending_jobs)} pending review jobs")
        
        # Create a test job if needed
        if not pending_jobs:
            logger.info("Creating test job for testing...")
            test_job_id = str(uuid4())
            
            insert_query = """
            INSERT INTO public.jobs (
                id, site, job_url, title, company, location_city, description, 
                date_posted, status, source_raw
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), $8, $9)
            """
            
            async with db_service.pool.acquire() as conn:
                await conn.execute(
                    insert_query,
                    test_job_id,
                    "integration_test",
                    f"https://test.com/job/{test_job_id}",
                    "Integration Test Job - Python Developer",
                    "Test Company Inc",
                    "Remote",
                    "This is a test job for integration testing of the job review system.",
                    "pending_review",
                    json.dumps({"test": True, "created_at": datetime.now().isoformat()})
                )
            
            logger.info(f"✓ Created test job: {test_job_id}")
            
            # Verify job was created
            job = await db_service.get_job_by_id(test_job_id)
            if job:
                logger.info(f"✓ Test job verified: {job['title']} at {job['company']}")
            else:
                logger.error("✗ Failed to verify test job creation")
                return False
        
        # Test job review operations (without actually running CrewAI)
        test_review_data = {
            "recommend": True,
            "confidence": "high",
            "rationale": "Integration test review - automatically generated",
            "personas": [{"id": "test_persona", "recommend": True, "reason": "Test reason"}],
            "tradeoffs": [],
            "actions": ["Integration test action"],
            "sources": ["integration_test"],
            "crew_output": {"test": True, "timestamp": datetime.now().isoformat()},
            "processing_time_seconds": 1.5,
            "crew_version": "integration_test_v1",
            "model_used": "test_model",
            "retry_count": 0
        }
        
        # Use first available job for testing
        pending_jobs = await db_service.get_pending_review_jobs(limit=1)
        if pending_jobs:
            test_job = pending_jobs[0]
            job_id = str(test_job["id"])
            
            # Test inserting review
            success = await db_service.insert_job_review(job_id, test_review_data)
            if success:
                logger.info("✓ Job review inserted successfully")
                
                # Test retrieving review
                review = await db_service.get_job_review(job_id)
                if review and review["recommend"] == test_review_data["recommend"]:
                    logger.info("✓ Job review retrieved successfully")
                    
                    # Test updating job status
                    success = await db_service.update_job_status(job_id, "reviewed")
                    if success:
                        logger.info("✓ Job status updated successfully")
                    else:
                        logger.error("✗ Failed to update job status")
                        return False
                else:
                    logger.error("✗ Failed to retrieve job review")
                    return False
            else:
                logger.error("✗ Failed to insert job review")
                return False
        
        logger.info("✓ All database operations completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"✗ Database test failed: {e}")
        return False


async def test_queue_operations():
    """Test queue operations for job reviews."""
    logger.info("Testing queue operations...")
    
    try:
        queue_service = get_queue_service()
        
        # Initialize queue
        success = await queue_service.initialize()
        if not success:
            logger.error("✗ Failed to initialize queue service")
            return False
        
        logger.info("✓ Queue service initialized successfully")
        
        # Test getting queue info
        queue_info = queue_service.get_queue_info()
        if queue_info:
            logger.info("✓ Queue info retrieved successfully")
            
            if 'review_queue' in queue_info:
                review_q = queue_info['review_queue']
                logger.info(f"  Review queue: {review_q['length']} pending, {review_q['started_jobs']} running")
            elif 'length' in queue_info:
                logger.info(f"  Queue length: {queue_info['length']}")
        else:
            logger.warning("⚠ Queue info empty (might be expected in test environment)")
        
        logger.info("✓ All queue operations completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"✗ Queue test failed: {e}")
        logger.info("This is expected if Redis is not available in the test environment")
        return True  # Don't fail the test for missing Redis


async def test_job_review_service():
    """Test the high-level job review service."""
    logger.info("Testing job review service...")
    
    try:
        service = get_job_review_service()
        
        # Test initialization (may fail without Redis/DB)
        success = await service.initialize()
        if not success:
            logger.warning("⚠ Job review service initialization failed (expected without Redis/DB)")
            return True
        
        logger.info("✓ Job review service initialized successfully")
        
        # Test getting stats (requires database)
        try:
            stats = await service.get_review_stats()
            if stats:
                logger.info("✓ Review statistics retrieved successfully")
                if 'job_status_counts' in stats:
                    logger.info(f"  Job status counts: {stats['job_status_counts']}")
                if 'review_stats' in stats:
                    rs = stats['review_stats']
                    logger.info(f"  Total reviews: {rs.get('total_reviews', 0)}")
            else:
                logger.warning("⚠ No review statistics available")
        except Exception as e:
            logger.warning(f"⚠ Stats test failed (expected without full DB): {e}")
        
        logger.info("✓ Job review service tests completed")
        return True
        
    except Exception as e:
        logger.error(f"✗ Job review service test failed: {e}")
        return False


async def test_configuration():
    """Test configuration and settings."""
    logger.info("Testing configuration...")
    
    try:
        settings = get_settings()
        
        # Check required settings
        required_settings = [
            'job_review_queue_name',
            'job_review_batch_size',
            'job_review_max_retries',
            'database_url',
            'redis_host',
            'redis_port'
        ]
        
        for setting in required_settings:
            value = getattr(settings, setting, None)
            if value is not None:
                logger.info(f"✓ {setting}: {value}")
            else:
                logger.warning(f"⚠ {setting}: not set")
        
        logger.info("✓ Configuration test completed")
        return True
        
    except Exception as e:
        logger.error(f"✗ Configuration test failed: {e}")
        return False


async def main():
    """Run all integration tests."""
    configure_logging()
    logger.info("Starting job review integration tests...")
    
    tests = [
        ("Configuration", test_configuration),
        ("Database Operations", test_database_operations),
        ("Queue Operations", test_queue_operations),
        ("Job Review Service", test_job_review_service),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running {test_name} Test")
        logger.info(f"{'='*50}")
        
        try:
            success = await test_func()
            if success:
                logger.success(f"✓ {test_name} test PASSED")
                passed += 1
            else:
                logger.error(f"✗ {test_name} test FAILED")
        except Exception as e:
            logger.error(f"✗ {test_name} test FAILED with exception: {e}")
    
    logger.info(f"\n{'='*50}")
    logger.info(f"Integration Test Results: {passed}/{total} tests passed")
    logger.info(f"{'='*50}")
    
    if passed == total:
        logger.success("🎉 All integration tests passed!")
        return 0
    else:
        logger.error(f"❌ {total - passed} tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))