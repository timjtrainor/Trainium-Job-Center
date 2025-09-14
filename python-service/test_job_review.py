#!/usr/bin/env python3
"""
Test script for job review functionality.

This script tests the job review worker without requiring a full Redis setup.
"""
import asyncio
import sys
import json
from uuid import uuid4
from loguru import logger

from app.core.config import configure_logging
from app.services.infrastructure.database import get_database_service
from app.services.infrastructure.worker import process_job_review


async def create_test_job():
    """Create a test job in the database."""
    configure_logging()
    
    db_service = get_database_service()
    await db_service.initialize()
    
    # Create a sample job
    test_job_id = str(uuid4())
    
    insert_query = """
    INSERT INTO public.jobs (
        id, site, job_url, title, company, location_city, description, 
        date_posted, status, source_raw
    ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), $8, $9)
    """
    
    test_data = {
        "id": test_job_id,
        "site": "test_site",
        "job_url": f"https://example.com/job/{test_job_id}",
        "title": "Senior Python Developer - AI/ML Focus",
        "company": "TechCorp AI Solutions",
        "location_city": "San Francisco",
        "description": """
We are seeking a Senior Python Developer with strong experience in AI/ML to join our innovative team.

Responsibilities:
- Develop and maintain AI-powered applications using Python
- Work with machine learning frameworks like TensorFlow, PyTorch
- Design and implement scalable data processing pipelines
- Collaborate with data scientists and product teams
- Ensure code quality through testing and code reviews

Requirements:
- 5+ years of Python development experience
- Strong background in machine learning and AI
- Experience with cloud platforms (AWS, GCP, or Azure)
- Proficiency in SQL and database design
- Bachelor's degree in Computer Science or related field

Benefits:
- Competitive salary and equity
- Remote-first culture
- Health, dental, and vision insurance
- Professional development budget
        """,
        "status": "pending_review",
        "source_raw": json.dumps({
            "scraped_at": "2024-01-15T10:00:00Z",
            "source": "test_data"
        })
    }
    
    try:
        async with db_service.pool.acquire() as conn:
            await conn.execute(
                insert_query,
                test_data["id"],
                test_data["site"], 
                test_data["job_url"],
                test_data["title"],
                test_data["company"],
                test_data["location_city"],
                test_data["description"],
                test_data["status"],
                test_data["source_raw"]
            )
        
        logger.info(f"Created test job: {test_job_id}")
        return test_job_id
        
    except Exception as e:
        logger.error(f"Failed to create test job: {e}")
        return None


async def test_job_review_worker():
    """Test the job review worker function."""
    configure_logging()
    logger.info("Starting job review worker test")
    
    # Create a test job
    job_id = await create_test_job()
    if not job_id:
        logger.error("Failed to create test job")
        return
    
    # Test the worker function
    logger.info(f"Testing job review worker with job_id: {job_id}")
    
    try:
        result = process_job_review(job_id, max_retries=1)
        
        logger.info("Worker result:")
        logger.info(f"  Status: {result.get('status')}")
        logger.info(f"  Job ID: {result.get('job_id')}")
        logger.info(f"  Message: {result.get('message')}")
        logger.info(f"  Recommendation: {result.get('recommend')}")
        logger.info(f"  Confidence: {result.get('confidence')}")
        logger.info(f"  Processing Time: {result.get('processing_time_seconds', 0):.2f}s")
        
        if result.get('status') == 'completed':
            logger.success("Job review completed successfully!")
        elif result.get('status') == 'retry':
            logger.warning("Job review failed but will retry")
        else:
            logger.error("Job review failed")
            if result.get('error'):
                logger.error(f"Error details: {result['error']}")
        
        # Check database state
        db_service = get_database_service()
        if not db_service.initialized:
            await db_service.initialize()
        
        # Check job status
        job = await db_service.get_job_by_id(job_id)
        logger.info(f"Job status after review: {job.get('status') if job else 'NOT FOUND'}")
        
        # Check review record
        review = await db_service.get_job_review(job_id)
        if review:
            logger.info("Review record created:")
            logger.info(f"  Recommend: {review.get('recommend')}")
            logger.info(f"  Confidence: {review.get('confidence')}")
            logger.info(f"  Rationale: {review.get('rationale', '')[:100]}...")
            logger.info(f"  Error: {review.get('error_message', 'None')}")
        else:
            logger.warning("No review record found in database")
            
    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "create-job":
        # Just create a test job
        asyncio.run(create_test_job())
    else:
        # Run full test
        asyncio.run(test_job_review_worker())