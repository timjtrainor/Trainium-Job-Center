#!/usr/bin/env python3
"""
Script to enable job schedules and fix pagination configuration.
This addresses the issue where schedules are disabled by default.
"""
import sys
import os
import asyncio
from datetime import datetime, timezone, timedelta

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from loguru import logger
    from app.core.config import get_settings, configure_logging
    from app.services.infrastructure.database import get_database_service
    
    async def enable_job_schedules():
        """Enable job schedules and update their configuration for proper pagination."""
        configure_logging()
        settings = get_settings()
        
        logger.info("🔧 Enabling job schedules and fixing pagination configuration...")
        
        db_service = get_database_service()
        await db_service.initialize()
        
        if not db_service.initialized:
            logger.error("❌ Failed to initialize database service")
            return False
        
        async with db_service.pool.acquire() as conn:
            # Check if site_schedules table exists
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 'site_schedules'
                )
            """)
            
            if not table_exists:
                logger.error("❌ site_schedules table does not exist - run database migrations first")
                return False
            
            # Get current schedules
            schedules = await conn.fetch("SELECT * FROM site_schedules ORDER BY site_name")
            logger.info(f"📊 Found {len(schedules)} schedules in database")
            
            for schedule in schedules:
                logger.info(f"   {schedule['site_name']}: enabled={schedule['enabled']}, payload={schedule['payload']}")
            
            # Update schedules with proper pagination configuration
            updates_made = 0
            
            # Enable high-volume sites with pagination
            high_volume_sites = {
                'indeed': {
                    'enabled': True,
                    'interval_minutes': 120,  # 2 hours
                    'payload': {
                        "search_term": "software engineer",
                        "location": "Remote",
                        "is_remote": True,
                        "results_wanted": 100,  # This will auto-enable pagination
                        "country_indeed": "USA"
                    }
                },
                'linkedin': {
                    'enabled': True,
                    'interval_minutes': 180,  # 3 hours
                    'payload': {
                        "search_term": "software engineer",
                        "location": "Remote", 
                        "is_remote": True,
                        "results_wanted": 75,  # This will auto-enable pagination
                        "linkedin_fetch_description": True
                    }
                },
                'glassdoor': {
                    'enabled': True,
                    'interval_minutes': 150,  # 2.5 hours
                    'payload': {
                        "search_term": "software engineer",
                        "location": "Remote",
                        "is_remote": True,
                        "results_wanted": 50,  # This will auto-enable pagination
                        "country_indeed": "USA"
                    }
                }
            }
            
            for site_name, config in high_volume_sites.items():
                # Calculate next run time (stagger the starts)
                minutes_offset = list(high_volume_sites.keys()).index(site_name) * 30
                next_run_at = datetime.now(timezone.utc) + timedelta(minutes=minutes_offset + 5)
                
                # Update or insert schedule
                result = await conn.execute("""
                    INSERT INTO site_schedules (site_name, enabled, interval_minutes, payload, next_run_at)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (site_name) 
                    DO UPDATE SET 
                        enabled = EXCLUDED.enabled,
                        interval_minutes = EXCLUDED.interval_minutes,
                        payload = EXCLUDED.payload,
                        next_run_at = EXCLUDED.next_run_at,
                        updated_at = NOW()
                """, site_name, config['enabled'], config['interval_minutes'], 
                str(config['payload']).replace("'", '"'), next_run_at)
                
                updates_made += 1
                logger.info(f"✅ Updated {site_name}: enabled={config['enabled']}, "
                          f"results_wanted={config['payload']['results_wanted']}, "
                          f"next_run={next_run_at.strftime('%H:%M:%S')}")
            
            # Disable lower priority sites for now
            low_priority_sites = ['ziprecruiter', 'google']
            for site_name in low_priority_sites:
                await conn.execute("""
                    UPDATE site_schedules 
                    SET enabled = false, updated_at = NOW()
                    WHERE site_name = $1
                """, site_name)
                logger.info(f"⏸️ Disabled {site_name} (low priority)")
            
            # Show final configuration
            logger.info("\n📋 Final Schedule Configuration:")
            final_schedules = await conn.fetch("""
                SELECT site_name, enabled, interval_minutes, payload, next_run_at 
                FROM site_schedules 
                ORDER BY enabled DESC, site_name
            """)
            
            for schedule in final_schedules:
                status = "🟢 ENABLED" if schedule['enabled'] else "🔴 DISABLED"
                payload = eval(schedule['payload']) if isinstance(schedule['payload'], str) else schedule['payload']
                results_wanted = payload.get('results_wanted', 'N/A')
                next_run = schedule['next_run_at'].strftime('%Y-%m-%d %H:%M:%S') if schedule['next_run_at'] else 'Not scheduled'
                
                logger.info(f"   {schedule['site_name']:<12} {status} | "
                          f"Results: {results_wanted:<3} | "
                          f"Interval: {schedule['interval_minutes']}min | "
                          f"Next: {next_run}")
            
            logger.info(f"\n🎉 Successfully updated {updates_made} schedules!")
            logger.info("🚀 Schedules are now configured for high-volume scraping with auto-pagination")
            
            return True
    
    async def main():
        """Main function."""
        try:
            success = await enable_job_schedules()
            if success:
                logger.info("\n✅ Schedule configuration completed successfully!")
                logger.info("Next steps:")
                logger.info("1. Start the scheduler: docker-compose up scheduler")
                logger.info("2. Start workers: docker-compose up worker")
                logger.info("3. Monitor logs for pagination activity")
                return True
            else:
                logger.error("❌ Failed to configure schedules")
                return False
        except Exception as e:
            logger.error(f"💥 Configuration failed: {e}")
            return False

except ImportError as e:
    print(f"Import error: {e}")
    print("This script requires the application dependencies to be installed.")
    sys.exit(1)

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Script failed: {e}")
        sys.exit(1)