#!/usr/bin/env python3
"""
Queue-Based Scraping System Demo
Demonstrates the complete workflow for the new queue + worker model.
"""
import sys
import os
import json

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from loguru import logger
import asyncio


def print_banner(title):
    """Print a formatted banner."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}\n")


def print_section(title):
    """Print a formatted section header."""
    print(f"\n📋 {title}")
    print("-" * (len(title) + 5))


def demo_api_endpoints():
    """Demonstrate the enhanced API endpoints."""
    
    print_banner("API ENDPOINTS DEMONSTRATION")
    
    print_section("Enhanced /jobs/scrape endpoint")
    
    print("🔄 ASYNC MODE (Default):")
    print("POST /jobs/scrape")
    print("Request:")
    async_request = {
        "site_name": "indeed",
        "search_term": "python developer", 
        "location": "remote",
        "is_remote": True,
        "results_wanted": 50
    }
    print(json.dumps(async_request, indent=2))
    
    print("\nResponse:")
    async_response = {
        "status": "success",
        "data": {
            "task_id": "run_a1b2c3d4",
            "run_id": "manual_a1b2c3d4",
            "status": "queued",
            "execution_mode": "async",
            "site_name": "indeed",
            "search_term": "python developer"
        },
        "message": "Job scraping task queued for indeed"
    }
    print(json.dumps(async_response, indent=2))
    
    print("\n🔄 SYNC MODE (For diagnostic runs):")
    print("POST /jobs/scrape?mode=sync")
    print("Request:")
    sync_request = {
        "site_name": "indeed",
        "search_term": "python developer",
        "results_wanted": 15
    }
    print(json.dumps(sync_request, indent=2))
    
    print("\nResponse:")
    sync_response = {
        "status": "success",
        "data": {
            "jobs": ["... job objects ..."],
            "total_found": 12,
            "search_metadata": {
                "site": "indeed",
                "search_params": sync_request,
                "success_rate": 1.0
            },
            "execution_mode": "sync"
        },
        "message": "Scraped 12 jobs from indeed"
    }
    print(json.dumps(sync_response, indent=2))
    
    print_section("New status checking endpoint")
    print("GET /jobs/scrape/{run_id}")
    print("Response:")
    status_response = {
        "status": "success", 
        "data": {
            "run_id": "manual_a1b2c3d4",
            "status": "succeeded",
            "trigger": "manual",
            "started_at": "2025-01-24T12:00:00Z",
            "finished_at": "2025-01-24T12:02:30Z",
            "requested_pages": 1,
            "completed_pages": 1,
            "errors_count": 0,
            "message": "Scraped 47 jobs from indeed"
        }
    }
    print(json.dumps(status_response, indent=2))
    
    print_section("Unchanged /jobs/sites endpoint")
    print("✅ GET /jobs/sites - Returns supported job sites (unchanged)")
    
    print_section("New scheduler endpoints")
    print("📅 POST /scheduler/run - Manually trigger scheduler")
    print("📊 GET /scheduler/status - Get scheduler status")
    print("📈 GET /jobs/queue/status - Get queue metrics")


def demo_database_schema():
    """Demonstrate the database schema."""
    
    print_banner("DATABASE SCHEMA")
    
    print_section("site_schedules table")
    print("""
CREATE TABLE site_schedules (
    id UUID PRIMARY KEY,
    site_name TEXT NOT NULL UNIQUE,
    enabled BOOLEAN NOT NULL DEFAULT true,
    interval_minutes INTEGER NOT NULL DEFAULT 60,
    last_run_at TIMESTAMPTZ,
    next_run_at TIMESTAMPTZ,
    payload JSONB NOT NULL DEFAULT '{}',
    min_pause_seconds INTEGER NOT NULL DEFAULT 2,
    max_pause_seconds INTEGER NOT NULL DEFAULT 8,
    max_retries INTEGER NOT NULL DEFAULT 3,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
    """)
    
    print("Sample data:")
    sample_schedule = {
        "site_name": "indeed",
        "enabled": True,
        "interval_minutes": 240,
        "payload": {
            "search_term": "software engineer",
            "location": "remote", 
            "is_remote": True,
            "results_wanted": 50
        },
        "min_pause_seconds": 2,
        "max_pause_seconds": 8
    }
    print(json.dumps(sample_schedule, indent=2))
    
    print_section("scrape_runs table")
    print("""
CREATE TABLE scrape_runs (
    id UUID PRIMARY KEY,
    run_id TEXT NOT NULL UNIQUE,
    site_schedule_id UUID REFERENCES site_schedules(id),
    task_id TEXT,
    trigger TEXT NOT NULL CHECK (trigger IN ('schedule', 'manual')),
    status TEXT NOT NULL CHECK (status IN ('queued', 'running', 'succeeded', 'partial', 'failed')),
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    requested_pages INTEGER DEFAULT 0,
    completed_pages INTEGER DEFAULT 0,
    errors_count INTEGER DEFAULT 0,
    message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
    """)
    
    print("Sample run record:")
    sample_run = {
        "run_id": "sched_abc12345",
        "trigger": "schedule",
        "status": "succeeded",
        "requested_pages": 1,
        "completed_pages": 1,
        "errors_count": 0,
        "message": "Scraped 47 jobs from indeed"
    }
    print(json.dumps(sample_run, indent=2))


def demo_architecture():
    """Demonstrate the system architecture."""
    
    print_banner("SYSTEM ARCHITECTURE")
    
    print_section("Components")
    
    components = [
        ("🌐 FastAPI Application", "Serves API endpoints, handles sync requests"),
        ("🔄 Redis Queue (RQ)", "Manages job queue and task distribution"),
        ("👷 Worker Processes", "Execute scraping jobs with error handling"),
        ("⏰ Scheduler Daemon", "Enqueues jobs based on site schedules"),
        ("🗄️ PostgreSQL Database", "Stores schedules, run history, audit trail"),
        ("🔧 Shared Scraping Function", "Single source of truth for job scraping")
    ]
    
    for component, description in components:
        print(f"{component:<25} {description}")
    
    print_section("Data Flow")
    print("""
1. 📊 Scheduler reads enabled site_schedules
2. 🔄 Enqueues scraping tasks in Redis queue
3. 👷 Workers pick up tasks from queue
4. 🌐 Workers execute shared scraping function
5. 📝 Update run status in scrape_runs table
6. 🔍 API provides status tracking via run_id
    """)
    
    print_section("Deployment Components")
    deployment = [
        "🐳 FastAPI Container - API server",
        "👷 Worker Container(s) - Scalable job processors", 
        "⏰ Scheduler Container - Single daemon instance",
        "🔴 Redis Container - Queue backend",
        "🐘 PostgreSQL Container - Data persistence"
    ]
    
    for component in deployment:
        print(f"  • {component}")


def demo_usage_scenarios():
    """Demonstrate usage scenarios."""
    
    print_banner("USAGE SCENARIOS")
    
    print_section("Scenario 1: Ad-hoc Manual Scraping")
    print("""
🎯 Use Case: Developer wants to quickly test scraping parameters

1. POST /jobs/scrape (async mode)
   ➤ Returns task_id and run_id immediately
   ➤ Job runs in background with full error handling

2. GET /jobs/scrape/{run_id}
   ➤ Check status: queued → running → succeeded/failed
   ➤ Get results when completed
    """)
    
    print_section("Scenario 2: Diagnostic Sync Scraping")
    print("""
🎯 Use Case: Quick validation with immediate results

1. POST /jobs/scrape?mode=sync
   ➤ Limited to 25 results max
   ➤ Returns results immediately
   ➤ Perfect for testing parameters
    """)
    
    print_section("Scenario 3: Scheduled Automated Scraping")
    print("""
🎯 Use Case: Regular scraping every 4 hours

1. Configure site_schedules table:
   - site_name: "indeed" 
   - enabled: true
   - interval_minutes: 240
   - payload: {search params}

2. Scheduler daemon automatically:
   - Checks for due schedules every minute
   - Applies ±10% jitter to prevent thundering herd
   - Prevents overlapping runs with Redis locks
   - Updates next_run_at after enqueueing
    """)
    
    print_section("Scenario 4: Monitoring and Observability")
    print("""
🎯 Use Case: Operations team monitors system health

1. GET /jobs/health
   ➤ Overall system health (API + Queue + DB)

2. GET /jobs/queue/status  
   ➤ Queue depth, processing stats

3. GET /scheduler/status
   ➤ Active schedules, last run times

4. Structured JSON logs with correlation IDs
   ➤ Trace requests through queue → worker → completion
    """)


def demo_error_handling():
    """Demonstrate error handling and resilience."""
    
    print_banner("ERROR HANDLING & RESILIENCE")
    
    print_section("Worker Error Handling")
    error_handling = [
        ("🔄 Automatic Retries", "Up to 3 retries with exponential backoff"),
        ("📊 Success Metrics", "succeeded (>70%), partial (30-70%), failed (<30%)"),
        ("🔒 Site Locking", "Prevents overlapping runs per site"),
        ("⏱️ Timeouts", "15-minute job timeout prevents hanging"),
        ("📝 Detailed Logging", "Correlation IDs track execution flow")
    ]
    
    for feature, description in error_handling:
        print(f"{feature:<20} {description}")
    
    print_section("Scheduler Resilience")
    scheduler_features = [
        ("🎲 Jitter", "±10% randomization prevents thundering herd"),
        ("🔒 Redis Locks", "Atomic per-site execution locking"),
        ("🔄 Graceful Recovery", "Handles Redis/DB temporary failures"),
        ("📈 Monitoring", "Health checks and status endpoints")
    ]
    
    for feature, description in scheduler_features:
        print(f"{feature:<20} {description}")


def main():
    """Run the complete demonstration."""
    
    print("🚀 Queue-Based Job Scraping System")
    print("   Trainium Job Center - Complete Architecture Demo")
    
    demo_architecture()
    demo_database_schema()  
    demo_api_endpoints()
    demo_usage_scenarios()
    demo_error_handling()
    
    print_banner("DEPLOYMENT READY")
    print("✨ The queue-based scraping system is fully implemented and ready!")
    print("\n📦 Next Steps:")
    print("   1. Apply database migrations with Sqitch")
    print("   2. Configure Redis connection")
    print("   3. Start FastAPI application")
    print("   4. Start worker processes")
    print("   5. Start scheduler daemon")
    print("   6. Configure site schedules via database")
    print("\n🎯 Benefits Achieved:")
    print("   ✅ Async job processing with queue system")
    print("   ✅ Scheduled scraping with jitter and locking")
    print("   ✅ Maintained backward compatibility")
    print("   ✅ Enhanced observability and monitoring")
    print("   ✅ Horizontal scaling capability")
    print("   ✅ Robust error handling and retries")


if __name__ == "__main__":
    main()