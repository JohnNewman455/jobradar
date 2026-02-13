"""
Base Scraper Class
All job site scrapers inherit from this
"""

from abc import ABC, abstractmethod
import time
import random

try:
    import requests
except ImportError:
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

try:
    from fake_useragent import UserAgent
except ImportError:
    UserAgent = None


class BaseScraper(ABC):
    """Base class for all job scrapers"""
    
    def __init__(self):
        if UserAgent:
            self.ua = UserAgent()
            ua_string = self.ua.random
        else:
            self.ua = None
            ua_string = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        if requests:
            self.session = requests.Session()
            self.session.headers.update({'User-Agent': ua_string})
        else:
            self.session = None
        self.delay = (2, 5)  # Random delay between requests
    
    @abstractmethod
    def scrape(self, job_title, location, remote=False):
        """
        Scrape jobs from the site
        
        Args:
            job_title: Job title to search for
            location: Location to search in
            remote: Whether to filter for remote jobs
            
        Returns:
            List of job dictionaries with standardized fields
        """
        pass
    
    def get_page(self, url, params=None):
        """Make HTTP request with error handling"""
        try:
            time.sleep(random.uniform(*self.delay))
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response
        except Exception as e:
            print(f"Error fetching {url}: {str(e)}")
            return None
    
    def parse_html(self, html_content):
        """Parse HTML content with BeautifulSoup"""
        return BeautifulSoup(html_content, 'html.parser')
    
    def standardize_job(self, job_data):
        """Standardize job data format with all required fields"""
        from datetime import datetime
        
        # Ensure work_type is set
        location = job_data.get('location', '')
        description = job_data.get('description', '')
        is_remote = job_data.get('remote', False)
        
        work_type = self._detect_work_type(location, description, is_remote)
        
        # Ensure posted_date is set
        posted_date = job_data.get('posted_date') or job_data.get('date_posted', 'Recently')
        
        return {
            'title': job_data.get('title', 'N/A'),
            'company': job_data.get('company', 'N/A'),
            'location': location or 'Remote',
            'description': description or 'N/A',
            'url': job_data.get('url', 'N/A'),
            'salary': job_data.get('salary', 'Not specified'),
            'salary_numeric': job_data.get('salary_numeric', 0),
            'job_type': job_data.get('job_type', 'Full-time'),
            'remote': is_remote,
            'work_type': work_type,
            'posted_date': posted_date,
            'posted_timestamp': job_data.get('posted_timestamp', 0),
            'tags': job_data.get('tags', []),
            'application_deadline': job_data.get('application_deadline', 'N/A')
        }
    
    def _detect_work_type(self, location, description, is_remote):
        """Detect if job is Remote, Hybrid, or On-site"""
        location_lower = location.lower() if location else ''
        desc_lower = description.lower() if description else ''
        
        # Check for remote
        if is_remote or 'remote' in location_lower or 'remote' in desc_lower:
            return 'Remote'
        
        # Check for hybrid
        if 'hybrid' in location_lower or 'hybrid' in desc_lower:
            return 'Hybrid'
        
        # Default to on-site
        return 'On-site'
