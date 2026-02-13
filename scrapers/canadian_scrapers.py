"""
Canadian Job Scrapers
Eluta, JobTome, JobRapido - Canadian job aggregators
"""

try:
    import requests
except ImportError:
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

import random
import time
from urllib.parse import quote
from datetime import datetime


# --- ELUTA SCRAPER ---
class ElutaScraper:
    """Scraper for Eluta.ca - Leading Canadian job board"""
    
    def scrape(self, job_title, location, remote):
        # Eluta URL format: https://www.eluta.ca/search?q=servicenow&l=&qc=
        base_url = "https://www.eluta.ca/search"
        params = {
            'q': job_title,
            'l': location or '',  # Location can be empty
            'qc': ''  # Query context
        }
        
        print(f"🔍 Eluta: Searching for '{job_title}'...")
        print(f"📡 Eluta: Fetching {base_url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.eluta.ca/',
            'Connection': 'keep-alive'
        }

        try:
            response = requests.get(base_url, params=params, headers=headers, timeout=15)
            
            if response.status_code != 200:
                print(f"❌ Eluta: Status {response.status_code}")
                return []
            
            print(f"✅ Eluta: Page loaded ({len(response.content)} bytes)")
            soup = BeautifulSoup(response.content, 'html.parser')
            jobs = []
            
            # Eluta structure - try multiple selectors
            selectors = [
                '.organic-job',
                '.sponsored-job',
                '.job-listing',
                '.result-item',
                'div[class*="job"]'
            ]
            
            cards = []
            for selector in selectors:
                cards = soup.select(selector)
                if cards:
                    print(f"✅ Eluta: Found {len(cards)} jobs using selector '{selector}'")
                    break
            
            if not cards:
                print(f"⚠️ Eluta: No job cards found")
                return []
            
            for card in cards[:50]:
                try:
                    # Try multiple title selectors
                    title_elem = (
                        card.select_one('.org-job-title') or
                        card.select_one('.job-title') or
                        card.select_one('h2 a') or
                        card.select_one('h3 a') or
                        card.select_one('a[class*="title"]')
                    )
                    
                    if not title_elem:
                        continue
                    
                    title = title_elem.text.strip()
                    
                    # Company
                    company_elem = (
                        card.select_one('.org-employer') or
                        card.select_one('.employer') or
                        card.select_one('.company')
                    )
                    company = company_elem.text.strip() if company_elem else "Eluta Listing"
                    
                    # Link
                    if title_elem.name == 'a':
                        link = title_elem.get('href', '')
                    else:
                        link_elem = card.select_one('a')
                        link = link_elem.get('href', '') if link_elem else ''
                    
                    # Fix relative URLs
                    if link and link.startswith('/'):
                        link = f"https://www.eluta.ca{link}"
                    
                    # Location
                    location_elem = (
                        card.select_one('.org-location') or
                        card.select_one('.location')
                    )
                    job_location = location_elem.text.strip() if location_elem else (location or 'Canada')
                    
                    # Description
                    desc_elem = card.select_one('.description, p')
                    description = desc_elem.text.strip()[:500] if desc_elem else card.text.strip()[:500]
                    
                    job = {
                        'title': title,
                        'company': company,
                        'url': link or base_url,
                        'location': job_location,
                        'source': 'eluta',
                        'description': description,
                        'salary': 'Not specified',
                        'posted_date': 'Recently',
                        'job_type': 'Full-time',
                        'remote': 'remote' in card.text.lower(),
                        'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    jobs.append(job)
                
                except Exception as e:
                    print(f"⚠️ Eluta: Error parsing job card - {e}")
                    continue
            
            if jobs:
                print(f"✅ Eluta: Found {len(jobs)} jobs")
            else:
                print(f"⚠️ Eluta: Parsed page but extracted 0 jobs")
            
            return jobs
            
        except requests.Timeout:
            print(f"❌ Eluta: Request timeout")
            return []
        except requests.RequestException as e:
            print(f"❌ Eluta: Network error - {e}")
            return []
        except Exception as e:
            print(f"❌ Eluta: Unexpected error - {e}")
            return []


# --- JOBTOME SCRAPER ---
class JobTomeScraper:
    """Scraper for JobTome Canada - Job aggregator"""
    
    def scrape(self, job_title, location, remote):
        # Construct URL: https://ca.jobtome.com/jobs?q=servicenow&l=canada
        url = f"https://ca.jobtome.com/jobs?q={quote(job_title)}&l={quote(location or 'canada')}"
        
        print(f"🔍 JobTome: Searching for '{job_title}'...")
        print(f"📡 JobTome: Fetching {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-CA,en;q=0.9'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                print(f"❌ JobTome: Status {response.status_code}")
                return []
            
            print(f"✅ JobTome: Page loaded ({len(response.content)} bytes)")
            soup = BeautifulSoup(response.content, 'html.parser')
            jobs = []
            
            # Try multiple selectors
            selectors = [
                '.job_result',
                '.result',
                '.job-card',
                'div[class*="job"]',
                'article'
            ]
            
            cards = []
            for selector in selectors:
                cards = soup.select(selector)
                if cards:
                    print(f"✅ JobTome: Found {len(cards)} jobs using selector '{selector}'")
                    break
            
            if not cards:
                print(f"⚠️ JobTome: No job cards found")
                return []
            
            for card in cards[:50]:
                try:
                    title_elem = (
                        card.select_one('h2 a') or
                        card.select_one('.title a') or
                        card.select_one('h3 a') or
                        card.select_one('a[class*="title"]')
                    )
                    
                    if not title_elem:
                        continue
                    
                    title = title_elem.text.strip()
                    link = title_elem.get('href', '')
                    
                    # Company
                    company_elem = card.select_one('.company, .employer')
                    company = company_elem.text.strip() if company_elem else "JobTome Listing"
                    
                    job = {
                        'title': title,
                        'company': company,
                        'url': link if link.startswith('http') else f"https://ca.jobtome.com{link}",
                        'location': location or 'Canada',
                        'source': 'jobtome',
                        'description': card.text.strip()[:500],
                        'salary': 'Not specified',
                        'posted_date': 'Recently',
                        'job_type': 'Full-time',
                        'remote': False,
                        'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    jobs.append(job)
                
                except Exception as e:
                    print(f"⚠️ JobTome: Error parsing job card - {e}")
                    continue
            
            if jobs:
                print(f"✅ JobTome: Found {len(jobs)} jobs")
            else:
                print(f"⚠️ JobTome: Parsed page but extracted 0 jobs")
            
            return jobs
            
        except Exception as e:
            print(f"❌ JobTome: Error - {e}")
            return []


# --- JOBRAPIDO SCRAPER ---

try:
    from curl_cffi import requests as cffi_requests
    CFFI_OK = True
except ImportError:
    CFFI_OK = False


class JobRapidoScraper:
    """Scraper for JobRapido Canada - Parses data-advert JSON from .result-item cards"""

    USER_AGENTS = [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64; rv:134.0) Gecko/20100101 Firefox/134.0',
    ]

    def scrape(self, job_title, location, remote):
        print(f"🔍 JobRapido: Searching for '{job_title}'...")

        all_jobs = []
        max_pages = 3

        for page in range(1, max_pages + 1):
            url = f"https://ca.jobrapido.com/?w={quote(job_title)}&l={quote(location or 'canada')}"
            if page > 1:
                url += f"&p={page}"

            jobs = self._fetch_page(url, location, remote, page)
            if not jobs:
                if page == 1:
                    print(f"   ⚠️ JobRapido: No jobs found on first page")
                break

            all_jobs.extend(jobs)
            print(f"   📄 JobRapido page {page}: {len(jobs)} jobs (total: {len(all_jobs)})")

            if page < max_pages:
                time.sleep(random.uniform(1.5, 3.0))

        if all_jobs:
            print(f"✅ JobRapido: Found {len(all_jobs)} total jobs")
        else:
            print(f"⚠️ JobRapido: No jobs found")
        return all_jobs

    def _fetch_page(self, url, default_location, remote, page_num):
        jobs = []
        try:
            ua = random.choice(self.USER_AGENTS)
            headers = {
                'User-Agent': ua,
                'Accept': 'text/html,application/xhtml+xml',
                'Accept-Language': 'en-CA,en;q=0.9',
            }

            response = None
            if CFFI_OK:
                try:
                    response = cffi_requests.get(url, impersonate='chrome120', timeout=15)
                except Exception:
                    response = None

            if not response or response.status_code != 200:
                response = requests.get(url, headers=headers, timeout=15)

            if response.status_code != 200:
                print(f"   ❌ JobRapido: Page {page_num} returned {response.status_code}")
                return []

            soup = BeautifulSoup(response.content, 'html.parser')
            cards = soup.select('.result-item[data-advert]')

            if not cards:
                print(f"   ⚠️ JobRapido page {page_num}: No .result-item[data-advert] cards")
                return []

            import json as _json
            for card in cards:
                try:
                    advert_json = card.get('data-advert', '{}')
                    advert = _json.loads(advert_json)

                    title = advert.get('companyForTitle', '') or ''
                    # The actual title is inside the card text, not in companyForTitle
                    # Try to get it from the visible text or the link preview text
                    title_text = ''
                    title_el = card.select_one('h2, h3, .job-title, a[class*="title"]')
                    if title_el:
                        title_text = title_el.get_text(strip=True)
                    if not title_text:
                        # Extract from "Open job preview for: TITLE - LOCATION"
                        full_text = card.get_text(strip=True)
                        if 'Open job preview for:' in full_text:
                            after = full_text.split('Open job preview for:')[1]
                            parts = after.split(' - ')
                            if parts:
                                title_text = parts[0].strip()
                        elif 'Open job preview for' in full_text:
                            after = full_text.split('Open job preview for')[1].lstrip(': ')
                            parts = after.split(' - ')
                            if parts:
                                title_text = parts[0].strip()

                    if not title_text:
                        # Last resort: use card text
                        text = card.get_text(strip=True)
                        title_text = text[:80]

                    company = advert.get('company', '') or 'JobRapido Listing'
                    location = advert.get('location', '') or default_location or 'Canada'
                    date_str = advert.get('date', '')  # e.g. "10 Feb"
                    advert_id = advert.get('advertId', '')

                    # Build URL
                    job_url = f"https://open.app.jobrapido.com/ca/{advert_id}/" if advert_id else url

                    # Parse date "10 Feb" -> "Feb 10, X days ago"
                    posted_date = self._parse_date(date_str)

                    is_remote = remote or 'remote' in location.lower() or 'remote' in title_text.lower()

                    jobs.append({
                        'title': title_text,
                        'company': company,
                        'url': job_url,
                        'location': location,
                        'description': card.get_text(strip=True)[:500],
                        'posted_date': posted_date,
                        'posted_timestamp': self._get_timestamp(date_str),
                        'salary': 'Not specified',
                        'salary_numeric': 0,
                        'job_type': 'Full-time',
                        'source': 'JOBRAPIDO',
                        'remote': is_remote,
                        'work_type': 'Remote' if is_remote else 'On-site',
                    })
                except Exception as e:
                    print(f"   ⚠️ JobRapido: Error parsing card - {str(e)[:60]}")
                    continue

        except Exception as e:
            print(f"   ❌ JobRapido: Page {page_num} error - {str(e)[:100]}")
        return jobs

    @staticmethod
    def _parse_date(date_str):
        """Parse '10 Feb' to 'Feb 10, 2 days ago'"""
        if not date_str:
            return 'Recently'
        try:
            # Parse "10 Feb" or "02 Feb"
            dt = datetime.strptime(f"{date_str} {datetime.now().year}", "%d %b %Y")
            days = (datetime.now() - dt).days
            formatted = dt.strftime('%b %d')
            if days == 0:
                return f"{formatted} (Today)"
            elif days == 1:
                return f"{formatted} (1 day ago)"
            elif days < 30:
                return f"{formatted} ({days} days ago)"
            else:
                return formatted
        except:
            return date_str

    @staticmethod
    def _get_timestamp(date_str):
        if not date_str:
            return 0
        try:
            dt = datetime.strptime(f"{date_str} {datetime.now().year}", "%d %b %Y")
            return int(dt.timestamp())
        except:
            return 0


if __name__ == "__main__":
    # Test scrapers
    print("🧪 Testing Canadian Scrapers\n")
    
    test_cases = [
        ("Eluta", ElutaScraper()),
        ("JobTome", JobTomeScraper()),
        ("JobRapido", JobRapidoScraper())
    ]
    
    for name, scraper in test_cases:
        print(f"\n{'='*60}")
        print(f"Testing: {name}")
        print('='*60)
        jobs = scraper.scrape("ServiceNow Developer", "Canada", True)
        print(f"Found {len(jobs)} jobs\n")
        
        if jobs:
            for i, job in enumerate(jobs[:3], 1):
                print(f"  {i}. {job['title']}")
                print(f"     Company: {job['company']}")
                print(f"     URL: {job['url'][:80]}...")
