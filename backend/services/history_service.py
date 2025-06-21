from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy import func, desc, and_
import pandas as pd
import json
import logging

from models import db, AnalysisResult, AnalysisStatistics

logger = logging.getLogger(__name__)

class HistoryService:
    """Service for managing analysis history and statistics"""

    @staticmethod
    def save_analysis_result(task_id: str, analysis_result: Dict[str, Any], 
                           analysis_type: str = 'content', file_size: Optional[int] = None) -> bool:
        """Save analysis result to database"""
        try:
            # Check if result already exists
            existing = AnalysisResult.query.filter_by(task_id=task_id).first()
            if existing:
                logger.info(f"Analysis result {task_id} already exists, skipping save")
                return True

            # Create new result
            result = AnalysisResult.create_from_analysis(
                task_id=task_id,
                analysis_result=analysis_result,
                analysis_type=analysis_type,
                file_size=file_size
            )
            
            db.session.add(result)
            db.session.commit()
            
            # Update daily statistics
            HistoryService.update_daily_statistics(result)
            
            logger.info(f"Saved analysis result {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving analysis result {task_id}: {str(e)}")
            db.session.rollback()
            return False

    @staticmethod
    def update_daily_statistics(result: AnalysisResult) -> None:
        """Update daily statistics with new analysis result"""
        try:
            today = date.today()
            
            # Get or create today's statistics
            stats = AnalysisStatistics.query.filter_by(date=today).first()
            if not stats:
                stats = AnalysisStatistics(date=today)
                db.session.add(stats)
            
            # Update counts
            stats.total_analyses += 1
            
            if result.risk_level == 'high':
                stats.high_risk_count += 1
            elif result.risk_level == 'medium':
                stats.medium_risk_count += 1
            elif result.risk_level == 'low':
                stats.low_risk_count += 1
            
            if result.analysis_type == 'file':
                stats.file_analyses += 1
            else:
                stats.content_analyses += 1
            
            # Recalculate average threat score for the day
            avg_score = db.session.query(func.avg(AnalysisResult.threat_score)).filter(
                func.date(AnalysisResult.created_at) == today
            ).scalar()
            stats.avg_threat_score = float(avg_score) if avg_score else 0.0
            
            db.session.commit()
            logger.debug(f"Updated daily statistics for {today}")
            
        except Exception as e:
            logger.error(f"Error updating daily statistics: {str(e)}")
            db.session.rollback()

    @staticmethod
    def get_analysis_history(page: int = 1, per_page: int = 20, 
                           risk_level: Optional[str] = None,
                           date_from: Optional[date] = None,
                           date_to: Optional[date] = None) -> Dict[str, Any]:
        """Get paginated analysis history with filters"""
        try:
            query = AnalysisResult.query
            
            # Apply filters
            if risk_level:
                query = query.filter(AnalysisResult.risk_level == risk_level.lower())
            
            if date_from:
                query = query.filter(func.date(AnalysisResult.created_at) >= date_from)
            
            if date_to:
                query = query.filter(func.date(AnalysisResult.created_at) <= date_to)
            
            # Order by most recent first
            query = query.order_by(desc(AnalysisResult.created_at))
            
            # Paginate
            pagination = query.paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return {
                'results': [result.to_dict() for result in pagination.items],
                'total': pagination.total,
                'pages': pagination.pages,
                'current_page': page,
                'per_page': per_page,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
            
        except Exception as e:
            logger.error(f"Error getting analysis history: {str(e)}")
            return {'results': [], 'total': 0, 'pages': 0, 'current_page': 1, 'per_page': per_page}

    @staticmethod
    def get_statistics_summary() -> Dict[str, Any]:
        """Get overall statistics summary"""
        try:
            total_analyses = AnalysisResult.query.count()
            
            if total_analyses == 0:
                return {
                    'total_analyses': 0,
                    'risk_distribution': {'high': 0, 'medium': 0, 'low': 0},
                    'analysis_types': {'file': 0, 'content': 0},
                    'avg_threat_score': 0.0,
                    'recent_activity': []
                }
            
            # Risk level distribution
            risk_distribution = dict(
                db.session.query(
                    AnalysisResult.risk_level,
                    func.count(AnalysisResult.id)
                ).group_by(AnalysisResult.risk_level).all()
            )
            
            # Analysis type distribution
            type_distribution = dict(
                db.session.query(
                    AnalysisResult.analysis_type,
                    func.count(AnalysisResult.id)
                ).group_by(AnalysisResult.analysis_type).all()
            )
            
            # Average threat score
            avg_threat_score = db.session.query(
                func.avg(AnalysisResult.threat_score)
            ).scalar() or 0.0
            
            # Recent activity (last 7 days)
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            recent_stats = AnalysisStatistics.query.filter(
                AnalysisStatistics.date >= seven_days_ago.date()
            ).order_by(desc(AnalysisStatistics.date)).limit(7).all()
            
            return {
                'total_analyses': total_analyses,
                'risk_distribution': {
                    'high': risk_distribution.get('high', 0),
                    'medium': risk_distribution.get('medium', 0),
                    'low': risk_distribution.get('low', 0)
                },
                'analysis_types': {
                    'file': type_distribution.get('file', 0),
                    'content': type_distribution.get('content', 0)
                },
                'avg_threat_score': float(avg_threat_score),
                'recent_activity': [stat.to_dict() for stat in recent_stats]
            }
            
        except Exception as e:
            logger.error(f"Error getting statistics summary: {str(e)}")
            return {
                'total_analyses': 0,
                'risk_distribution': {'high': 0, 'medium': 0, 'low': 0},
                'analysis_types': {'file': 0, 'content': 0},
                'avg_threat_score': 0.0,
                'recent_activity': []
            }

    @staticmethod
    def get_trend_data(days: int = 30) -> Dict[str, Any]:
        """Get trend data for the specified number of days"""
        try:
            start_date = date.today() - timedelta(days=days)
            
            # Get daily statistics
            daily_stats = AnalysisStatistics.query.filter(
                AnalysisStatistics.date >= start_date
            ).order_by(AnalysisStatistics.date).all()
            
            # Convert to list format
            data = []
            for stat in daily_stats:
                data.append({
                    'date': stat.date.isoformat(),
                    'total_analyses': stat.total_analyses,
                    'high_risk': stat.high_risk_count,
                    'medium_risk': stat.medium_risk_count,
                    'low_risk': stat.low_risk_count,
                    'avg_threat_score': stat.avg_threat_score
                })
            
            # Fill in missing dates with zero values
            all_dates = []
            current_date = start_date
            while current_date <= date.today():
                all_dates.append(current_date.isoformat())
                current_date += timedelta(days=1)
            
            # Create a complete dataset
            date_map = {item['date']: item for item in data}
            complete_data = []
            
            for date_str in all_dates:
                if date_str in date_map:
                    complete_data.append(date_map[date_str])
                else:
                    complete_data.append({
                        'date': date_str,
                        'total_analyses': 0,
                        'high_risk': 0,
                        'medium_risk': 0,
                        'low_risk': 0,
                        'avg_threat_score': 0.0
                    })
            
            return {
                'trend_data': complete_data,
                'period_days': days,
                'start_date': start_date.isoformat(),
                'end_date': date.today().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting trend data: {str(e)}")
            return {
                'trend_data': [],
                'period_days': days,
                'start_date': start_date.isoformat(),
                'end_date': date.today().isoformat()
            }

    @staticmethod
    def export_data(format_type: str = 'json', 
                   date_from: Optional[date] = None,
                   date_to: Optional[date] = None) -> Dict[str, Any]:
        """Export analysis data in specified format"""
        try:
            query = AnalysisResult.query
            
            # Apply date filters
            if date_from:
                query = query.filter(func.date(AnalysisResult.created_at) >= date_from)
            
            if date_to:
                query = query.filter(func.date(AnalysisResult.created_at) <= date_to)
            
            results = query.order_by(desc(AnalysisResult.created_at)).all()
            
            if format_type.lower() == 'csv':
                # Convert to pandas DataFrame for CSV export
                data = []
                for result in results:
                    data.append({
                        'id': result.id,
                        'task_id': result.task_id,
                        'subject': result.subject,
                        'sender': result.sender,
                        'threat_score': result.threat_score,
                        'risk_level': result.risk_level,
                        'analysis_type': result.analysis_type,
                        'created_at': result.created_at.isoformat(),
                        'file_size': result.file_size
                    })
                
                df = pd.DataFrame(data)
                csv_data = df.to_csv(index=False)
                
                return {
                    'format': 'csv',
                    'data': csv_data,
                    'filename': f'phishguard_export_{date.today().isoformat()}.csv',
                    'count': len(results)
                }
            
            else:  # JSON format
                data = [result.to_dict() for result in results]
                
                return {
                    'format': 'json',
                    'data': data,
                    'filename': f'phishguard_export_{date.today().isoformat()}.json',
                    'count': len(results)
                }
                
        except Exception as e:
            logger.error(f"Error exporting data: {str(e)}")
            return {
                'format': format_type,
                'data': None,
                'error': str(e),
                'count': 0
            }

    @staticmethod
    def get_analysis_detail(task_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed analysis result by task ID"""
        try:
            result = AnalysisResult.query.filter_by(task_id=task_id).first()
            return result.to_dict() if result else None
            
        except Exception as e:
            logger.error(f"Error getting analysis detail for {task_id}: {str(e)}")
            return None

    @staticmethod
    def delete_old_results(days_to_keep: int = 90) -> int:
        """Delete analysis results older than specified days"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            old_results = AnalysisResult.query.filter(
                AnalysisResult.created_at < cutoff_date
            )
            
            count = old_results.count()
            old_results.delete()
            
            # Also delete old statistics
            old_stats = AnalysisStatistics.query.filter(
                AnalysisStatistics.date < cutoff_date.date()
            )
            old_stats.delete()
            
            db.session.commit()
            
            logger.info(f"Deleted {count} old analysis results")
            return count
            
        except Exception as e:
            logger.error(f"Error deleting old results: {str(e)}")
            db.session.rollback()
            return 0 