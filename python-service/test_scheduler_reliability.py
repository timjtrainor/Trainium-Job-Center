#!/usr/bin/env python3
"""
Scheduler reliability test script.
Tests Redis connectivity, database connectivity, and scheduler functionality.
"""
import sys
import os
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from loguru import logger
    from app.core.config import get_settings, configure_logging
    
    # Test imports for scheduler components
    has_scheduler = False
    has_redis = False
    has_db = False
    
    try:
        from app.services.infrastructure.scheduler import get_scheduler_service
        has_scheduler = True
    except ImportError as e:
        logger.warning(f"Scheduler import failed: {e}")
    
    try:
        from app.services.infrastructure.queue import get_queue_service
        import redis
        has_redis = True
    except ImportError as e:
        logger.warning(f"Redis import failed: {e}")
    
    try:
        from app.services.infrastructure.database import get_database_service
        import asyncpg
        has_db = True
    except ImportError as e:
        logger.warning(f"Database import failed: {e}")

except ImportError as e:
    print(f"Critical import error: {e}")
    print("This script requires the core dependencies to be installed.")
    sys.exit(1)


async def test_redis_connectivity():
    """Test Redis connection and basic operations."""
    logger.info("🔴 Testing Redis connectivity...")
    
    if not has_redis:
        logger.error("❌ Redis dependencies not available")
        return False
    
    try:
        settings = get_settings()
        
        # Test basic Redis connection
        redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=True
        )
        
        # Test ping
        pong = redis_client.ping()
        if not pong:
            logger.error("❌ Redis ping failed")
            return False
        
        logger.info("✅ Redis ping successful")
        
        # Test set/get operations
        test_key = "scheduler_test_key"
        test_value = f"test_value_{datetime.now().timestamp()}"
        
        redis_client.set(test_key, test_value, ex=60)  # Expire in 60s
        retrieved_value = redis_client.get(test_key)
        
        if retrieved_value != test_value:
            logger.error(f"❌ Redis set/get failed: expected {test_value}, got {retrieved_value}")
            return False
        
        logger.info("✅ Redis set/get operations successful")
        
        # Test lock operations
        lock_key = "test_lock"
        lock_value = "test_lock_value"
        
        # Acquire lock
        lock_result = redis_client.set(lock_key, lock_value, nx=True, ex=30)
        if not lock_result:
            logger.warning("⚠️ Test lock already exists or acquisition failed")
        else:
            logger.info("✅ Redis lock acquisition successful")
        
        # Release lock
        lua_script = """
        if redis.call("GET", KEYS[1]) == ARGV[1] then
            return redis.call("DEL", KEYS[1])
        else
            return 0
        end
        """
        release_result = redis_client.eval(lua_script, 1, lock_key, lock_value)
        logger.info(f"✅ Redis lock release: {release_result}")
        
        # Cleanup
        redis_client.delete(test_key)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Redis connectivity test failed: {e}")
        return False


async def test_database_connectivity():
    """Test database connection and basic operations."""
    logger.info("🗄️ Testing database connectivity...")
    
    if not has_db:
        logger.error("❌ Database dependencies not available")
        return False
    
    try:
        settings = get_settings()
        
        # Test basic database connection
        db_service = get_database_service()
        init_success = await db_service.initialize()
        
        if not init_success:
            logger.error("❌ Database initialization failed")
            return False
        
        logger.info("✅ Database initialization successful")
        
        # Test basic query
        async with db_service.pool.acquire() as conn:
            # Test connection with simple query
            result = await conn.fetchval("SELECT NOW()")
            logger.info(f"✅ Database query successful: {result}")
            
            # Test if jobs table exists
            table_check = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 'jobs'
                )
            """)
            
            if table_check:
                logger.info("✅ Jobs table exists")
                
                # Count existing jobs
                job_count = await conn.fetchval("SELECT COUNT(*) FROM public.jobs")
                logger.info(f"📊 Current job count in database: {job_count}")
            else:
                logger.warning("⚠️ Jobs table does not exist - may need schema setup")
            
            # Test if site_schedules table exists
            schedule_table_check = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 'site_schedules'
                )
            """)
            
            if schedule_table_check:
                logger.info("✅ Site_schedules table exists")
                
                # Count enabled schedules
                enabled_count = await conn.fetchval("""
                    SELECT COUNT(*) FROM public.site_schedules WHERE enabled = true
                """)
                logger.info(f"📊 Enabled site schedules: {enabled_count}")
                
                if enabled_count > 0:
                    # Get sample schedule
                    sample_schedule = await conn.fetchrow("""
                        SELECT id, site_name, interval_minutes, next_run_at, last_run_at
                        FROM public.site_schedules 
                        WHERE enabled = true 
                        LIMIT 1
                    """)
                    if sample_schedule:
                        logger.info(f"📋 Sample schedule: {dict(sample_schedule)}")
            else:
                logger.warning("⚠️ Site_schedules table does not exist - scheduler will not work")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database connectivity test failed: {e}")
        return False


async def test_queue_service():
    """Test RQ queue service functionality."""
    logger.info("📋 Testing queue service...")
    
    if not has_redis:
        logger.error("❌ Queue service requires Redis")
        return False
    
    try:
        queue_service = get_queue_service()
        init_success = await queue_service.initialize()
        
        if not init_success:
            logger.error("❌ Queue service initialization failed")
            return False
        
        logger.info("✅ Queue service initialization successful")
        
        # Test queue info
        queue_info = queue_service.get_queue_info()
        logger.info(f"📊 Queue info: {queue_info}")
        
        # Test Redis lock operations
        test_lock_key = "test_scheduler_lock"
        test_lock_value = f"test_value_{datetime.now().timestamp()}"
        
        # Test acquire lock
        lock_acquired = queue_service.acquire_redis_lock(test_lock_key, test_lock_value, timeout=30)
        if lock_acquired:
            logger.info("✅ Redis lock acquired successfully")
            
            # Test check lock
            existing_lock = queue_service.check_redis_lock(test_lock_key)
            if existing_lock:
                logger.info(f"✅ Redis lock check successful: {existing_lock}")
            
            # Test release lock
            lock_released = queue_service.release_redis_lock(test_lock_key, test_lock_value)
            if lock_released:
                logger.info("✅ Redis lock released successfully")
            else:
                logger.warning("⚠️ Redis lock release failed")
        else:
            logger.error("❌ Redis lock acquisition failed")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Queue service test failed: {e}")
        return False


async def test_scheduler_service():
    """Test scheduler service functionality."""
    logger.info("⏰ Testing scheduler service...")
    
    if not has_scheduler:
        logger.error("❌ Scheduler dependencies not available")
        return False
    
    try:
        scheduler_service = get_scheduler_service()
        init_success = await scheduler_service.initialize()
        
        if not init_success:
            logger.error("❌ Scheduler service initialization failed")
            return False
        
        logger.info("✅ Scheduler service initialization successful")
        
        # Test scheduler status
        status = await scheduler_service.get_scheduler_status()
        logger.info(f"📊 Scheduler status: {status}")
        
        # Test process_scheduled_sites (dry run mode)
        logger.info("🔍 Testing scheduled sites processing...")
        jobs_enqueued = await scheduler_service.process_scheduled_sites()
        logger.info(f"📈 Scheduled sites processing result: {jobs_enqueued} jobs enqueued")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Scheduler service test failed: {e}")
        return False


async def create_test_schedule():
    """Create a test schedule for verification (if database is available)."""
    logger.info("🧪 Creating test schedule...")
    
    if not has_db:
        logger.warning("⚠️ Cannot create test schedule - database not available")
        return False
    
    try:
        db_service = get_database_service()
        if not db_service.initialized:
            await db_service.initialize()
        
        # Check if site_schedules table exists
        async with db_service.pool.acquire() as conn:
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 'site_schedules'
                )
            """)
            
            if not table_exists:
                logger.warning("⚠️ Site_schedules table does not exist - cannot create test schedule")
                return False
            
            # Check if test schedule already exists
            existing_test = await conn.fetchval("""
                SELECT id FROM public.site_schedules 
                WHERE site_name = 'test_indeed'
            """)
            
            if existing_test:
                logger.info(f"ℹ️ Test schedule already exists with ID: {existing_test}")
                return True
            
            # Create test schedule
            test_payload = {
                "site_name": "indeed",
                "search_term": "software engineer test",
                "location": "Remote",
                "results_wanted": 5,
                "country_indeed": "USA"
            }
            
            next_run = datetime.now(timezone.utc) + timedelta(minutes=2)
            
            test_id = await conn.fetchval("""
                INSERT INTO public.site_schedules (
                    site_name, interval_minutes, payload, enabled, next_run_at,
                    min_pause_seconds, max_pause_seconds, max_retries
                ) VALUES (
                    'test_indeed', 60, $1, false, $2, 2, 8, 3
                ) RETURNING id
            """, str(test_payload).replace("'", '"'), next_run)
            
            logger.info(f"✅ Created test schedule with ID: {test_id}")
            logger.info(f"📅 Test schedule will run at: {next_run.isoformat()}")
            logger.info("⚠️ Note: Test schedule is DISABLED to prevent actual scraping")
            
            return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create test schedule: {e}")
        return False


async def main():
    """Main test function."""
    configure_logging()
    
    logger.info("🧪 Starting scheduler reliability tests...")
    logger.info(f"🐍 Python version: {sys.version}")
    
    settings = get_settings()
    logger.info(f"🔧 Environment: {settings.environment}")
    logger.info(f"🗄️ Database: {settings.database_url[:50]}...")
    logger.info(f"🔴 Redis: {settings.redis_host}:{settings.redis_port}")
    
    # Test results
    results = {
        "redis": False,
        "database": False,
        "queue_service": False,
        "scheduler_service": False,
        "test_schedule": False
    }
    
    # Test 1: Redis connectivity
    logger.info("\n" + "="*50)
    results["redis"] = await test_redis_connectivity()
    
    # Test 2: Database connectivity  
    logger.info("\n" + "="*50)
    results["database"] = await test_database_connectivity()
    
    # Test 3: Queue service (requires Redis)
    logger.info("\n" + "="*50)
    if results["redis"]:
        results["queue_service"] = await test_queue_service()
    else:
        logger.warning("⚠️ Skipping queue service test - Redis not available")
    
    # Test 4: Scheduler service (requires Redis + Database)
    logger.info("\n" + "="*50)
    if results["redis"] and results["database"]:
        results["scheduler_service"] = await test_scheduler_service()
    else:
        logger.warning("⚠️ Skipping scheduler service test - dependencies not available")
    
    # Test 5: Create test schedule (optional)
    logger.info("\n" + "="*50)
    if results["database"]:
        results["test_schedule"] = await create_test_schedule()
    
    # Final summary
    logger.info("\n" + "="*60)
    logger.info("📋 SCHEDULER RELIABILITY TEST SUMMARY")
    logger.info("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        logger.info(f"{test_name.replace('_', ' ').title():<20}: {status}")
    
    overall_success = all(results[key] for key in ["redis", "database", "queue_service", "scheduler_service"])
    
    if overall_success:
        logger.info("\n🎉 ALL CRITICAL TESTS PASSED - Scheduler should work reliably!")
        logger.info("\nNext steps:")
        logger.info("1. Start the scheduler daemon: python scheduler_daemon.py")
        logger.info("2. Start worker processes: python worker.py")
        logger.info("3. Monitor logs for scheduled job execution")
    else:
        logger.info("\n⚠️ SOME TESTS FAILED - Scheduler may not work properly")
        logger.info("\nRequired fixes:")
        
        if not results["redis"]:
            logger.info("- Fix Redis connectivity (check host, port, credentials)")
        if not results["database"]:
            logger.info("- Fix database connectivity and ensure proper schema")
        if not results["queue_service"]:
            logger.info("- Fix queue service initialization")
        if not results["scheduler_service"]:
            logger.info("- Fix scheduler service dependencies")
    
    return overall_success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        sys.exit(1)