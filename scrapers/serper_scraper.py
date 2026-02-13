"""
Serper.dev Google Jobs Scraper
Free tier: 2,500 searches per month
Aggregates jobs from Google Jobs (includes Indeed, LinkedIn, etc.)
"""

from .base_scraper import BaseScraper
import os


class SerperGoogleJobsScraper(BaseScraper):
    """Scraper using Serper.dev free API for Google Jobs"""
    
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv("SERPER_API_KEY", "demo")  # Use demo key or set SERPER_API_KEY env var
        self.base_url = "https://google.serper.dev/jobs"
    
    def scrape(self, job_title, location, remote=False):
        """Scrape jobs from Google Jobs via Serper API"""
        jobs = []
        
        print(f"🔍 Serper (Google Jobs): Searching for '{job_title}'...")
        
        # Build search query
        query = f"{job_title}"
        if remote:
            query += " remote"
        
        try:
            import requests
            
            headers = {
                "X-API-KEY": self.api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "q": query,
                "location": location if location else "United States",
                "gl": "us",
                "num": 50
            }
            
            print(f"📡 Serper: Fetching from Google Jobs API...")
            response = requests.post(
                self.base_url,
                json=payload,
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 401:
                print("⚠️  Serper: API key not set. Get free key at https://serper.dev")
                print("   Set environment variable: export SERPER_API_KEY='your_key'")
                return jobs
            
            response.raise_for_status()
            data = response.json()
            
            results = data.get('jobs', [])
            print(f"🎯 Serper: Found {len(results)} jobs from Google")
            
            for job_data in results:
                try:
                    job = self._parse_serper_job(job_data)
                    if job:
                        jobs.append(self.standardize_job(job))
                except Exception as e:
                    print(f"⚠️  Serper: Error parsing job: {str(e)}")
                    continue
            
            print(f"✅ Serper: Successfully scraped {len(jobs)} jobs")
            
        except Exception as e:
            print(f"❌ Serper error: {str(e)}")
        
        return jobs
    
    def _parse_serper_job(self, job_data):
        """Parse Serper job data"""
        try:
            # Serper returns Google Jobs format
            return {
                'title': job_data.get('title', 'N/A'),
                'company': job_data.get('company', {}).get('name', 'N/A') if isinstance(job_data.get('company'), dict) else job_data.get('company', 'N/A'),
                'location': job_data.get('location', 'Remote'),
                'description': job_data.get('description', 'N/A'),
                'url': job_data.get('link', job_data.get('applyLink', 'N/A')),
                'salary': job_data.get('salary', 'Not specified'),
                'job_type': job_data.get('employmentType', 'Full-time'),
                'remote': 'remote' in job_data.get('title', '').lower() or 'remote' in job_data.get('location', '').lower(),
                'posted_date': job_data.get('datePosted', job_data.get('datePublished', 'N/A')),
                'source_site': job_data.get('via', 'Google Jobs'),
            }
            
        except Exception as e:
            print(f"Error parsing Serper job: {str(e)}")
            return None
