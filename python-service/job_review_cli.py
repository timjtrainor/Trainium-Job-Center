#!/usr/bin/env python3
"""
Job Review CLI - Command line utility for managing job reviews.

Usage:
    python job_review_cli.py queue [--limit N] [--retries N]    # Queue pending jobs
    python job_review_cli.py status <job_id>                   # Check job review status  
    python job_review_cli.py stats                             # Show review statistics
    python job_review_cli.py requeue [--retries N]            # Re-queue failed jobs
    python job_review_cli.py test <job_id>                    # Test review on specific job
"""
import sys
import asyncio
import argparse
from loguru import logger

from app.core.config import configure_logging
from app.services.infrastructure.job_review_service import get_job_review_service
from app.services.infrastructure.queue import get_queue_service


async def main():
    """Main CLI function."""
    configure_logging()
    
    parser = argparse.ArgumentParser(description="Job Review Management CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Queue command
    queue_parser = subparsers.add_parser("queue", help="Queue pending jobs for review")
    queue_parser.add_argument("--limit", type=int, default=50, help="Maximum jobs to queue")
    queue_parser.add_argument("--retries", type=int, default=3, help="Maximum retry attempts")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Check job review status")
    status_parser.add_argument("job_id", help="Job ID to check")
    
    # Stats command
    subparsers.add_parser("stats", help="Show review statistics")
    
    # Requeue command
    requeue_parser = subparsers.add_parser("requeue", help="Re-queue failed jobs")
    requeue_parser.add_argument("--retries", type=int, default=3, help="Maximum retry attempts")
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Test review on specific job")
    test_parser.add_argument("job_id", help="Job ID to test review")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize service
    service = get_job_review_service()
    success = await service.initialize()
    if not success:
        logger.error("Failed to initialize job review service")
        return
    
    if args.command == "queue":
        result = await service.queue_pending_jobs(args.limit, args.retries)
        print(f"Status: {result['status']}")
        print(f"Queued: {result['queued_count']} jobs")
        print(f"Failed: {result['failed_count']} jobs")
        print(f"Message: {result['message']}")
        
    elif args.command == "status":
        result = await service.get_review_status(args.job_id)
        if not result:
            print(f"Job {args.job_id} not found")
            return
        
        print(f"Job ID: {result['job_id']}")
        print(f"Title: {result['job_title']}")
        print(f"Company: {result['job_company']}")
        print(f"Status: {result['job_status']}")
        print(f"Review Exists: {result['review_exists']}")
        
        if result['review_data']:
            review = result['review_data']
            print(f"Recommendation: {review['recommend']}")
            print(f"Confidence: {review['confidence']}")  
            print(f"Rationale: {review['rationale']}")
            if review['error_message']:
                print(f"Error: {review['error_message']}")
            print(f"Retry Count: {review['retry_count']}")
            print(f"Created: {review['created_at']}")
            print(f"Updated: {review['updated_at']}")
    
    elif args.command == "stats":
        result = await service.get_review_stats()
        
        print("=== Job Status Counts ===")
        for status, count in result['job_status_counts'].items():
            print(f"  {status}: {count}")
        
        print("\n=== Review Statistics ===")
        stats = result['review_stats']
        print(f"  Total Reviews: {stats['total_reviews']}")
        print(f"  Recommended: {stats['recommended_count']}")
        print(f"  Not Recommended: {stats['not_recommended_count']}")
        print(f"  Errors: {stats['error_count']}")
        print(f"  Avg Processing Time: {stats['avg_processing_time_seconds']:.2f}s")
        print(f"  Avg Retry Count: {stats['avg_retry_count']:.1f}")
        
        print("\n=== Queue Information ===")
        queue_info = result['queue_info']
        if 'review_queue' in queue_info:
            review_q = queue_info['review_queue']
            print(f"  Review Queue ({review_q['name']}):")
            print(f"    Pending: {review_q['length']}")
            print(f"    Running: {review_q['started_jobs']}")
            print(f"    Finished: {review_q['finished_jobs']}")
            print(f"    Failed: {review_q['failed_jobs']}")
    
    elif args.command == "requeue":
        result = await service.requeue_failed_jobs(args.retries)
        print(f"Status: {result['status']}")
        print(f"Re-queued: {result['requeued_count']} jobs")
        print(f"Message: {result['message']}")
        
        if result.get('jobs'):
            print("\nRe-queued Jobs:")
            for job in result['jobs']:
                status_indicator = "✓" if job['task_id'] else "✗"
                print(f"  {status_indicator} {job['job_id']}: {job['title']} at {job['company']} (retry: {job['retry_count']})")
    
    elif args.command == "test":
        # Queue single job for testing
        queue_service = get_queue_service()
        if not queue_service.initialized:
            await queue_service.initialize()
        
        task_id = queue_service.enqueue_job_review(args.job_id)
        if task_id:
            print(f"Queued job {args.job_id} for review with task ID: {task_id}")
            print("Use 'python job_review_cli.py status <job_id>' to check progress")
        else:
            print(f"Failed to queue job {args.job_id}")


if __name__ == "__main__":
    asyncio.run(main())