from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class AnalysisResult(db.Model):
    """Model for storing email analysis results"""
    __tablename__ = 'analysis_results'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    
    # Email metadata
    subject = db.Column(db.Text)
    sender = db.Column(db.String(255))
    timestamp = db.Column(db.String(255))  # Email timestamp from headers
    
    # Analysis results
    threat_score = db.Column(db.Float, nullable=False)
    risk_level = db.Column(db.String(50), nullable=False)
    
    # Detailed analysis (stored as JSON)
    header_analysis = db.Column(db.Text)  # JSON string
    content_analysis = db.Column(db.Text)  # JSON string
    link_analysis = db.Column(db.Text)  # JSON string
    attachment_analysis = db.Column(db.Text)  # JSON string
    recommendations = db.Column(db.Text)  # JSON string
    
    # Analysis metadata
    analysis_type = db.Column(db.String(50))  # 'file' or 'content'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    file_size = db.Column(db.Integer)  # For file uploads
    
    def __repr__(self):
        return f'<AnalysisResult {self.task_id}>'
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'subject': self.subject,
            'sender': self.sender,
            'timestamp': self.timestamp,
            'threat_score': self.threat_score,
            'risk_level': self.risk_level,
            'header_analysis': json.loads(self.header_analysis) if self.header_analysis else {},
            'content_analysis': json.loads(self.content_analysis) if self.content_analysis else {},
            'link_analysis': json.loads(self.link_analysis) if self.link_analysis else {},
            'attachment_analysis': json.loads(self.attachment_analysis) if self.attachment_analysis else {},
            'recommendations': json.loads(self.recommendations) if self.recommendations else [],
            'analysis_type': self.analysis_type,
            'created_at': self.created_at.isoformat(),
            'file_size': self.file_size
        }
    
    @classmethod
    def create_from_analysis(cls, task_id, analysis_result, analysis_type='content', file_size=None):
        """Create a new analysis result record"""
        result = cls(
            task_id=task_id,
            subject=analysis_result.get('subject', 'Unknown'),
            sender=analysis_result.get('sender', 'Unknown'),
            timestamp=analysis_result.get('timestamp', 'Unknown'),
            threat_score=analysis_result.get('threat_score', 0.0),
            risk_level=analysis_result.get('risk_level', 'unknown'),
            header_analysis=json.dumps(analysis_result.get('header_analysis', {})),
            content_analysis=json.dumps(analysis_result.get('content_analysis', {})),
            link_analysis=json.dumps(analysis_result.get('link_analysis', {})),
            attachment_analysis=json.dumps(analysis_result.get('attachment_analysis', {})),
            recommendations=json.dumps(analysis_result.get('recommendations', [])),
            analysis_type=analysis_type,
            file_size=file_size
        )
        return result


class AnalysisStatistics(db.Model):
    """Model for storing aggregated statistics"""
    __tablename__ = 'analysis_statistics'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    
    # Daily counts
    total_analyses = db.Column(db.Integer, default=0)
    high_risk_count = db.Column(db.Integer, default=0)
    medium_risk_count = db.Column(db.Integer, default=0)
    low_risk_count = db.Column(db.Integer, default=0)
    
    # Analysis types
    file_analyses = db.Column(db.Integer, default=0)
    content_analyses = db.Column(db.Integer, default=0)
    
    # Average threat score
    avg_threat_score = db.Column(db.Float, default=0.0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<AnalysisStatistics {self.date}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'total_analyses': self.total_analyses,
            'high_risk_count': self.high_risk_count,
            'medium_risk_count': self.medium_risk_count,
            'low_risk_count': self.low_risk_count,
            'file_analyses': self.file_analyses,
            'content_analyses': self.content_analyses,
            'avg_threat_score': self.avg_threat_score,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        } 