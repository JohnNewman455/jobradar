"""
Jooble Canada Scraper
Aggregates from multiple sources
"""

from .base_scraper import BaseScraper


class JoobleScraper(BaseScraper):
    """Scraper for Jooble Canada"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://ca.jooble.org"
        self.api_url = "https://ca.jooble.org/api"
    
    def scrape(self, job_title, location, remote=False):
        """Scrape jobs from Jooble"""
        jobs = []
        
        try:
            # Jooble search URL
            params = {
                'keywords': job_title,
                'location': location if not remote else 'Remote Canada'
            }
            
            url = f"{self.base_url}/SearchResult"
            response = self.get_page(url, params=params)
            
            if not response:
                return jobs
            
            soup = self.parse_html(response.text)
            
            # Find job listings
            job_listings = soup.find_all('div', class_='_78d63')
            
            for listing in job_listings[:50]:
                try:
                    job = self._parse_jooble_job(listing)
                    if job:
                        jobs.append(self.standardize_job(job))
                except Exception as e:
                    continue
            
            print(f"✅ Jooble: Found {len(jobs)} jobs")
            
        except Exception as e:
            print(f"❌ Jooble error: {str(e)}")
        
        return jobs
    
    def _parse_jooble_job(self, listing):
        """Parse Jooble job listing"""
        try:
            title_elem = listing.find('h2')
            title = title_elem.get_text(strip=True) if title_elem else 'N/A'
            
            link_elem = listing.find('a', class_='_0f0d2')
            url = f"{self.base_url}{link_elem['href']}" if link_elem and link_elem.get('href') else 'N/A'
            
            company_elem = listing.find('span', class_='_0f0d2')
            company = company_elem.get_text(strip=True) if company_elem else 'N/A'
            
            location_elem = listing.find('div', class_='_8e5f0')
            location = location_elem.get_text(strip=True) if location_elem else 'Canada'
            
            return {
                'title': title,
                'company': company,
                'location': location,
                'description': 'Job from Jooble aggregator',
                'url': url,
                'salary': 'Not specified',
                'remote': 'remote' in location.lower()
            }
        except:
            return None
