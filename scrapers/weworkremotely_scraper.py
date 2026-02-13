"""
WeWorkRemotely Job Scraper
Scrapes remote jobs from WeWorkRemotely.com
"""

from .base_scraper import BaseScraper
import re


class WeWorkRemotelyScraper(BaseScraper):
    """Scraper for WeWorkRemotely.com"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://weworkremotely.com"
    
    def scrape(self, job_title, location, remote=False):
        """Scrape jobs from WeWorkRemotely"""
        jobs = []
        
        try:
            # WeWorkRemotely categories - we'll search programming/dev ops
            categories = [
                '/remote-jobs/search?term=' + job_title.replace(' ', '+')
            ]
            
            for category in categories:
                url = f"{self.base_url}{category}"
                response = self.get_page(url)
                
                if not response:
                    continue
                
                soup = self.parse_html(response.text)
                
                # Find job listings
                job_listings = soup.find_all('li', class_=re.compile(r'feature'))
                
                for listing in job_listings[:50]:  # Limit to 50
                    try:
                        job = self._parse_job_listing(listing)
                        if job:
                            jobs.append(self.standardize_job(job))
                    except Exception as e:
                        print(f"Error parsing WWR job: {str(e)}")
                        continue
            
            print(f"✅ WeWorkRemotely: Found {len(jobs)} jobs")
            
        except Exception as e:
            print(f"❌ WeWorkRemotely scraping error: {str(e)}")
        
        return jobs
    
    def _parse_job_listing(self, listing):
        """Parse individual job listing"""
        try:
            # Title and URL
            title_elem = listing.find('span', class_='title')
            title = title_elem.get_text(strip=True) if title_elem else 'N/A'
            
            link_elem = listing.find('a')
            job_url = f"{self.base_url}{link_elem['href']}" if link_elem and link_elem.get('href') else 'N/A'
            
            # Company
            company_elem = listing.find('span', class_='company')
            company = company_elem.get_text(strip=True) if company_elem else 'N/A'
            
            # Region/Location
            region_elem = listing.find('span', class_='region')
            location = region_elem.get_text(strip=True) if region_elem else 'Remote'
            
            # Tags
            tags = []
            tag_elems = listing.find_all('span', class_='tag')
            for tag in tag_elems:
                tags.append(tag.get_text(strip=True))
            
            return {
                'title': title,
                'company': company,
                'location': location,
                'description': f"Remote job for {title} at {company}",
                'url': job_url,
                'salary': 'Not specified',
                'job_type': 'Full-time',
                'remote': True,
                'posted_date': 'Recent',
                'tags': tags
            }
            
        except Exception as e:
            print(f"Error parsing WWR listing: {str(e)}")
            return None
