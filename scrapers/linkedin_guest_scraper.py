"""
LinkedIn Guest Scraper - 2026 Working Version
Uses the hidden 'jobs-guest' API endpoint for logged-out users
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
from urllib.parse import quote
from datetime import datetime


class LinkedInGuestScraper:
    """Scraper for LinkedIn using the guest API endpoint"""
    
    def __init__(self):
        self.name = "LinkedIn (Guest API)"
        self.base_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    
    def scrape(self, job_title, location, remote=False):
        """
        Scrape LinkedIn jobs using the guest API endpoint
        
        Args:
            job_title: Job title to search for
            location: Location to search in
            remote: Whether to filter for remote jobs
            
        Returns:
            List of job dictionaries
        """
        print(f"🚀 {self.name}: Starting scrape for '{job_title}' in '{location}'...")
        jobs = []
        
        # Scrape up to 20 pages (500 jobs max)
        # LinkedIn loads jobs in batches of 25 via this API
        max_pages = 20
        for start in range(0, max_pages * 25, 25):
            if not self._should_continue_scraping(start, len(jobs)):
                break
            
            try:
                params = {
                    'keywords': job_title,
                    'location': location,
                    'start': start,
                    'f_WT': '2' if remote else '',  # 2 = Remote, 1 = Hybrid, 3 = On-site
                    'sortBy': 'DD',  # Sort by date (most recent)
                }
                
                # Rotate headers to look like a real browser
                headers = self._get_headers()
                
                # Random delay between requests (crucial to avoid blocks)
                delay = random.uniform(1.5, 3.0)
                if start > 0:
                    print(f"   ⏳ Waiting {delay:.1f}s before next page...")
                    time.sleep(delay)
                
                response = requests.get(
                    self.base_url, 
                    params=params, 
                    headers=headers, 
                    timeout=15
                )
                
                # Handle rate limiting and blocks
                if response.status_code == 429:
                    print(f"   ⚠️ {self.name}: Rate limited (429). Stopping safely.")
                    break
                    
                if response.status_code != 200:
                    print(f"   ⚠️ {self.name}: Status {response.status_code} on page {start//25 + 1}")
                    continue
                
                # Parse the HTML response
                soup = BeautifulSoup(response.text, 'html.parser')
                job_cards = soup.find_all('li')
                
                if not job_cards or len(job_cards) == 0:
                    print(f"   ℹ️ {self.name}: No more jobs found at page {start//25 + 1}")
                    break
                
                page_num = start // 25 + 1
                print(f"   ✅ {self.name}: Found {len(job_cards)} jobs on page {page_num}")
                
                # Parse each job card
                for card in job_cards:
                    job = self._parse_job_card(card, location)
                    if job:
                        jobs.append(job)
                        
            except Exception as e:
                print(f"   ❌ {self.name}: Error scraping page {start//25 + 1}: {str(e)[:100]}")
                break
        
        print(f"✅ {self.name}: Total {len(jobs)} jobs scraped")
        return jobs
    
    def _get_headers(self):
        """Get randomized headers to avoid detection"""
        user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0',
        ]
        
        return {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.linkedin.com/jobs',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    def _should_continue_scraping(self, start, jobs_found):
        """Determine if we should continue to the next page"""
        # Stop if we've already found enough jobs
        if jobs_found >= 500:
            print(f"   ℹ️ {self.name}: Reached 500 jobs limit, stopping")
            return False
        return True
    
    def _parse_job_card(self, card, default_location):
        """Parse a single job card"""
        try:
            title_tag = card.find('h3', class_='base-search-card__title')
            company_tag = card.find('h4', class_='base-search-card__subtitle')
            link_tag = card.find('a', class_='base-card__full-link')
            date_tag = card.find('time')
            location_tag = card.find('span', class_='job-search-card__location')
            
            if not title_tag or not link_tag:
                return None
            
            # Clean the URL (remove tracking params)
            job_url = link_tag.get('href', '').split('?')[0]
            if not job_url:
                return None
            
            # Parse date
            posted_date = 'Recently'
            if date_tag:
                datetime_str = date_tag.get('datetime', '')
                if datetime_str:
                    posted_date = self._format_date(datetime_str)
                else:
                    posted_date = date_tag.text.strip()
            
            job = {
                'title': title_tag.text.strip(),
                'company': company_tag.text.strip() if company_tag else "LinkedIn Job",
                'url': job_url,
                'location': location_tag.text.strip() if location_tag else default_location,
                'description': '',  # Guest API doesn't provide descriptions
                'posted_date': posted_date,
                'posted_timestamp': self._get_timestamp(date_tag.get('datetime', '') if date_tag else None),
                'salary': 'Not specified',
                'salary_numeric': 0,
                'job_type': 'Full-time',
                'source': 'LINKEDIN',
                'remote': 'remote' in (location_tag.text.strip() if location_tag else '').lower(),
                'work_type': 'Remote' if 'remote' in (location_tag.text.strip() if location_tag else '').lower() else 'On-site'
            }
            
            return job
            
        except Exception as e:
            # Silently skip cards that fail to parse
            return None
    
    def _format_date(self, datetime_str):
        """Format ISO datetime to relative time"""
        try:
            if not datetime_str:
                return 'Recently'
            
            # Parse ISO format
            job_date = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            now = datetime.now(job_date.tzinfo)
            diff = now - job_date
            
            days = diff.days
            if days == 0:
                return 'Today'
            elif days == 1:
                return '1 day ago'
            elif days < 7:
                return f'{days} days ago'
            elif days < 30:
                weeks = days // 7
                return f'{weeks} week{"s" if weeks > 1 else ""} ago'
            else:
                months = days // 30
                return f'{months} month{"s" if months > 1 else ""} ago'
                
        except:
            return 'Recently'
    
    def _get_timestamp(self, datetime_str):
        """Convert ISO datetime to timestamp"""
        try:
            if not datetime_str:
                return 0
            
            job_date = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            return int(job_date.timestamp())
        except:
            return 0
