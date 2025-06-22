import vt
import logging
import re
import hashlib
from urllib.parse import urlparse
from typing import Dict, List, Optional, Any
from config import Config

logger = logging.getLogger(__name__)

class ThreatIntelligenceService:
    """Service for threat intelligence using VirusTotal API"""
    
    def __init__(self):
        self.vt_client = None
        
        # Debug logging
        logger.info(f"ThreatIntelligenceService init - ENABLE_THREAT_INTELLIGENCE: {Config.ENABLE_THREAT_INTELLIGENCE}")
        logger.info(f"ThreatIntelligenceService init - VIRUSTOTAL_API_KEY configured: {bool(Config.VIRUSTOTAL_API_KEY)}")
        if Config.VIRUSTOTAL_API_KEY:
            logger.info(f"ThreatIntelligenceService init - API key length: {len(Config.VIRUSTOTAL_API_KEY)}")
        
        self.enabled = Config.ENABLE_THREAT_INTELLIGENCE and Config.VIRUSTOTAL_API_KEY
        
        if self.enabled:
            try:
                self.vt_client = vt.Client(Config.VIRUSTOTAL_API_KEY)
                logger.info("VirusTotal client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize VirusTotal client: {str(e)}")
                self.enabled = False
        else:
            reasons = []
            if not Config.ENABLE_THREAT_INTELLIGENCE:
                reasons.append("ENABLE_THREAT_INTELLIGENCE is False")
            if not Config.VIRUSTOTAL_API_KEY:
                reasons.append("VIRUSTOTAL_API_KEY is empty or None")
            logger.warning(f"Threat intelligence disabled - Reasons: {', '.join(reasons)}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.vt_client:
            self.vt_client.close()

    def analyze_urls(self, urls: List[str]) -> Dict[str, Any]:
        """Analyze URLs using VirusTotal"""
        if not self.enabled or not urls:
            return {"malicious_urls": [], "suspicious_urls": [], "url_reports": []}
        
        malicious_urls = []
        suspicious_urls = []
        url_reports = []
        
        for url in urls[:10]:  # Limit to first 10 URLs to avoid rate limits
            try:
                report = self._check_url(url)
                if report:
                    url_reports.append(report)
                    if report['malicious_count'] > 0:
                        malicious_urls.append(url)
                    elif report['suspicious_count'] > 0:
                        suspicious_urls.append(url)
            except Exception as e:
                logger.error(f"Error analyzing URL {url}: {str(e)}")
        
        return {
            "malicious_urls": malicious_urls,
            "suspicious_urls": suspicious_urls,
            "url_reports": url_reports
        }

    def analyze_domains(self, domains: List[str]) -> Dict[str, Any]:
        """Analyze domains using VirusTotal"""
        if not self.enabled or not domains:
            return {"malicious_domains": [], "suspicious_domains": [], "domain_reports": []}
        
        malicious_domains = []
        suspicious_domains = []
        domain_reports = []
        
        for domain in domains[:10]:  # Limit to first 10 domains
            try:
                report = self._check_domain(domain)
                if report:
                    domain_reports.append(report)
                    if report['malicious_count'] > 0:
                        malicious_domains.append(domain)
                    elif report['suspicious_count'] > 0:
                        suspicious_domains.append(domain)
            except Exception as e:
                logger.error(f"Error analyzing domain {domain}: {str(e)}")
        
        return {
            "malicious_domains": malicious_domains,
            "suspicious_domains": suspicious_domains,
            "domain_reports": domain_reports
        }

    def analyze_ips(self, ips: List[str]) -> Dict[str, Any]:
        """Analyze IP addresses using VirusTotal"""
        if not self.enabled or not ips:
            return {"malicious_ips": [], "suspicious_ips": [], "ip_reports": []}
        
        malicious_ips = []
        suspicious_ips = []
        ip_reports = []
        
        for ip in ips[:10]:  # Limit to first 10 IPs
            try:
                report = self._check_ip(ip)
                if report:
                    ip_reports.append(report)
                    if report['malicious_count'] > 0:
                        malicious_ips.append(ip)
                    elif report['suspicious_count'] > 0:
                        suspicious_ips.append(ip)
            except Exception as e:
                logger.error(f"Error analyzing IP {ip}: {str(e)}")
        
        return {
            "malicious_ips": malicious_ips,
            "suspicious_ips": suspicious_ips,
            "ip_reports": ip_reports
        }

    def analyze_file_hashes(self, file_data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze file hashes using VirusTotal"""
        if not self.enabled or not file_data_list:
            return {"malicious_files": [], "suspicious_files": [], "file_reports": []}
        
        malicious_files = []
        suspicious_files = []
        file_reports = []
        
        for file_data in file_data_list[:5]:  # Limit to first 5 files
            try:
                filename = file_data.get('filename', 'unknown')
                file_hash = file_data.get('hash')
                
                if not file_hash:
                    continue
                    
                report = self._check_file_hash(file_hash, filename)
                if report:
                    file_reports.append(report)
                    if report['malicious_count'] > 0:
                        malicious_files.append(filename)
                    elif report['suspicious_count'] > 0:
                        suspicious_files.append(filename)
            except Exception as e:
                logger.error(f"Error analyzing file hash: {str(e)}")
        
        return {
            "malicious_files": malicious_files,
            "suspicious_files": suspicious_files,
            "file_reports": file_reports
        }

    def _check_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Check a single URL with VirusTotal"""
        try:
            url_id = vt.url_id(url)
            url_obj = self.vt_client.get_object(f"/urls/{url_id}")
            
            stats = url_obj.last_analysis_stats
            return {
                "url": url,
                "malicious_count": stats.get("malicious", 0),
                "suspicious_count": stats.get("suspicious", 0),
                "harmless_count": stats.get("harmless", 0),
                "undetected_count": stats.get("undetected", 0),
                "scan_date": str(url_obj.last_analysis_date) if url_obj.last_analysis_date else None
            }
        except vt.APIError as e:
            if e.code == "NotFoundError":
                # URL not in VirusTotal database, submit for scanning
                try:
                    self.vt_client.scan_url(url)
                    logger.info(f"Submitted URL for scanning: {url}")
                except:
                    pass
            logger.warning(f"VirusTotal API error for URL {url}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error checking URL {url}: {str(e)}")
            return None

    def _check_domain(self, domain: str) -> Optional[Dict[str, Any]]:
        """Check a single domain with VirusTotal"""
        try:
            domain_obj = self.vt_client.get_object(f"/domains/{domain}")
            
            stats = domain_obj.last_analysis_stats
            return {
                "domain": domain,
                "malicious_count": stats.get("malicious", 0),
                "suspicious_count": stats.get("suspicious", 0),
                "harmless_count": stats.get("harmless", 0),
                "undetected_count": stats.get("undetected", 0),
                "reputation": domain_obj.reputation,
                "categories": getattr(domain_obj, 'categories', {}),
                "creation_date": str(domain_obj.creation_date) if hasattr(domain_obj, 'creation_date') and domain_obj.creation_date else None
            }
        except vt.APIError as e:
            if e.code != "NotFoundError":
                logger.warning(f"VirusTotal API error for domain {domain}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error checking domain {domain}: {str(e)}")
            return None

    def _check_ip(self, ip: str) -> Optional[Dict[str, Any]]:
        """Check a single IP address with VirusTotal"""
        try:
            ip_obj = self.vt_client.get_object(f"/ip_addresses/{ip}")
            
            stats = ip_obj.last_analysis_stats
            return {
                "ip": ip,
                "malicious_count": stats.get("malicious", 0),
                "suspicious_count": stats.get("suspicious", 0),
                "harmless_count": stats.get("harmless", 0),
                "undetected_count": stats.get("undetected", 0),
                "reputation": ip_obj.reputation,
                "country": getattr(ip_obj, 'country', 'Unknown'),
                "asn": getattr(ip_obj, 'asn', None),
                "as_owner": getattr(ip_obj, 'as_owner', 'Unknown')
            }
        except vt.APIError as e:
            if e.code != "NotFoundError":
                logger.warning(f"VirusTotal API error for IP {ip}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error checking IP {ip}: {str(e)}")
            return None

    def _check_file_hash(self, file_hash: str, filename: str) -> Optional[Dict[str, Any]]:
        """Check a file hash with VirusTotal"""
        try:
            file_obj = self.vt_client.get_object(f"/files/{file_hash}")
            
            stats = file_obj.last_analysis_stats
            return {
                "filename": filename,
                "hash": file_hash,
                "malicious_count": stats.get("malicious", 0),
                "suspicious_count": stats.get("suspicious", 0),
                "harmless_count": stats.get("harmless", 0),
                "undetected_count": stats.get("undetected", 0),
                "file_type": getattr(file_obj, 'type_description', 'Unknown'),
                "file_size": getattr(file_obj, 'size', 0),
                "scan_date": str(file_obj.last_analysis_date) if file_obj.last_analysis_date else None
            }
        except vt.APIError as e:
            if e.code != "NotFoundError":
                logger.warning(f"VirusTotal API error for file hash {file_hash}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error checking file hash {file_hash}: {str(e)}")
            return None

    @staticmethod
    def extract_urls_from_text(text: str) -> List[str]:
        """Extract URLs from email text"""
        url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
        return list(set(url_pattern.findall(text)))

    @staticmethod
    def extract_domains_from_urls(urls: List[str]) -> List[str]:
        """Extract domains from URLs"""
        domains = []
        for url in urls:
            try:
                parsed = urlparse(url)
                if parsed.netloc:
                    domains.append(parsed.netloc.lower())
            except Exception:
                continue
        return list(set(domains))

    @staticmethod
    def extract_ips_from_text(text: str) -> List[str]:
        """Extract IP addresses from email text"""
        ip_pattern = re.compile(
            r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        )
        ips = ip_pattern.findall(text)
        # Basic validation - exclude private ranges and invalid IPs
        valid_ips = []
        for ip in ips:
            parts = ip.split('.')
            if all(0 <= int(part) <= 255 for part in parts):
                # Exclude private IP ranges
                first_octet = int(parts[0])
                if not (first_octet in [10, 127] or 
                       (first_octet == 172 and 16 <= int(parts[1]) <= 31) or
                                               (first_octet == 192 and int(parts[1]) == 168)):
                    valid_ips.append(ip)
        return list(set(valid_ips))

    @staticmethod
    def extract_header_ips(email_headers: str) -> List[str]:
        """Extract IP addresses from email headers"""
        ips = []
        # Look for IPs in Received headers and other header fields
        received_pattern = re.compile(r'Received:.*?\[([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})\]', re.IGNORECASE | re.DOTALL)
        x_originating_pattern = re.compile(r'X-Originating-IP:\s*([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})', re.IGNORECASE)
        
        ips.extend(received_pattern.findall(email_headers))
        ips.extend(x_originating_pattern.findall(email_headers))
        
        # Filter out private IPs
        valid_ips = []
        for ip in ips:
            parts = ip.split('.')
            if len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts):
                first_octet = int(parts[0])
                if not (first_octet in [10, 127] or 
                       (first_octet == 172 and 16 <= int(parts[1]) <= 31) or
                       (first_octet == 192 and int(parts[1]) == 168)):
                    valid_ips.append(ip)
        return list(set(valid_ips))

    @staticmethod
    def extract_sender_domain(from_header: str) -> Optional[str]:
        """Extract sender domain from From header"""
        if not from_header:
            return None
        
        # Extract email address from "Name <email@domain.com>" format
        email_pattern = re.compile(r'<([^>]+@[^>]+)>|(\S+@\S+)')
        match = email_pattern.search(from_header)
        
        if match:
            email = match.group(1) or match.group(2)
            if '@' in email:
                return email.split('@')[1].strip().lower()
        return None

    @staticmethod
    def compute_file_hash(file_data: bytes) -> str:
        """Compute SHA256 hash of file data"""
        return hashlib.sha256(file_data).hexdigest() 