from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from ....core.database import get_db
from ....services.analytics_service import AnalyticsService
from ....schemas.common import ResponseModel
import structlog

logger = structlog.get_logger()
router = APIRouter()


@router.get("/dashboard-metrics")
async def get_dashboard_metrics(
    days: int = Query(30, description="Number of days to analyze"),
    lender_id: Optional[int] = Query(None, description="Filter by specific lender"),
    db: AsyncSession = Depends(get_db)
) -> ResponseModel[Dict[str, Any]]:
    """Get comprehensive dashboard metrics"""
    try:
        analytics_service = AnalyticsService()
        metrics = await analytics_service.get_dashboard_metrics(db, days, lender_id)
        
        return ResponseModel(
            success=True,
            data=metrics,
            message="Dashboard metrics retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Failed to get dashboard metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard metrics")


@router.get("/lender-performance")
async def get_lender_performance(
    days: int = Query(30, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db)
) -> ResponseModel[List[Dict[str, Any]]]:
    """Get performance metrics by lender"""
    try:
        analytics_service = AnalyticsService()
        performance = await analytics_service.get_lender_performance(db, days)
        
        return ResponseModel(
            success=True,
            data=performance,
            message="Lender performance metrics retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Failed to get lender performance: {e}")
        raise HTTPException(status_code=500, detail="Failed to get lender performance")


@router.get("/error-analysis")
async def get_error_analysis(
    days: int = Query(30, description="Number of days to analyze"),
    lender_id: Optional[int] = Query(None, description="Filter by specific lender"),
    db: AsyncSession = Depends(get_db)
) -> ResponseModel[List[Dict[str, Any]]]:
    """Get error analysis and trends"""
    try:
        analytics_service = AnalyticsService()
        errors = await analytics_service.get_error_analysis(db, days, lender_id)
        
        return ResponseModel(
            success=True,
            data=errors,
            message="Error analysis retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Failed to get error analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to get error analysis")


@router.get("/response-time-trends")
async def get_response_time_trends(
    days: int = Query(30, description="Number of days to analyze"),
    lender_id: Optional[int] = Query(None, description="Filter by specific lender"),
    db: AsyncSession = Depends(get_db)
) -> ResponseModel[List[Dict[str, Any]]]:
    """Get response time trends over time"""
    try:
        analytics_service = AnalyticsService()
        trends = await analytics_service.get_response_time_trends(db, days, lender_id)
        
        return ResponseModel(
            success=True,
            data=trends,
            message="Response time trends retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Failed to get response time trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to get response time trends")


@router.get("/integration-health")
async def get_integration_health(
    db: AsyncSession = Depends(get_db)
) -> ResponseModel[List[Dict[str, Any]]]:
    """Get health status of all integrations"""
    try:
        analytics_service = AnalyticsService()
        health = await analytics_service.get_integration_health(db)
        
        return ResponseModel(
            success=True,
            data=health,
            message="Integration health status retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Failed to get integration health: {e}")
        raise HTTPException(status_code=500, detail="Failed to get integration health")


@router.get("/field-mapping-analytics")
async def get_field_mapping_analytics(
    lender_id: Optional[int] = Query(None, description="Filter by specific lender"),
    db: AsyncSession = Depends(get_db)
) -> ResponseModel[Dict[str, Any]]:
    """Get analytics about field mapping usage and effectiveness"""
    try:
        analytics_service = AnalyticsService()
        analytics = await analytics_service.get_field_mapping_analytics(db, lender_id)
        
        return ResponseModel(
            success=True,
            data=analytics,
            message="Field mapping analytics retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Failed to get field mapping analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get field mapping analytics")


@router.get("/sequence-performance")
async def get_sequence_performance(
    days: int = Query(30, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db)
) -> ResponseModel[List[Dict[str, Any]]]:
    """Get performance metrics for integration sequences"""
    try:
        analytics_service = AnalyticsService()
        performance = await analytics_service.get_sequence_performance(db, days)
        
        return ResponseModel(
            success=True,
            data=performance,
            message="Sequence performance metrics retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Failed to get sequence performance: {e}")
        raise HTTPException(status_code=500, detail="Failed to get sequence performance")


@router.get("/comprehensive-analytics")
async def get_comprehensive_analytics(
    days: int = Query(30, description="Number of days to analyze"),
    lender_id: Optional[int] = Query(None, description="Filter by specific lender"),
    db: AsyncSession = Depends(get_db)
) -> ResponseModel[Dict[str, Any]]:
    """Get comprehensive analytics for all aspects"""
    try:
        analytics_service = AnalyticsService()
        
        # Get all analytics data
        dashboard_metrics = await analytics_service.get_dashboard_metrics(db, days, lender_id)
        lender_performance = await analytics_service.get_lender_performance(db, days)
        error_analysis = await analytics_service.get_error_analysis(db, days, lender_id)
        response_time_trends = await analytics_service.get_response_time_trends(db, days, lender_id)
        integration_health = await analytics_service.get_integration_health(db)
        field_mapping_analytics = await analytics_service.get_field_mapping_analytics(db, lender_id)
        sequence_performance = await analytics_service.get_sequence_performance(db, days)
        
        comprehensive_data = {
            "dashboard_metrics": dashboard_metrics,
            "lender_performance": lender_performance,
            "error_analysis": error_analysis,
            "response_time_trends": response_time_trends,
            "integration_health": integration_health,
            "field_mapping_analytics": field_mapping_analytics,
            "sequence_performance": sequence_performance,
            "analysis_period_days": days,
            "lender_filter": lender_id
        }
        
        return ResponseModel(
            success=True,
            data=comprehensive_data,
            message="Comprehensive analytics retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Failed to get comprehensive analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get comprehensive analytics")


@router.get("/real-time-metrics")
async def get_real_time_metrics(
    db: AsyncSession = Depends(get_db)
) -> ResponseModel[Dict[str, Any]]:
    """Get real-time metrics for the last hour"""
    try:
        analytics_service = AnalyticsService()
        
        # Get metrics for last hour
        hourly_metrics = await analytics_service.get_dashboard_metrics(db, 1)
        
        # Get recent errors (last hour)
        recent_errors = await analytics_service.get_error_analysis(db, 1)
        
        # Get integration health
        health_status = await analytics_service.get_integration_health(db)
        
        real_time_data = {
            "hourly_metrics": hourly_metrics,
            "recent_errors": recent_errors[:5],  # Top 5 recent errors
            "health_status": health_status,
            "timestamp": datetime.now().isoformat()
        }
        
        return ResponseModel(
            success=True,
            data=real_time_data,
            message="Real-time metrics retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Failed to get real-time metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get real-time metrics")


@router.get("/performance-summary")
async def get_performance_summary(
    days: int = Query(7, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db)
) -> ResponseModel[Dict[str, Any]]:
    """Get a summary of key performance indicators"""
    try:
        analytics_service = AnalyticsService()
        
        # Get basic metrics
        metrics = await analytics_service.get_dashboard_metrics(db, days)
        
        # Get top performing lenders
        lender_performance = await analytics_service.get_lender_performance(db, days)
        top_lenders = lender_performance[:3]  # Top 3 lenders
        
        # Get critical errors
        errors = await analytics_service.get_error_analysis(db, days)
        critical_errors = [e for e in errors if e['count'] > 5][:3]  # Top 3 critical errors
        
        # Get health status
        health = await analytics_service.get_integration_health(db)
        critical_health = [h for h in health if h['health'] == 'critical']
        warning_health = [h for h in health if h['health'] == 'warning']
        
        summary = {
            "period_days": days,
            "overall_metrics": metrics,
            "top_performing_lenders": top_lenders,
            "critical_errors": critical_errors,
            "health_alerts": {
                "critical_count": len(critical_health),
                "warning_count": len(warning_health),
                "critical_integrations": critical_health,
                "warning_integrations": warning_health
            },
            "summary_timestamp": datetime.now().isoformat()
        }
        
        return ResponseModel(
            success=True,
            data=summary,
            message="Performance summary retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Failed to get performance summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get performance summary")
