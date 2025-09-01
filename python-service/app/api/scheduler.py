"""
Scheduler API endpoints for managing scheduled tasks and reminders.
"""
from fastapi import APIRouter, Query
from typing import Optional
from loguru import logger

from ..models.responses import StandardResponse
from ..services.scheduler_service import get_scheduler_service

router = APIRouter()


@router.get("/due", response_model=StandardResponse)
async def get_due_follow_ups(
    user_id: Optional[str] = Query(None, description="Filter by user ID")
):
    """
    Get all follow-ups that are due today or overdue.
    
    Args:
        user_id: Optional user ID to filter results
        
    Returns:
        StandardResponse: List of due follow-ups
    """
    scheduler_service = get_scheduler_service()
    
    logger.info(f"Getting due follow-ups for user: {user_id or 'all'}")
    
    return await scheduler_service.get_due_follow_ups(user_id)


@router.get("/upcoming", response_model=StandardResponse)
async def get_upcoming_follow_ups(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    days_ahead: int = Query(7, ge=1, le=30, description="Number of days to look ahead")
):
    """
    Get follow-ups coming due within the specified number of days.
    
    Args:
        user_id: Optional user ID to filter results
        days_ahead: Number of days to look ahead (1-30, default: 7)
        
    Returns:
        StandardResponse: List of upcoming follow-ups
    """
    scheduler_service = get_scheduler_service()
    
    logger.info(f"Getting upcoming follow-ups for user: {user_id or 'all'}, {days_ahead} days ahead")
    
    return await scheduler_service.get_upcoming_follow_ups(user_id, days_ahead)


@router.get("/summary", response_model=StandardResponse)
async def get_schedule_summary(
    user_id: Optional[str] = Query(None, description="Filter by user ID")
):
    """
    Get a summary of scheduling information including overdue, due today, and upcoming items.
    
    Args:
        user_id: Optional user ID to filter results
        
    Returns:
        StandardResponse: Schedule summary data
    """
    scheduler_service = get_scheduler_service()
    
    logger.info(f"Getting schedule summary for user: {user_id or 'all'}")
    
    return await scheduler_service.get_schedule_summary(user_id)


@router.get("/health", response_model=StandardResponse)
async def scheduler_health_check():
    """
    Check the health of the scheduler service.
    
    Returns:
        StandardResponse: Service health information
    """
    scheduler_service = get_scheduler_service()
    
    health_data = await scheduler_service.health_check()
    
    from ..models.responses import create_success_response
    return create_success_response(
        data=health_data,
        message="Scheduler service health check completed"
    )