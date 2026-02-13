"""
JSearch Job Aggregator
Free job search API aggregating Indeed, LinkedIn, Glassdoor, ZipRecruiter, etc.
No API key needed for basic use
"""

from .base_scraper import BaseScraper
import json


class AdzunaScraper(BaseScraper):
    """Scraper using JSearch API - aggregates 20+ job boards"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://jsearch.p.rapidapi.com/search"
        # Free tier API key (publicly available)
        self.headers = {
            "X-RapidAPI-Key": "test",  # Will use query params instead
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
        }
    
    def scrape(self, job_title, location, remote=False):
        """Scrape jobs using simplified jobicy.com API (no auth needed)"""
        jobs = []
        
        print(f"🔍 Jobicy: Searching for '{job_title}'...")
        
        # Use Jobicy's free public API
        url = "https://jobicy.com/api/v2/remote-jobs"
        
        params = {
            'count': 50,
            'geo': location if location else '',
            'industry': 'programming',
            'tag': job_title.lower().replace(' ', '-')
        }
        
        try:
            print(f"📡 Jobicy: Fetching from free API...")
            
            # Don't use session headers for this API
            import requests
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('jobs', [])
            
            print(f"🎯 Jobicy: Found {len(results)} jobs from API")
            
            for job_data in results:
                try:
                    job = self._parse_jobicy_job(job_data, job_title)
                    if job:
                        jobs.append(self.standardize_job(job))
                except Exception as e:
                    print(f"⚠️  Jobicy: Error parsing job: {str(e)}")
                    continue
            
            print(f"✅ Jobicy: Successfully scraped {len(jobs)} jobs")
            
        except Exception as e:
            print(f"❌ Jobicy error: {str(e)}")
            # Fallback: Try Remotive API
            jobs = self._try_remotive_fallback(job_title, location)
        
        return jobs
    
    def _parse_jobicy_job(self, job_data, search_term):
        """Parse Jobicy job data"""
        try:
            # Only include jobs matching search term
            title = job_data.get('jobTitle', '')
            description = job_data.get('jobDescription', '')
            
            # Skip if doesn't match search term
            search_lower = search_term.lower()
            if search_lower not in title.lower() and search_lower not in description.lower():
                return None
            
            return {
                'title': title,
                'company': job_data.get('companyName', 'N/A'),
                'location': job_data.get('jobGeo', 'Remote'),
                'description': description,
                'url': job_data.get('url', 'N/A'),
                'salary': job_data.get('annualSalaryMin', 'Not specified'),
                'job_type': job_data.get('jobType', ['Full-time'])[0] if job_data.get('jobType') else 'Full-time',
                'remote': True,
                'posted_date': job_data.get('pubDate', 'N/A'),
                'category': job_data.get('jobCategory', ''),
            }
            
        except Exception as e:
            print(f"Error parsing Jobicy job: {str(e)}")
            return None
    
    def _try_remotive_fallback(self, job_title, location):
        """Fallback to Remotive API if Jobicy fails"""
        jobs = []
        
        try:
            print(f"🔄 Trying Remotive API as fallback...")
            url = "https://remotive.com/api/remote-jobs"
            
            import requests
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('jobs', [])
            
            # Filter by search term
            search_lower = job_title.lower()
            for job_data in results[:50]:
                title = job_data.get('title', '').lower()
                description = job_data.get('description', '').lower()
                
                if search_lower not in title and search_lower not in description:
                    continue
                
                job = {
                    'title': job_data.get('title', 'N/A'),
                    'company': job_data.get('company_name', 'N/A'),
                    'location': 'Remote',
                    'description': job_data.get('description', 'N/A'),
                    'url': job_data.get('url', 'N/A'),
                    'salary': job_data.get('salary', 'Not specified'),
                    'job_type': job_data.get('job_type', 'Full-time'),
                    'remote': True,
                    'posted_date': job_data.get('publication_date', 'N/A'),
                    'category': job_data.get('category', ''),
                }
                jobs.append(self.standardize_job(job))
            
            print(f"✅ Remotive: Found {len(jobs)} jobs")
            
        except Exception as e:
            print(f"❌ Remotive fallback error: {str(e)}")
        
        return jobs
