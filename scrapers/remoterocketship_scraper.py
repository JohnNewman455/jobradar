"""
RemoteRocketship Scraper
Canadian remote job board with clean URL structure
"""

try:
    import requests
except ImportError:
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

from urllib.parse import quote
from datetime import datetime


class RemoteRocketshipScraper:
    """Scraper for RemoteRocketship.com - Remote jobs for Canada"""
    
    def scrape(self, job_title, location, remote):
        # URL format: https://www.remoterocketship.com/ca/jobs/servicenow/?page=1&sort=DateAdded
        # Clean the job title for URL (spaces to hyphens, lowercase)
        job_slug = job_title.lower().replace(' ', '-')
        url = f"https://www.remoterocketship.com/ca/jobs/{job_slug}/?page=1&sort=DateAdded"
        
        # Fallback to search if specific job title URL doesn't work
        fallback_url = f"https://www.remoterocketship.com/ca/jobs/search?q={quote(job_title)}"
        
        print(f"🔍 RemoteRocketship: Searching for '{job_title}'...")
        print(f"📡 RemoteRocketship: Fetching {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive'
        }
        
        jobs = []
        
        # Try primary URL first
        for attempt_url in [url, fallback_url]:
            try:
                response = requests.get(attempt_url, headers=headers, timeout=15)
                
                if response.status_code == 404 and attempt_url == url:
                    print(f"⚠️ RemoteRocketship: Job category not found, trying search...")
                    continue  # Try fallback
                
                if response.status_code != 200:
                    print(f"❌ RemoteRocketship: Status {response.status_code}")
                    continue
                
                print(f"✅ RemoteRocketship: Page loaded ({len(response.text)} bytes)")
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for job listings - RemoteRocketship structure
                selectors = [
                    'div[class*="JobCard"]',
                    '.job-listing',
                    '.job-item',
                    'article.job',
                    'div[class*="job-row"]',
                    '.result-item'
                ]
                
                cards = []
                for selector in selectors:
                    cards = soup.select(selector)
                    if cards:
                        print(f"✅ RemoteRocketship: Found {len(cards)} jobs using selector '{selector}'")
                        break
                
                if not cards:
                    print(f"⚠️ RemoteRocketship: No job cards found with URL: {attempt_url}")
                    continue  # Try next URL
                
                # Parse jobs
                for card in cards[:50]:
                    try:
                        # Title
                        title_elem = (
                            card.select_one('h2') or
                            card.select_one('h3') or
                            card.select_one('.title') or
                            card.select_one('a[class*="title"]')
                        )
                        
                        if not title_elem:
                            continue
                        
                        title = title_elem.text.strip()
                        
                        # Link
                        if title_elem.name == 'a':
                            link = title_elem.get('href', '')
                        else:
                            link_elem = card.select_one('a')
                            link = link_elem.get('href', '') if link_elem else ''
                        
                        # Fix relative URLs
                        if link and not link.startswith('http'):
                            link = f"https://www.remoterocketship.com{link}"
                        
                        # Company
                        company_elem = (
                            card.select_one('.company') or
                            card.select_one('.employer') or
                            card.select_one('[class*="company"]')
                        )
                        company = company_elem.text.strip() if company_elem else "RemoteRocketship"
                        
                        # Location (usually "Remote" for this site)
                        location_elem = card.select_one('.location, [class*="location"]')
                        job_location = location_elem.text.strip() if location_elem else "Remote (Canada)"
                        
                        # Date if available
                        date_elem = card.select_one('.date, time, [class*="posted"]')
                        posted_date = date_elem.text.strip() if date_elem else 'Recently'
                        
                        # Description
                        desc_elem = card.select_one('.description, p')
                        description = desc_elem.text.strip()[:500] if desc_elem else card.text.strip()[:500]
                        
                        job = {
                            'title': title,
                            'company': company,
                            'url': link or attempt_url,
                            'location': job_location,
                            'source': 'remoterocketship',
                            'description': description,
                            'salary': 'Not specified',
                            'posted_date': posted_date,
                            'job_type': 'Full-time',
                            'remote': True,  # This site is all remote jobs
                            'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        jobs.append(job)
                    
                    except Exception as e:
                        print(f"⚠️ RemoteRocketship: Error parsing job card - {e}")
                        continue
                
                # If we found jobs, break out of URL attempts
                if jobs:
                    break
                    
            except requests.Timeout:
                print(f"❌ RemoteRocketship: Request timeout for {attempt_url}")
            except requests.RequestException as e:
                print(f"❌ RemoteRocketship: Network error - {e}")
            except Exception as e:
                print(f"❌ RemoteRocketship: Unexpected error - {e}")
        
        if jobs:
            print(f"✅ RemoteRocketship: Found {len(jobs)} jobs")
        else:
            print(f"⚠️ RemoteRocketship: No jobs found after all attempts")
        
        return jobs


if __name__ == "__main__":
    # Test the scraper
    print("🧪 Testing RemoteRocketship Scraper\n")
    scraper = RemoteRocketshipScraper()
    jobs = scraper.scrape("ServiceNow Developer", "Canada", True)
    
    print(f"\n📊 Total jobs found: {len(jobs)}")
    if jobs:
        print("\n📋 Sample jobs:")
        for i, job in enumerate(jobs[:5], 1):
            print(f"  {i}. {job['title']} at {job['company']}")
            print(f"     Location: {job['location']}")
            print(f"     URL: {job['url'][:80]}...")
