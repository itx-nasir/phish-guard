from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
import json
import logging

from models import mongo, AnalysisResult, AnalysisStatistics

logger = logging.getLogger(__name__)

class HistoryService:
    """Service for managing analysis history and statistics"""

    @staticmethod
    def save_analysis_result(task_id: str, analysis_result: Dict[str, Any], 
                           analysis_type: str = 'content', file_size: Optional[int] = None) -> bool:
        """Save analysis result to database"""
        try:
            # Check if result already exists
            existing = AnalysisResult.find_by_task_id(task_id)
            if existing:
                logger.info(f"Analysis result {task_id} already exists, skipping save")
                return True

            # Create new result document
            document = AnalysisResult.create_from_analysis(
                task_id=task_id,
                analysis_result=analysis_result,
                analysis_type=analysis_type,
                file_size=file_size
            )
            
            # Insert into MongoDB
            AnalysisResult.insert(document)
            
            # Update daily statistics
            AnalysisStatistics.update_daily_stats(document)
            
            logger.info(f"Saved analysis result {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving analysis result {task_id}: {str(e)}")
            return False

    @staticmethod
    def update_daily_statistics(result: Dict[str, Any]) -> None:
        """Update daily statistics with new analysis result"""
        try:
            # This is now handled by AnalysisStatistics.update_daily_stats
            # in the save_analysis_result method
            pass
            
        except Exception as e:
            logger.error(f"Error updating daily statistics: {str(e)}")

    @staticmethod
    def get_analysis_history(page: int = 1, per_page: int = 20, 
                           risk_level: Optional[str] = None,
                           date_from: Optional[date] = None,
                           date_to: Optional[date] = None) -> Dict[str, Any]:
        """Get paginated analysis history with filters"""
        try:
            return AnalysisResult.find_paginated(
                page=page,
                per_page=per_page,
                risk_level=risk_level,
                date_from=date_from,
                date_to=date_to
            )
            
        except Exception as e:
            logger.error(f"Error getting analysis history: {str(e)}")
            return {'results': [], 'total': 0, 'pages': 0, 'current_page': 1, 'per_page': per_page}

    @staticmethod
    def get_statistics_summary() -> Dict[str, Any]:
        """Get overall statistics summary"""
        try:
            stats = AnalysisResult.get_statistics()
            
            # Add recent activity - get last 7 days of stats
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            recent_data = AnalysisResult.get_trend_data(days=7)
            
            stats['recent_activity'] = recent_data
            return stats
            
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
            
            # Get trend data from MongoDB
            trend_data = AnalysisResult.get_trend_data(days=days)
            
            return {
                'trend_data': trend_data,
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
            # Get data from MongoDB
            results = AnalysisResult.export_data(date_from=date_from, date_to=date_to)
            
            if format_type.lower() == 'csv':
                # Convert to pandas DataFrame for CSV export
                data = []
                for result in results:
                    data.append({
                        'id': result.get('id', result.get('_id')),
                        'task_id': result.get('task_id'),
                        'subject': result.get('subject'),
                        'sender': result.get('sender'),
                        'threat_score': result.get('threat_score'),
                        'risk_level': result.get('risk_level'),
                        'analysis_type': result.get('analysis_type'),
                        'created_at': result.get('created_at').isoformat() if isinstance(result.get('created_at'), datetime) else result.get('created_at'),
                        'file_size': result.get('file_size')
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
                return {
                    'format': 'json',
                    'data': results,
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
            result = AnalysisResult.find_by_task_id(task_id)
            return result
            
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