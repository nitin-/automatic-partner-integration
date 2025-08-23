from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from sqlalchemy.orm import joinedload
import structlog

from ..models.integration import IntegrationLog, Integration, IntegrationSequence
from ..models.lender import Lender
from ..models.field_mapping import FieldMapping

logger = structlog.get_logger()


class AnalyticsService:
    """Service for integration analytics and monitoring"""
    
    async def get_dashboard_metrics(
        self,
        db: AsyncSession,
        days: int = 30,
        lender_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get comprehensive dashboard metrics"""
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Build base query
            base_query = select(IntegrationLog).where(
                IntegrationLog.request_time >= start_date
            )
            
            if lender_id:
                base_query = base_query.join(Integration).where(
                    Integration.lender_id == lender_id
                )
            
            # Get total requests
            total_requests = await db.scalar(
                select(func.count(IntegrationLog.id)).select_from(base_query.subquery())
            )
            
            # Get successful requests
            successful_requests = await db.scalar(
                select(func.count(IntegrationLog.id))
                .select_from(base_query.subquery())
                .where(IntegrationLog.response_status < 400)
            )
            
            # Get failed requests
            failed_requests = total_requests - successful_requests
            
            # Calculate success rate
            success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
            
            # Get average response time
            avg_response_time = await db.scalar(
                select(func.avg(IntegrationLog.duration_ms))
                .select_from(base_query.subquery())
                .where(IntegrationLog.duration_ms.isnot(None))
            )
            
            # Get total leads processed
            total_leads = await db.scalar(
                select(func.count(func.distinct(IntegrationLog.lead_id)))
                .select_from(base_query.subquery())
                .where(IntegrationLog.lead_id.isnot(None))
            )
            
            return {
                'total_requests': total_requests or 0,
                'successful_requests': successful_requests or 0,
                'failed_requests': failed_requests or 0,
                'success_rate': round(success_rate, 2),
                'avg_response_time_ms': round(avg_response_time or 0, 2),
                'total_leads': total_leads or 0,
                'period_days': days
            }
            
        except Exception as e:
            logger.error(f"Failed to get dashboard metrics: {e}")
            return {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'success_rate': 0,
                'avg_response_time_ms': 0,
                'total_leads': 0,
                'period_days': days
            }
    
    async def get_lender_performance(
        self,
        db: AsyncSession,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get performance metrics by lender"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Get lenders with their integration logs
            lenders_query = select(Lender).options(
                joinedload(Lender.integrations)
            )
            lenders = (await db.execute(lenders_query)).scalars().all()
            
            lender_performance = []
            
            for lender in lenders:
                # Get logs for this lender
                logs_query = select(IntegrationLog).join(Integration).where(
                    and_(
                        Integration.lender_id == lender.id,
                        IntegrationLog.request_time >= start_date
                    )
                )
                logs = (await db.execute(logs_query)).scalars().all()
                
                if not logs:
                    continue
                
                # Calculate metrics
                total_requests = len(logs)
                successful_requests = len([log for log in logs if log.response_status and log.response_status < 400])
                failed_requests = total_requests - successful_requests
                success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
                
                avg_response_time = 0
                response_times = [log.duration_ms for log in logs if log.duration_ms]
                if response_times:
                    avg_response_time = sum(response_times) / len(response_times)
                
                total_leads = len(set([log.lead_id for log in logs if log.lead_id]))
                
                lender_performance.append({
                    'lender_id': lender.id,
                    'lender_name': lender.name,
                    'total_requests': total_requests,
                    'successful_requests': successful_requests,
                    'failed_requests': failed_requests,
                    'success_rate': round(success_rate, 2),
                    'avg_response_time_ms': round(avg_response_time, 2),
                    'total_leads': total_leads
                })
            
            # Sort by success rate descending
            lender_performance.sort(key=lambda x: x['success_rate'], reverse=True)
            
            return lender_performance
            
        except Exception as e:
            logger.error(f"Failed to get lender performance: {e}")
            return []
    
    async def get_error_analysis(
        self,
        db: AsyncSession,
        days: int = 30,
        lender_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get error analysis and trends"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Build query for failed requests
            error_query = select(IntegrationLog).where(
                and_(
                    IntegrationLog.request_time >= start_date,
                    IntegrationLog.response_status >= 400
                )
            )
            
            if lender_id:
                error_query = error_query.join(Integration).where(
                    Integration.lender_id == lender_id
                )
            
            error_logs = (await db.execute(error_query)).scalars().all()
            
            # Group errors by type
            error_counts = {}
            for log in error_logs:
                error_type = f"{log.response_status} - {log.error_code or 'Unknown'}"
                if error_type not in error_counts:
                    error_counts[error_type] = {
                        'error_type': error_type,
                        'count': 0,
                        'examples': []
                    }
                
                error_counts[error_type]['count'] += 1
                if len(error_counts[error_type]['examples']) < 3:
                    error_counts[error_type]['examples'].append({
                        'error_message': log.error_message,
                        'request_time': log.request_time.isoformat(),
                        'lender_name': log.integration.lender.name if log.integration else 'Unknown'
                    })
            
            # Convert to list and sort by count
            error_analysis = list(error_counts.values())
            error_analysis.sort(key=lambda x: x['count'], reverse=True)
            
            return error_analysis
            
        except Exception as e:
            logger.error(f"Failed to get error analysis: {e}")
            return []
    
    async def get_response_time_trends(
        self,
        db: AsyncSession,
        days: int = 30,
        lender_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get response time trends over time"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Build query
            trend_query = select(
                func.date_trunc('day', IntegrationLog.request_time).label('date'),
                func.avg(IntegrationLog.duration_ms).label('avg_response_time'),
                func.count(IntegrationLog.id).label('request_count')
            ).where(
                and_(
                    IntegrationLog.request_time >= start_date,
                    IntegrationLog.duration_ms.isnot(None)
                )
            ).group_by(
                func.date_trunc('day', IntegrationLog.request_time)
            ).order_by(
                func.date_trunc('day', IntegrationLog.request_time)
            )
            
            if lender_id:
                trend_query = trend_query.join(Integration).where(
                    Integration.lender_id == lender_id
                )
            
            trends = (await db.execute(trend_query)).all()
            
            return [
                {
                    'date': trend.date.strftime('%Y-%m-%d'),
                    'avg_response_time_ms': round(trend.avg_response_time or 0, 2),
                    'request_count': trend.request_count
                }
                for trend in trends
            ]
            
        except Exception as e:
            logger.error(f"Failed to get response time trends: {e}")
            return []
    
    async def get_integration_health(
        self,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Get health status of all integrations"""
        try:
            # Get all integrations with their recent logs
            integrations_query = select(Integration).options(
                joinedload(Integration.lender)
            )
            integrations = (await db.execute(integrations_query)).scalars().all()
            
            health_status = []
            
            for integration in integrations:
                # Get recent logs (last 24 hours)
                recent_time = datetime.now() - timedelta(hours=24)
                recent_logs_query = select(IntegrationLog).where(
                    and_(
                        IntegrationLog.integration_id == integration.id,
                        IntegrationLog.request_time >= recent_time
                    )
                )
                recent_logs = (await db.execute(recent_logs_query)).scalars().all()
                
                # Calculate health metrics
                total_recent = len(recent_logs)
                successful_recent = len([log for log in recent_logs if log.response_status and log.response_status < 400])
                
                # Get last successful and failed times
                last_successful = None
                last_failed = None
                
                for log in recent_logs:
                    if log.response_status and log.response_status < 400:
                        if not last_successful or log.request_time > last_successful:
                            last_successful = log.request_time
                    else:
                        if not last_failed or log.request_time > last_failed:
                            last_failed = log.request_time
                
                # Determine health status
                if total_recent == 0:
                    health = 'unknown'
                elif successful_recent == total_recent:
                    health = 'healthy'
                elif successful_recent > total_recent * 0.8:
                    health = 'warning'
                else:
                    health = 'critical'
                
                health_status.append({
                    'integration_id': integration.id,
                    'integration_name': integration.name,
                    'lender_name': integration.lender.name,
                    'health': health,
                    'total_recent_requests': total_recent,
                    'successful_recent_requests': successful_recent,
                    'success_rate': (successful_recent / total_recent * 100) if total_recent > 0 else 0,
                    'last_successful': last_successful.isoformat() if last_successful else None,
                    'last_failed': last_failed.isoformat() if last_failed else None,
                    'status': integration.status.value
                })
            
            # Sort by health status (critical first)
            health_order = {'critical': 0, 'warning': 1, 'healthy': 2, 'unknown': 3}
            health_status.sort(key=lambda x: health_order.get(x['health'], 4))
            
            return health_status
            
        except Exception as e:
            logger.error(f"Failed to get integration health: {e}")
            return []
    
    async def get_field_mapping_analytics(
        self,
        db: AsyncSession,
        lender_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get analytics about field mapping usage and effectiveness"""
        try:
            # Build query for field mappings
            mappings_query = select(FieldMapping)
            if lender_id:
                mappings_query = mappings_query.where(FieldMapping.lender_id == lender_id)
            
            mappings = (await db.execute(mappings_query)).scalars().all()
            
            # Analyze transformation types
            transformation_counts = {}
            active_mappings = 0
            required_mappings = 0
            
            for mapping in mappings:
                if mapping.is_active:
                    active_mappings += 1
                if mapping.is_required:
                    required_mappings += 1
                
                transform_type = mapping.transformation_type.value
                if transform_type not in transformation_counts:
                    transformation_counts[transform_type] = 0
                transformation_counts[transform_type] += 1
            
            # Get most common transformations
            common_transformations = sorted(
                transformation_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            return {
                'total_mappings': len(mappings),
                'active_mappings': active_mappings,
                'required_mappings': required_mappings,
                'transformation_distribution': transformation_counts,
                'most_common_transformations': common_transformations,
                'active_rate': (active_mappings / len(mappings) * 100) if mappings else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get field mapping analytics: {e}")
            return {
                'total_mappings': 0,
                'active_mappings': 0,
                'required_mappings': 0,
                'transformation_distribution': {},
                'most_common_transformations': [],
                'active_rate': 0
            }
    
    async def get_sequence_performance(
        self,
        db: AsyncSession,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get performance metrics for integration sequences"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Get sequences with their logs
            sequences_query = select(IntegrationSequence).options(
                joinedload(IntegrationSequence.lender)
            )
            sequences = (await db.execute(sequences_query)).scalars().all()
            
            sequence_performance = []
            
            for sequence in sequences:
                # Get logs for this sequence
                logs_query = select(IntegrationLog).where(
                    and_(
                        IntegrationLog.sequence_id == sequence.id,
                        IntegrationLog.request_time >= start_date
                    )
                )
                logs = (await db.execute(logs_query)).scalars().all()
                
                if not logs:
                    continue
                
                # Calculate sequence metrics
                total_executions = len(set([log.request_id for log in logs]))
                successful_executions = 0
                failed_executions = 0
                
                # Group by request_id to count complete sequences
                request_groups = {}
                for log in logs:
                    if log.request_id not in request_groups:
                        request_groups[log.request_id] = []
                    request_groups[log.request_id].append(log)
                
                for request_logs in request_groups.values():
                    # Check if all steps in sequence were successful
                    all_successful = all(
                        log.response_status and log.response_status < 400
                        for log in request_logs
                    )
                    
                    if all_successful:
                        successful_executions += 1
                    else:
                        failed_executions += 1
                
                avg_execution_time = 0
                execution_times = []
                
                for request_logs in request_groups.values():
                    total_time = sum(log.duration_ms or 0 for log in request_logs)
                    execution_times.append(total_time)
                
                if execution_times:
                    avg_execution_time = sum(execution_times) / len(execution_times)
                
                sequence_performance.append({
                    'sequence_id': sequence.id,
                    'sequence_name': sequence.name,
                    'lender_name': sequence.lender.name,
                    'total_executions': total_executions,
                    'successful_executions': successful_executions,
                    'failed_executions': failed_executions,
                    'success_rate': (successful_executions / total_executions * 100) if total_executions > 0 else 0,
                    'avg_execution_time_ms': round(avg_execution_time, 2),
                    'execution_mode': sequence.execution_mode,
                    'step_count': len(sequence.steps)
                })
            
            # Sort by success rate descending
            sequence_performance.sort(key=lambda x: x['success_rate'], reverse=True)
            
            return sequence_performance
            
        except Exception as e:
            logger.error(f"Failed to get sequence performance: {e}")
            return []
