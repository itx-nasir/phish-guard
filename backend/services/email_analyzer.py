import email
from email import policy
from email.parser import BytesParser, Parser
from bs4 import BeautifulSoup
import re
import dns.resolver
import requests
from urllib.parse import urlparse
from typing import Dict, List, Tuple, Any, Optional
import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class AnalysisResult:
    """Data class for analysis results"""
    threat_score: float
    risk_level: str
    header_analysis: Dict[str, Any]
    content_analysis: Dict[str, Any]
    link_analysis: Dict[str, Any]
    attachment_analysis: Dict[str, Any]
    recommendations: List[str]
    timestamp: str
    subject: str
    sender: str
    error: Optional[str] = None

class EmailAnalysisError(Exception):
    """Custom exception for email analysis errors"""
    pass

class EmailParsingError(EmailAnalysisError):
    """Exception for email parsing errors"""
    pass

class FileValidationError(EmailAnalysisError):
    """Exception for file validation errors"""
    pass

class EmailAnalyzer:
    """Service for analyzing emails for phishing indicators"""
    
    # Configuration constants
    MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'.eml'}
    
    # Suspicious patterns configuration
    SUSPICIOUS_KEYWORDS = {
        'urgent', 'account suspended', 'verify your account', 'click here',
        'update your information', 'password expired', 'security alert',
        'unusual activity', 'limited time', 'act now', 'immediate action',
        'congratulations', 'winner', 'lottery', 'prize', 'free money'
    }
    
    URGENCY_PATTERNS = [
        r'urgent',
        r'immediate action required',
        r'account.*suspend',
        r'within \d+ hours?',
        r'expires? (?:today|soon)',
        r'act now',
        r'time.?sensitive'
    ]
    
    SUSPICIOUS_ATTACHMENTS = {
        'exe', 'bat', 'cmd', 'scr', 'js', 'vbs', 'ps1',
        'wsf', 'msi', 'jar', 'reg', 'com', 'pif', 'zip'
    }

    def __init__(self):
        pass

    @staticmethod
    def analyze_content(content: str) -> Dict[str, Any]:
        """Analyze email content for phishing indicators"""
        if not content or not content.strip():
            logger.warning("Empty content provided for analysis")
            return {
                'error': 'Empty email content provided',
                'threat_score': 0.0,
                'risk_level': 'unknown',
                'message': 'No content to analyze'
            }
        
        try:
            # Parse email content with better error handling
            try:
                email_message = Parser(policy=policy.default).parsestr(content)
            except Exception as e:
                logger.error(f"Failed to parse email content: {str(e)}")
                raise EmailParsingError(f"Invalid email format: {str(e)}")
            
            # Create analyzer instance
            analyzer = EmailAnalyzer()
            
            # Perform various analyses with error handling
            try:
                header_analysis = analyzer._analyze_headers(email_message)
                content_analysis = analyzer._analyze_body(email_message)
                link_analysis = analyzer._analyze_links(email_message)
                attachment_analysis = analyzer._analyze_attachments(email_message)
            except Exception as e:
                logger.error(f"Error during analysis components: {str(e)}")
                return {
                    'error': f'Analysis failed: {str(e)}',
                    'threat_score': 0.0,
                    'risk_level': 'unknown',
                    'message': 'Partial analysis failure'
                }
            
            # Calculate overall threat score
            threat_score = analyzer._calculate_threat_score(
                header_analysis,
                content_analysis,
                link_analysis,
                attachment_analysis
            )
            
            result = {
                'threat_score': threat_score,
                'risk_level': analyzer._get_risk_level(threat_score),
                'header_analysis': header_analysis,
                'content_analysis': content_analysis,
                'link_analysis': link_analysis,
                'attachment_analysis': attachment_analysis,
                'recommendations': analyzer._generate_recommendations(
                    header_analysis,
                    content_analysis,
                    link_analysis,
                    attachment_analysis
                ),
                'timestamp': str(email_message.get('Date', 'Unknown')),
                'subject': str(email_message.get('Subject', 'No Subject')),
                'sender': str(email_message.get('From', 'Unknown'))
            }
            
            logger.info(f"Email analysis completed. Threat score: {threat_score:.2f}, Risk: {result['risk_level']}")
            return result
            
        except EmailParsingError:
            # Re-raise parsing errors
            raise
        except Exception as e:
            logger.error(f"Unexpected error analyzing email content: {str(e)}", exc_info=True)
            return {
                'error': f'Internal analysis error: {str(e)}',
                'threat_score': 0.0,
                'risk_level': 'unknown',
                'message': 'Analysis failed due to unexpected error'
            }

    @staticmethod
    def analyze_file(file_path: str) -> Dict[str, Any]:
        """Analyze email file for phishing indicators"""
        try:
            # Validate file existence and permissions
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            if not os.access(file_path, os.R_OK):
                raise PermissionError(f"Cannot read file: {file_path}")
            
            # Validate file size
            file_size = os.path.getsize(file_path)
            if file_size > EmailAnalyzer.MAX_FILE_SIZE:
                raise FileValidationError(f"File too large: {file_size} bytes. Maximum allowed: {EmailAnalyzer.MAX_FILE_SIZE} bytes")
            
            if file_size == 0:
                raise FileValidationError("File is empty")
            
            # Validate file extension
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext not in EmailAnalyzer.ALLOWED_EXTENSIONS:
                raise FileValidationError(f"Invalid file extension: {file_ext}. Allowed: {EmailAnalyzer.ALLOWED_EXTENSIONS}")
            
            # Read and parse file
            try:
                with open(file_path, 'rb') as f:
                    email_message = BytesParser(policy=policy.default).parse(f)
            except UnicodeDecodeError as e:
                logger.error(f"Unicode decode error reading file {file_path}: {str(e)}")
                raise EmailParsingError(f"File encoding error: {str(e)}")
            except Exception as e:
                logger.error(f"Error reading email file {file_path}: {str(e)}")
                raise EmailParsingError(f"Failed to parse email file: {str(e)}")
            
            # Analyze the parsed email
            result = EmailAnalyzer.analyze_content(email_message.as_string())
            logger.info(f"File analysis completed for: {os.path.basename(file_path)}")
            return result
            
        except (FileNotFoundError, PermissionError, FileValidationError, EmailParsingError):
            # Re-raise known exceptions
            raise
        except Exception as e:
            logger.error(f"Unexpected error analyzing email file {file_path}: {str(e)}", exc_info=True)
            return {
                'error': f'File analysis failed: {str(e)}',
                'threat_score': 0.0,
                'risk_level': 'unknown',
                'message': 'File analysis failed due to unexpected error'
            }

    def _analyze_headers(self, email_message: email.message.Message) -> Dict[str, Any]:
        """Analyze email headers for suspicious patterns"""
        results = {
            'suspicious_patterns': [],
            'authentication_results': {},
            'risk_indicators': []
        }
        
        try:
            # Check SPF
            auth_results = email_message.get('Authentication-Results', '')
            if 'spf=pass' not in auth_results.lower() and auth_results:
                results['risk_indicators'].append('SPF verification failed')
                results['authentication_results']['spf'] = 'failed'
            elif 'spf=pass' in auth_results.lower():
                results['authentication_results']['spf'] = 'passed'
            
            # Check DKIM
            if 'dkim=pass' not in auth_results.lower() and auth_results:
                results['risk_indicators'].append('DKIM verification failed')
                results['authentication_results']['dkim'] = 'failed'
            elif 'dkim=pass' in auth_results.lower():
                results['authentication_results']['dkim'] = 'passed'
            
            # Check for display name spoofing
            from_header = email_message.get('From', '')
            if self._check_display_name_spoofing(from_header):
                results['suspicious_patterns'].append('Possible display name spoofing')
            
            # Check for mismatched sender domains
            reply_to = email_message.get('Reply-To', '')
            if self._check_mismatched_domains(from_header, reply_to):
                results['suspicious_patterns'].append('Mismatched sender domains')
                
        except Exception as e:
            logger.error(f"Error in header analysis: {str(e)}")
            results['error'] = str(e)
        
        return results

    def _analyze_body(self, email_message: email.message.Message) -> Dict[str, Any]:
        """Analyze email body for suspicious content"""
        results = {
            'suspicious_keywords': [],
            'urgency_indicators': [],
            'sentiment_analysis': {}
        }
        
        # Get email body
        body = self._get_email_body(email_message)
        
        # Check for suspicious keywords
        for keyword in self.SUSPICIOUS_KEYWORDS:
            if keyword.lower() in body.lower():
                results['suspicious_keywords'].append(keyword)
        
        # Check for urgency indicators
        for pattern in self.URGENCY_PATTERNS:
            if re.search(pattern, body.lower()):
                results['urgency_indicators'].append(pattern)
        
        return results

    def _analyze_links(self, email_message: email.message.Message) -> Dict[str, Any]:
        """Analyze links in email body"""
        results = {
            'suspicious_links': [],
            'redirects': [],
            'malicious_domains': []
        }
        
        body = self._get_email_body(email_message)
        soup = BeautifulSoup(body, 'html.parser')
        
        # Extract all links
        links = [a.get('href') for a in soup.find_all('a', href=True)]
        
        for link in links:
            if not link:
                continue
                
            # Check for URL redirects
            if self._check_redirect(link):
                results['redirects'].append(link)
            
            # Check domain reputation
            try:
                domain = urlparse(link).netloc
                if domain and self._check_domain_reputation(domain):
                    results['malicious_domains'].append(domain)
            except:
                pass
            
            # Check for deceptive URLs
            if self._check_deceptive_url(link):
                results['suspicious_links'].append(link)
        
        return results

    def _analyze_attachments(self, email_message: email.message.Message) -> Dict[str, Any]:
        """Analyze email attachments"""
        results = {
            'suspicious_attachments': [],
            'file_types': []
        }
        
        for part in email_message.walk():
            if part.get_content_maintype() == 'multipart':
                continue
                
            filename = part.get_filename()
            if filename:
                # Check file extension
                if self._is_suspicious_attachment(filename):
                    results['suspicious_attachments'].append(filename)
                
                # Record file type
                ext = filename.split('.')[-1].lower()
                results['file_types'].append(ext)
        
        return results

    def _calculate_threat_score(self, *analyses) -> float:
        """Calculate overall threat score based on all analyses"""
        score = 0.0
        weights = {
            'header': 0.3,
            'content': 0.2,
            'link': 0.3,
            'attachment': 0.2
        }
        
        # Header analysis
        if analyses[0]['risk_indicators']:
            score += len(analyses[0]['risk_indicators']) * weights['header']
        
        # Content analysis
        if analyses[1]['suspicious_keywords']:
            score += len(analyses[1]['suspicious_keywords']) * weights['content']
        
        # Link analysis
        link_score = (
            len(analyses[2]['suspicious_links']) +
            len(analyses[2]['malicious_domains']) * 2
        ) * weights['link']
        score += link_score
        
        # Attachment analysis
        if analyses[3]['suspicious_attachments']:
            score += len(analyses[3]['suspicious_attachments']) * weights['attachment']
        
        return min(score, 1.0)  # Normalize to 0-1 range

    def _get_risk_level(self, threat_score: float) -> str:
        """Convert threat score to risk level"""
        phishing_score_threshold = 0.7
        if threat_score >= phishing_score_threshold:
            return 'high'
        elif threat_score >= phishing_score_threshold * 0.5:
            return 'medium'
        return 'low'

    def _generate_recommendations(self, *analyses) -> List[str]:
        """Generate user recommendations based on analysis results"""
        recommendations = []
        
        # Header-based recommendations
        if analyses[0]['risk_indicators']:
            recommendations.append(
                "The email failed security verification checks. Be extremely cautious."
            )
        
        # Content-based recommendations
        if analyses[1]['suspicious_keywords']:
            recommendations.append(
                "This email contains common phishing phrases. Verify any requests through official channels."
            )
        
        # Link-based recommendations
        if analyses[2]['suspicious_links'] or analyses[2]['malicious_domains']:
            recommendations.append(
                "Do not click on any links. If necessary, manually type the URL in your browser."
            )
        
        # Attachment-based recommendations
        if analyses[3]['suspicious_attachments']:
            recommendations.append(
                "This email contains potentially dangerous attachments. Do not open them."
            )
        
        if not recommendations:
            recommendations.append("This email appears to be safe, but always remain vigilant.")
        
        return recommendations

    def _get_email_body(self, email_message: email.message.Message) -> str:
        """Extract email body content"""
        body = ""
        try:
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        payload = part.get_payload(decode=True)
                        if payload:
                            body += payload.decode('utf-8', errors='ignore')
                    elif part.get_content_type() == "text/html":
                        payload = part.get_payload(decode=True)
                        if payload:
                            soup = BeautifulSoup(payload.decode('utf-8', errors='ignore'), 'html.parser')
                            body += soup.get_text()
            else:
                payload = email_message.get_payload(decode=True)
                if payload:
                    body = payload.decode('utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"Error extracting email body: {str(e)}")
            body = ""
        return body

    @staticmethod
    def _check_display_name_spoofing(from_header: str) -> bool:
        """Check for display name spoofing"""
        # Simple check for common spoofing patterns
        suspicious_patterns = ['paypal', 'amazon', 'microsoft', 'google', 'apple', 'bank']
        from_lower = from_header.lower()
        
        for pattern in suspicious_patterns:
            if pattern in from_lower and not f'@{pattern}' in from_lower:
                return True
        return False

    @staticmethod
    def _check_mismatched_domains(from_header: str, reply_to: str) -> bool:
        """Check for mismatched sender domains"""
        if not reply_to:
            return False
            
        try:
            from_domain = from_header.split('@')[-1].strip('>')
            reply_domain = reply_to.split('@')[-1].strip('>')
            return from_domain != reply_domain
        except:
            return False

    @staticmethod
    def _check_redirect(url: str) -> bool:
        """Check if URL contains redirects"""
        redirect_indicators = ['redirect', 'redir', 'r.php', 'goto', 'link.php']
        return any(indicator in url.lower() for indicator in redirect_indicators)

    @staticmethod
    def _check_domain_reputation(domain: str) -> bool:
        """Check domain reputation using simple heuristics"""
        # Simple heuristic-based check (in production, use proper threat intelligence)
        suspicious_tlds = ['.tk', '.ml', '.ga', '.cf']
        suspicious_patterns = ['secure-', 'verify-', 'account-', 'update-']
        
        if any(domain.endswith(tld) for tld in suspicious_tlds):
            return True
        
        if any(pattern in domain.lower() for pattern in suspicious_patterns):
            return True
            
        return False

    @staticmethod
    def _check_deceptive_url(url: str) -> bool:
        """Check for deceptive URLs"""
        deceptive_patterns = [
            'bit.ly', 'tinyurl.com', 'goo.gl', 't.co',  # URL shorteners
            'phishing', 'malware', 'suspicious'
        ]
        return any(pattern in url.lower() for pattern in deceptive_patterns)

    @staticmethod
    def _is_suspicious_attachment(filename: str) -> bool:
        """Check if attachment is potentially dangerous"""
        if not filename or '.' not in filename:
            return False
        
        extension = filename.split('.')[-1].lower()
        return extension in EmailAnalyzer.SUSPICIOUS_ATTACHMENTS


# Note: Celery tasks are now defined in app.py to avoid circular imports