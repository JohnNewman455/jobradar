"""
Google Jobs Scraper
Uses Google Jobs API/SerpAPI for job listings
"""

from .base_scraper import BaseScraper

try:
    import requests
except ImportError:
    requests = None


class GoogleJobsScraper(BaseScraper):
    """Scraper for Google Jobs"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://serpapi.com/search"
        # Note: Google Jobs requires SerpAPI or similar service
        # Free tier: 100 searches/month
    
    def scrape(self, job_title, location, remote=False):
        """
        Scrape jobs from Google Jobs
        Using SerpAPI (requires API key in .env)
        Alternative: Use direct Google Jobs scraping with Playwright
        """
        jobs = []
        
        try:
            # Method 1: Direct scraping from Google Jobs (no API needed)
            jobs = self._scrape_direct(job_title, location, remote)
            
            print(f"✅ Google Jobs: Found {len(jobs)} jobs")
            
        except Exception as e:
            print(f"❌ Google Jobs error: {str(e)}")
        
        return jobs
    
    def _scrape_direct(self, job_title, location, remote):
        """Direct scraping from Google Jobs search results"""
        jobs = []
        
        # Build Google Jobs URL
        query = f"{job_title} {location if not remote else 'remote'}"
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}&ibp=htl;jobs"
        
        response = self.get_page(url)
        if not response:
            return jobs
        
        soup = self.parse_html(response.text)
        
        # Google Jobs uses dynamic loading, so this is a basic implementation
        # For production, use Playwright or SerpAPI
        
        job_cards = soup.find_all('div', class_='PwjeAc')
        
        for card in job_cards[:50]:
            try:
                job = self._parse_google_job(card)
                if job:
                    jobs.append(self.standardize_job(job))
            except Exception as e:
                continue
        
        return jobs
    
    def _parse_google_job(self, card):
        """Parse individual Google Job card"""
        try:
            title_elem = card.find('div', class_='BjJfJf')
            title = title_elem.get_text(strip=True) if title_elem else 'N/A'
            
            company_elem = card.find('div', class_='vNEEBe')
            company = company_elem.get_text(strip=True) if company_elem else 'N/A'
            
            location_elem = card.find('div', class_='Qk80Jf')
            location = location_elem.get_text(strip=True) if location_elem else 'N/A'
            
            return {
                'title': title,
                'company': company,
                'location': location,
                'description': f"Job listing from Google Jobs",
                'url': 'https://www.google.com/search?q=jobs',
                'salary': 'Not specified',
                'remote': 'remote' in location.lower()
            }
        except:
            return None
