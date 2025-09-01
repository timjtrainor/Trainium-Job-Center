"""
Scheduler service for managing scheduled tasks and reminders.
This module provides the foundation for scheduling follow-ups, reminders,
and recurring tasks within the Trainium Job Center application.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, date, timedelta
import asyncio
from loguru import logger

from ..core.config import get_settings
from ..models.responses import StandardResponse, create_success_response, create_error_response
from .postgrest import get_postgrest_service


class SchedulerService:
    """
    Service class for handling scheduling and reminder functionality.
    Provides methods to manage follow-ups, due date checks, and task scheduling.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.initialized = False
        self.postgrest_service = None
        
    async def initialize(self) -> bool:
        """
        Initialize the scheduler service.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            # Get PostgREST service for database operations
            self.postgrest_service = get_postgrest_service()
            
            # Ensure PostgREST service is initialized
            if not self.postgrest_service.client:
                await self.postgrest_service.initialize()
            
            self.initialized = True
            logger.info("Scheduler service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize scheduler service: {str(e)}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the scheduler service.
        
        Returns:
            Dict[str, Any]: Health status information
        """
        return {
            "service": "scheduler",
            "initialized": self.initialized,
            "postgrest_available": self.postgrest_service is not None and self.postgrest_service.client is not None,
            "status": "ready" if self.initialized else "not_initialized"
        }
    
    async def get_due_follow_ups(self, user_id: Optional[str] = None) -> StandardResponse:
        """
        Get all follow-ups that are due today or overdue.
        
        Args:
            user_id (str, optional): Filter by specific user ID
            
        Returns:
            StandardResponse: List of due follow-ups
        """
        try:
            if not self.initialized:
                await self.initialize()
            
            if not self.postgrest_service:
                return create_error_response(
                    error="Scheduler service not properly initialized",
                    message="PostgREST service not available"
                )
            
            today = date.today().isoformat()
            
            # Query for messages with due follow-up dates
            endpoint = "/messages"
            params = {
                "follow_up_due_date": f"lte.{today}",
                "select": "*,contact:contacts(first_name,last_name),company:companies(company_name)"
            }
            
            if user_id:
                params["user_id"] = f"eq.{user_id}"
            
            response = await self.postgrest_service.client.get(endpoint, params=params)
            
            if response.status_code == 200:
                data = response.json()
                return create_success_response(
                    data={
                        "count": len(data),
                        "due_date": today,
                        "follow_ups": data
                    },
                    message=f"Found {len(data)} due follow-ups"
                )
            else:
                return create_error_response(
                    error=f"Failed to fetch due follow-ups: HTTP {response.status_code}",
                    message=response.text
                )
                
        except Exception as e:
            logger.error(f"Error fetching due follow-ups: {str(e)}")
            return create_error_response(
                error="Failed to fetch due follow-ups",
                message=str(e)
            )
    
    async def get_upcoming_follow_ups(self, user_id: Optional[str] = None, days_ahead: int = 7) -> StandardResponse:
        """
        Get follow-ups coming due within the specified number of days.
        
        Args:
            user_id (str, optional): Filter by specific user ID
            days_ahead (int): Number of days to look ahead (default: 7)
            
        Returns:
            StandardResponse: List of upcoming follow-ups
        """
        try:
            if not self.initialized:
                await self.initialize()
            
            if not self.postgrest_service:
                return create_error_response(
                    error="Scheduler service not properly initialized",
                    message="PostgREST service not available"
                )
            
            today = date.today()
            future_date = (today + timedelta(days=days_ahead)).isoformat()
            today_str = today.isoformat()
            
            # Query for messages with upcoming follow-up dates
            endpoint = "/messages"
            params = {
                "follow_up_due_date": f"gte.{today_str}",
                "follow_up_due_date": f"lte.{future_date}",
                "select": "*,contact:contacts(first_name,last_name),company:companies(company_name)",
                "order": "follow_up_due_date.asc"
            }
            
            if user_id:
                params["user_id"] = f"eq.{user_id}"
            
            response = await self.postgrest_service.client.get(endpoint, params=params)
            
            if response.status_code == 200:
                data = response.json()
                return create_success_response(
                    data={
                        "count": len(data),
                        "date_range": {
                            "start": today_str,
                            "end": future_date
                        },
                        "days_ahead": days_ahead,
                        "follow_ups": data
                    },
                    message=f"Found {len(data)} upcoming follow-ups in the next {days_ahead} days"
                )
            else:
                return create_error_response(
                    error=f"Failed to fetch upcoming follow-ups: HTTP {response.status_code}",
                    message=response.text
                )
                
        except Exception as e:
            logger.error(f"Error fetching upcoming follow-ups: {str(e)}")
            return create_error_response(
                error="Failed to fetch upcoming follow-ups",
                message=str(e)
            )
    
    async def get_schedule_summary(self, user_id: Optional[str] = None) -> StandardResponse:
        """
        Get a summary of scheduling information including overdue, due today, and upcoming items.
        
        Args:
            user_id (str, optional): Filter by specific user ID
            
        Returns:
            StandardResponse: Schedule summary data
        """
        try:
            if not self.initialized:
                await self.initialize()
            
            # Get due follow-ups
            due_response = await self.get_due_follow_ups(user_id)
            if due_response.status != "success":
                return due_response
            
            # Get upcoming follow-ups
            upcoming_response = await self.get_upcoming_follow_ups(user_id, 7)
            if upcoming_response.status != "success":
                return upcoming_response
            
            due_data = due_response.data
            upcoming_data = upcoming_response.data
            
            # Separate overdue from due today
            today = date.today().isoformat()
            overdue_items = []
            due_today_items = []
            
            for item in due_data.get("follow_ups", []):
                if item.get("follow_up_due_date"):
                    if item["follow_up_due_date"] < today:
                        overdue_items.append(item)
                    elif item["follow_up_due_date"] == today:
                        due_today_items.append(item)
            
            summary = {
                "date": today,
                "overdue": {
                    "count": len(overdue_items),
                    "items": overdue_items
                },
                "due_today": {
                    "count": len(due_today_items),
                    "items": due_today_items
                },
                "upcoming_7_days": {
                    "count": upcoming_data.get("count", 0),
                    "items": upcoming_data.get("follow_ups", [])
                }
            }
            
            total_active = len(overdue_items) + len(due_today_items) + upcoming_data.get("count", 0)
            
            return create_success_response(
                data=summary,
                message=f"Schedule summary: {total_active} total items ({len(overdue_items)} overdue, {len(due_today_items)} due today, {upcoming_data.get('count', 0)} upcoming)"
            )
            
        except Exception as e:
            logger.error(f"Error generating schedule summary: {str(e)}")
            return create_error_response(
                error="Failed to generate schedule summary",
                message=str(e)
            )


# Global service instance
scheduler_service = SchedulerService()


def get_scheduler_service() -> SchedulerService:
    """Get the global scheduler service instance."""
    return scheduler_service