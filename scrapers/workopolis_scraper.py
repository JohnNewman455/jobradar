"""
Workopolis Scraper
Workopolis is owned by Indeed and uses the same anti-bot defenses
Requires curl_cffi to bypass bot detection
"""

try:
    from curl_cffi import requests as curl_requests
    CURL_CFFI_AVAILABLE = True
except ImportError:
    CURL_CFFI_AVAILABLE = False
    import requests as curl_requests

from bs4 import BeautifulSoup
from urllib.parse import quote
from datetime import datetime


class WorkopolisScraper:
    """Scraper for Workopolis - Uses curl_cffi to bypass Indeed's anti-bot protection"""
    
    def scrape(self, job_title, location, remote):
        if not CURL_CFFI_AVAILABLE:
            print("❌ Workopolis: curl_cffi not installed. Run: pip install curl-cffi")
            return []
        
        # Workopolis Search URL
        # Format: https://www.workopolis.com/jobsearch/find-jobs?ak=servicenow&l=oakville,%20ontario
        location_param = quote(location) if location else ''
        base_url = f"https://www.workopolis.com/jobsearch/find-jobs?ak={quote(job_title)}&l={location_param}"
        
        print(f"🔍 Workopolis: Searching for '{job_title}'...")
        print(f"📡 Workopolis: Fetching {base_url}")

        try:
            # Impersonate Chrome to bypass Indeed's firewall
            response = curl_requests.get(
                base_url, 
                impersonate="chrome110",  # Pretend to be Chrome 110
                timeout=15
            )
            
            if response.status_code != 200:
                print(f"❌ Workopolis: Blocked with status {response.status_code}")
                return []
            
            print(f"✅ Workopolis: Page loaded ({len(response.content)} bytes)")
            soup = BeautifulSoup(response.content, 'html.parser')
            jobs = []
            
            # Workopolis uses specific classes like 'JobCard' or 'result'
            # Since it's Indeed-backed, classes are often obfuscated (e.g., 'css-12345')
            # We look for generic containers
            selectors = [
                'div[class*="JobCard"]',
                'div.result',
                'a[class*="job-link"]',
                'div[class*="job_seen"]',
                'div.job-snippet',
                'div[class*="resultContent"]'
            ]
            
            cards = []
            for selector in selectors:
                cards = soup.select(selector)
                if cards:
                    print(f"✅ Workopolis: Found {len(cards)} jobs using selector '{selector}'")
                    break
            
            if not cards:
                print(f"⚠️ Workopolis: No job cards found on page")
                print(f"💡 Page might be using heavy JavaScript or different structure")
                return []
            
            for card in cards[:50]:
                try:
                    # Title
                    title_elem = (
                        card.select_one('h2') or
                        card.select_one('.job-title') or
                        card.select_one('a[class*="title"]') or
                        card.select_one('span[class*="title"]')
                    )
                    
                    if not title_elem:
                        continue
                    
                    title = title_elem.text.strip()
                    
                    # Company
                    company_elem = (
                        card.select_one('.company-name') or
                        card.select_one('.employer') or
                        card.select_one('[class*="companyName"]')
                    )
                    company = company_elem.text.strip() if company_elem else "Workopolis"
                    
                    # Extract link (careful of relative links)
                    if card.name == 'a':
                        link = card.get('href', '')
                    else:
                        link_elem = card.select_one('a')
                        link = link_elem.get('href', '') if link_elem else ''
                    
                    if link and link.startswith('/'):
                        link = f"https://www.workopolis.com{link}"
                    
                    # Location
                    location_elem = (
                        card.select_one('.location') or
                        card.select_one('[class*="companyLocation"]')
                    )
                    job_location = location_elem.text.strip() if location_elem else (location or 'Canada')
                    
                    # Description
                    desc_elem = card.select_one('.job-snippet, .description, [class*="snippet"]')
                    description = desc_elem.text.strip()[:500] if desc_elem else card.text.strip()[:500]
                    
                    job = {
                        'title': title,
                        'company': company,
                        'url': link or base_url,
                        'location': job_location,
                        'source': 'workopolis',
                        'description': description,
                        'salary': 'Not specified',
                        'posted_date': 'Recently',
                        'job_type': 'Full-time',
                        'remote': 'remote' in card.text.lower(),
                        'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    jobs.append(job)
                
                except Exception as e:
                    print(f"⚠️ Workopolis: Error parsing job card - {e}")
                    continue
            
            if jobs:
                print(f"✅ Workopolis: Found {len(jobs)} jobs")
            else:
                print(f"⚠️ Workopolis: Parsed page but extracted 0 jobs")
            
            return jobs

        except Exception as e:
            print(f"❌ Workopolis: Error - {e}")
            return []


if __name__ == "__main__":
    # Test the scraper
    print("🧪 Testing Workopolis Scraper\n")
    
    if not CURL_CFFI_AVAILABLE:
        print("❌ curl_cffi not installed!")
        print("Install with: pip install curl-cffi")
    else:
        scraper = WorkopolisScraper()
        jobs = scraper.scrape("ServiceNow Developer", "Ontario", True)
        
        print(f"\n📊 Total jobs found: {len(jobs)}")
        if jobs:
            print("\n📋 Sample jobs:")
            for i, job in enumerate(jobs[:5], 1):
                print(f"  {i}. {job['title']} at {job['company']}")
                print(f"     Location: {job['location']}")
                print(f"     URL: {job['url'][:80]}...")
