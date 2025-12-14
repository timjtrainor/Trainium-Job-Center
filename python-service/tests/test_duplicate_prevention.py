#!/usr/bin/env python3
"""
Test script to verify preventive deduplication is working.
"""

import asyncio
import sys
import os
from datetime import datetime, timezone

# Add the python-service to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python-service'))

from app.schemas.jobspy import ScrapedJob
from app.services.infrastructure.job_persistence import persist_jobs


async def test_duplicate_prevention():
    """Test that duplicates are prevented from being processed."""

    print("🧪 Testing Preventive Deduplication...")
    print("=" * 50)

    # Create two identical jobs that should be considered duplicates
    original_job_data = {
        "title": "Software Engineer",
        "company": "Google",
        "location": "Mountain View, CA",
        "description": "Senior Python developer with machine learning experience required. Build AI systems.",
        "job_url": "https://example.com/job1",
        "date_posted": datetime.now(timezone.utc).isoformat(),
        "site": "test",
        "job_type": "full_time",
        "salary_min": 120000,
        "salary_max": 180000,
        "job_url_direct": "https://example.com/job1"
    }

    duplicate_job_data = {
        "title": "Software Engineer",  # Same title
        "company": "Google",  # Same company
        "location": "Mountain View, CA",  # Different location (shouldn't prevent canonical match)
        "description": "Python developer and ML expert needed. Build AI platforms.",  # Similar but different
        "job_url": "https://example.com/job2",  # Different URL
        "date_posted": datetime.now(timezone.utc).isoformat(),
        "site": "test2",  # Different site
        "job_type": "full_time",
        "salary_min": 130000,  # Slightly different salary
        "salary_max": 190000,
        "job_url_direct": "https://example.com/job2"
    }

    print("📌 Job 1: Original")
    print(f"   Title: {original_job_data['title']}")
    print(f"   Company: {original_job_data['company']}")
    print(f"   URL: {original_job_data['job_url']}")
    print()

    print("📌 Job 2: Duplicate")
    print(f"   Title: {duplicate_job_data['title']}")
    print(f"   Company: {duplicate_job_data['company']}")
    print(f"   URL: {duplicate_job_data['job_url']}")
    print()

    # Test insertion of first job
    print("🔄 Inserting original job...")
    result1 = await persist_jobs([original_job_data], "test")
    print(f"   Result: {result1}")

    if result1['inserted'] == 1:
        print("   ✅ SUCCESS: Original job inserted as expected")
    else:
        print("   ❌ ERROR: Original job should have been inserted")
        return False

    print()

    # Test insertion of duplicate job
    print("🔄 Inserting duplicate job...")
    result2 = await persist_jobs([duplicate_job_data], "test2")
    print(f"   Result: {result2}")

    if result2['blocked_duplicates'] == 1 and result2['inserted'] == 0:
        print("   ✅ SUCCESS: Duplicate job was blocked from insertion!")
        print("   ✅ SUCCESS: Preventive deduplication is working!")
        return True
    else:
        print("   ❌ ERROR: Duplicate should have been blocked, got inserted instead")
        return False


async def main():
    """Main test function."""
    try:
        success = await test_duplicate_prevention()

        print("\n" + "=" * 50)
        if success:
            print("🎉 TEST PASSED: Preventive deduplication is working correctly!")
        else:
            print("💥 TEST FAILED: Preventive deduplication is not working!")
            sys.exit(1)

    except Exception as e:
        print(f"\n💥 TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
