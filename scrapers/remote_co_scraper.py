"""
Remote.co Scraper - 2026 Working Version
Simple scraper for Remote.co job board
"""

try:
    import requests
except ImportError:
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

import time
import random


class RemoteCoScraper:
    """Scraper for Remote.co"""
    
    def __init__(self):
        self.name = "Remote.co"
    
    def scrape(self, job_title, location, remote=False):
        """
        Scrape jobs from Remote.co
        
        Args:
            job_title: Job title to search for
            location: Location (ignored, all jobs are remote)
            remote: Remote filter (ignored, all jobs are remote)
            
        Returns:
            List of job dictionaries
        """
        # Remote.co has specific category pages, or a search
        url = f"https://remote.co/remote-jobs/search/?search_keywords={job_title.replace(' ', '+')}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://remote.co/'
        }
        
        print(f"🌐 {self.name}: Searching for '{job_title}'...")
        
        jobs = []
        
        try:
            # Be polite
            time.sleep(random.uniform(1, 3))
            
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                print(f"   ❌ {self.name}: Status {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try multiple selectors
            job_cards = soup.select(
                '.card, '  # Standard card layout
                '.job_listing, '  # Alternative
                'article.job, '  # Article-based
                'li.job, '  # List-based
                '[class*="job-card"]'  # Generic match
            )
            
            if not job_cards:
                print(f"   ℹ️  {self.name}: No jobs found for '{job_title}'")
                return []
            
            print(f"   📊 {self.name}: Found {len(job_cards)} job cards")
            
            for card in job_cards:
                try:
                    title = card.select_one('.card-title, .job-title, h2, h3, a.title')
                    link = card.select_one('a')
                    company = card.select_one('.company-name, .company, .card-subtitle')
                    
                    if title and link:
                        href = link.get('href', '')
                        if href.startswith('/'):
                            href = f"https://remote.co{href}"
                        
                        if not href:
                            continue
                        
                        jobs.append({
                            'title': title.text.strip(),
                            'company': company.text.strip() if company else "Remote.co Listing",
                            'url': href,
                            'location': 'Remote',
                            'description': card.get_text()[:300],
                            'posted_date': 'Recently',
                            'posted_timestamp': 0,
                            'salary': 'Not specified',
                            'salary_numeric': 0,
                            'job_type': 'Full-time',
                            'source': 'REMOTE.CO',
                            'remote': True,
                            'work_type': 'Remote'
                        })
                        
                except Exception as e:
                    continue
            
            print(f"✅ {self.name}: Found {len(jobs)} jobs")
            return jobs
            
        except Exception as e:
            print(f"❌ {self.name}: Error - {str(e)[:100]}")
            return []
