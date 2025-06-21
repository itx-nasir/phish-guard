from flask_pymongo import PyMongo
from datetime import datetime, date, timedelta
import json
from bson import ObjectId
from typing import Dict, List, Any, Optional

mongo = PyMongo()

class MongoJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for MongoDB ObjectId and datetime"""
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, date):
            return obj.isoformat()
        return super().default(obj)

class AnalysisResult:
    """MongoDB model for storing email analysis results"""
    
    collection_name = 'analysis_results'
    
    @staticmethod
    def create_from_analysis(task_id: str, analysis_result: Dict[str, Any], 
                           analysis_type: str = 'content', file_size: Optional[int] = None) -> Dict[str, Any]:
        """Create a new analysis result document"""
        document = {
            'task_id': task_id,
            'subject': analysis_result.get('subject', 'Unknown'),
            'sender': analysis_result.get('sender', 'Unknown'),
            'timestamp': analysis_result.get('timestamp', 'Unknown'),
            'threat_score': analysis_result.get('threat_score', 0.0),
            'risk_level': analysis_result.get('risk_level', 'unknown'),
            'header_analysis': analysis_result.get('header_analysis', {}),
            'content_analysis': analysis_result.get('content_analysis', {}),
            'link_analysis': analysis_result.get('link_analysis', {}),
            'attachment_analysis': analysis_result.get('attachment_analysis', {}),
            'recommendations': analysis_result.get('recommendations', []),
            'analysis_type': analysis_type,
            'file_size': file_size,
            'created_at': datetime.utcnow()
        }
        return document
    
    @staticmethod
    def insert(document: Dict[str, Any]) -> str:
        """Insert a new analysis result document"""
        result = mongo.db[AnalysisResult.collection_name].insert_one(document)
        return str(result.inserted_id)
    
    @staticmethod
    def find_by_task_id(task_id: str) -> Optional[Dict[str, Any]]:
        """Find analysis result by task_id"""
        result = mongo.db[AnalysisResult.collection_name].find_one({'task_id': task_id})
        if result:
            result['_id'] = str(result['_id'])
        return result
    
    @staticmethod
    def find_paginated(page: int = 1, per_page: int = 20, 
                      risk_level: Optional[str] = None,
                      date_from: Optional[date] = None,
                      date_to: Optional[date] = None) -> Dict[str, Any]:
        """Find analysis results with pagination and filters"""
        
        # Build query
        query = {}
        
        if risk_level:
            query['risk_level'] = risk_level.lower()
        
        if date_from or date_to:
            date_query = {}
            if date_from:
                date_query['$gte'] = datetime.combine(date_from, datetime.min.time())
            if date_to:
                date_query['$lte'] = datetime.combine(date_to, datetime.max.time())
            query['created_at'] = date_query
        
        # Get total count
        total = mongo.db[AnalysisResult.collection_name].count_documents(query)
        
        # Calculate pagination
        skip = (page - 1) * per_page
        pages = (total + per_page - 1) // per_page
        
        # Get results
        cursor = mongo.db[AnalysisResult.collection_name].find(query)\
            .sort('created_at', -1)\
            .skip(skip)\
            .limit(per_page)
        
        results = []
        for doc in cursor:
            doc['_id'] = str(doc['_id'])
            doc['id'] = doc['_id']  # For compatibility
            results.append(doc)
        
        return {
            'results': results,
            'total': total,
            'pages': pages,
            'current_page': page,
            'per_page': per_page,
            'has_next': page < pages,
            'has_prev': page > 1
        }
    
    @staticmethod
    def get_statistics() -> Dict[str, Any]:
        """Get overall statistics"""
        collection = mongo.db[AnalysisResult.collection_name]
        
        # Total analyses
        total_analyses = collection.count_documents({})
        
        if total_analyses == 0:
            return {
                'total_analyses': 0,
                'risk_distribution': {'high': 0, 'medium': 0, 'low': 0},
                'analysis_types': {'file': 0, 'content': 0},
                'avg_threat_score': 0.0
            }
        
        # Risk level distribution
        risk_pipeline = [
            {'$group': {'_id': '$risk_level', 'count': {'$sum': 1}}}
        ]
        risk_results = list(collection.aggregate(risk_pipeline))
        risk_distribution = {item['_id']: item['count'] for item in risk_results}
        
        # Analysis type distribution
        type_pipeline = [
            {'$group': {'_id': '$analysis_type', 'count': {'$sum': 1}}}
        ]
        type_results = list(collection.aggregate(type_pipeline))
        type_distribution = {item['_id']: item['count'] for item in type_results}
        
        # Average threat score
        avg_pipeline = [
            {'$group': {'_id': None, 'avg_score': {'$avg': '$threat_score'}}}
        ]
        avg_results = list(collection.aggregate(avg_pipeline))
        avg_threat_score = avg_results[0]['avg_score'] if avg_results else 0.0
        
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
            'avg_threat_score': float(avg_threat_score)
        }
    
    @staticmethod
    def get_trend_data(days: int = 30) -> List[Dict[str, Any]]:
        """Get trend data for the specified number of days"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        pipeline = [
            {'$match': {'created_at': {'$gte': start_date}}},
            {'$group': {
                '_id': {
                    'year': {'$year': '$created_at'},
                    'month': {'$month': '$created_at'},
                    'day': {'$dayOfMonth': '$created_at'}
                },
                'total_analyses': {'$sum': 1},
                'high_risk': {'$sum': {'$cond': [{'$eq': ['$risk_level', 'high']}, 1, 0]}},
                'medium_risk': {'$sum': {'$cond': [{'$eq': ['$risk_level', 'medium']}, 1, 0]}},
                'low_risk': {'$sum': {'$cond': [{'$eq': ['$risk_level', 'low']}, 1, 0]}},
                'avg_threat_score': {'$avg': '$threat_score'}
            }},
            {'$sort': {'_id': 1}}
        ]
        
        results = list(mongo.db[AnalysisResult.collection_name].aggregate(pipeline))
        
        # Convert to the expected format
        trend_data = []
        for result in results:
            date_obj = date(result['_id']['year'], result['_id']['month'], result['_id']['day'])
            trend_data.append({
                'date': date_obj.isoformat(),
                'total_analyses': result['total_analyses'],
                'high_risk': result['high_risk'],
                'medium_risk': result['medium_risk'],
                'low_risk': result['low_risk'],
                'avg_threat_score': result['avg_threat_score'] or 0.0
            })
        
        # Fill in missing dates with zero values
        all_dates = []
        current_date = start_date.date()
        end_date = datetime.utcnow().date()
        
        while current_date <= end_date:
            all_dates.append(current_date.isoformat())
            current_date += timedelta(days=1)
        
        # Create a complete dataset
        date_map = {item['date']: item for item in trend_data}
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
        
        return complete_data
    
    @staticmethod
    def export_data(date_from: Optional[date] = None, date_to: Optional[date] = None) -> List[Dict[str, Any]]:
        """Export analysis data"""
        query = {}
        
        if date_from or date_to:
            date_query = {}
            if date_from:
                date_query['$gte'] = datetime.combine(date_from, datetime.min.time())
            if date_to:
                date_query['$lte'] = datetime.combine(date_to, datetime.max.time())
            query['created_at'] = date_query
        
        cursor = mongo.db[AnalysisResult.collection_name].find(query).sort('created_at', -1)
        
        results = []
        for doc in cursor:
            doc['_id'] = str(doc['_id'])
            doc['id'] = doc['_id']
            results.append(doc)
        
        return results
    
    @staticmethod
    def delete_old_results(days_to_keep: int = 90) -> int:
        """Delete analysis results older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        result = mongo.db[AnalysisResult.collection_name].delete_many({
            'created_at': {'$lt': cutoff_date}
        })
        
        return result.deleted_count


class AnalysisStatistics:
    """MongoDB model for storing aggregated statistics (optional - can be computed on-demand)"""
    
    collection_name = 'analysis_statistics'
    
    @staticmethod
    def update_daily_stats(analysis_result: Dict[str, Any]) -> None:
        """Update daily statistics with new analysis result"""
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        # Get existing stats for today
        existing_stats = mongo.db[AnalysisStatistics.collection_name].find_one({
            'date': today.isoformat()
        })
        
        if existing_stats:
            # Update existing stats
            update_data = {
                '$inc': {
                    'total_analyses': 1,
                    f"{analysis_result['risk_level']}_risk_count": 1,
                    f"{analysis_result['analysis_type']}_analyses": 1
                },
                '$set': {
                    'updated_at': datetime.utcnow()
                }
            }
            mongo.db[AnalysisStatistics.collection_name].update_one(
                {'date': today.isoformat()},
                update_data
            )
        else:
            # Create new stats
            stats_doc = {
                'date': today.isoformat(),
                'total_analyses': 1,
                'high_risk_count': 1 if analysis_result['risk_level'] == 'high' else 0,
                'medium_risk_count': 1 if analysis_result['risk_level'] == 'medium' else 0,
                'low_risk_count': 1 if analysis_result['risk_level'] == 'low' else 0,
                'file_analyses': 1 if analysis_result['analysis_type'] == 'file' else 0,
                'content_analyses': 1 if analysis_result['analysis_type'] == 'content' else 0,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            mongo.db[AnalysisStatistics.collection_name].insert_one(stats_doc)
        
        # Recalculate average threat score for today
        pipeline = [
            {'$match': {'created_at': {'$gte': today_start, '$lte': today_end}}},
            {'$group': {'_id': None, 'avg_score': {'$avg': '$threat_score'}}}
        ]
        
        avg_results = list(mongo.db[AnalysisResult.collection_name].aggregate(pipeline))
        avg_score = avg_results[0]['avg_score'] if avg_results else 0.0
        
        mongo.db[AnalysisStatistics.collection_name].update_one(
            {'date': today.isoformat()},
            {'$set': {'avg_threat_score': avg_score}}
        ) 