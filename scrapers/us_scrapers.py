"""
US-Specific Job Scrapers - 2026 Working
BuiltIn.com (US tech startups) and USAJobs.gov (government)
"""

try:
    from curl_cffi import requests as cffi_requests
    CURL_CFFI_AVAILABLE = True
except ImportError:
    CURL_CFFI_AVAILABLE = False

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import json
import time
import random
from datetime import datetime


class BuiltInScraper:
    """Scraper for BuiltIn.com - US tech startups and companies (USA)"""
    
    def __init__(self):
        self.name = "BuiltIn (USA)"
        self.base_url = "https://builtin.com"
    
    def scrape(self, job_title, location, remote=False):
        """Scrape jobs from BuiltIn.com"""
        print(f"🏗️ {self.name}: Searching for '{job_title}'...")
        
        all_jobs = []
        max_pages = 3
        
        for page in range(1, max_pages + 1):
            # BuiltIn uses /jobs/remote or /jobs/dev with search
            if remote:
                url = f"{self.base_url}/jobs/remote?search={quote(job_title)}"
            else:
                url = f"{self.base_url}/jobs?search={quote(job_title)}"
            
            if page > 1:
                url += f"&page={page}"
            
            jobs = self._fetch_page(url, location, remote, page)
            if not jobs:
                break
            
            all_jobs.extend(jobs)
            print(f"   📄 Page {page}: {len(jobs)} jobs (total: {len(all_jobs)})")
            
            if page < max_pages:
                time.sleep(random.uniform(1.5, 3.0))
        
        if all_jobs:
            print(f"✅ {self.name}: Found {len(all_jobs)} total jobs")
        else:
            print(f"⚠️ {self.name}: No jobs found")
        return all_jobs
    
    def _fetch_page(self, url, default_location, remote, page_num):
        jobs = []
        try:
            time.sleep(random.uniform(1.0, 2.0))
            
            response = None
            if CURL_CFFI_AVAILABLE:
                try:
                    response = cffi_requests.get(url, impersonate="chrome120", timeout=15)
                except:
                    response = None
            
            if not response or response.status_code != 200:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml',
                }
                response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # BuiltIn uses Next.js __NEXT_DATA__
            next_data = soup.select_one('script#__NEXT_DATA__')
            if next_data:
                try:
                    data = json.loads(next_data.text)
                    page_props = data.get('props', {}).get('pageProps', {})
                    job_list = page_props.get('jobs', []) or page_props.get('results', [])
                    
                    if job_list:
                        for item in job_list:
                            job = self._parse_nextjs_job(item, default_location, remote)
                            if job:
                                jobs.append(job)
                        return jobs
                except (json.JSONDecodeError, KeyError):
                    pass
            
            # Fallback: HTML parsing
            for sel in ['div[data-id]', 'a[href*="/job/"]', 'article', '.job-card']:
                cards = soup.select(sel)
                if len(cards) > 2:
                    seen = set()
                    for card in cards:
                        link = card.select_one('a[href*="/job/"]') or (card if card.name == 'a' else None)
                        title_el = card.select_one('h2, h3, .job-title') or card
                        
                        if link and title_el:
                            title = title_el.get_text(strip=True)
                            href = link.get('href', '')
                            if title and href and href not in seen and len(title) > 5:
                                seen.add(href)
                                if href.startswith('/'):
                                    href = f"{self.base_url}{href}"
                                
                                company_el = card.select_one('.company-name, .company')
                                
                                jobs.append({
                                    'title': title,
                                    'company': company_el.get_text(strip=True) if company_el else 'BuiltIn Listing',
                                    'url': href,
                                    'location': default_location or 'USA',
                                    'description': card.get_text(strip=True)[:300],
                                    'posted_date': 'Recently',
                                    'posted_timestamp': 0,
                                    'salary': 'Not specified',
                                    'salary_numeric': 0,
                                    'job_type': 'Full-time',
                                    'source': 'BUILTIN',
                                    'remote': remote,
                                    'work_type': 'Remote' if remote else 'On-site'
                                })
                    if jobs:
                        return jobs
        
        except Exception as e:
            print(f"   ❌ {self.name}: Page {page_num} error - {str(e)[:100]}")
        return jobs
    
    def _parse_nextjs_job(self, item, default_location, remote):
        try:
            title = item.get('title', '') or item.get('jobTitle', '')
            if not title:
                return None
            
            company = item.get('company', {})
            if isinstance(company, dict):
                company = company.get('name', '') or 'BuiltIn Listing'
            elif not company:
                company = 'BuiltIn Listing'
            
            url = item.get('url', '') or item.get('slug', '')
            if url and not url.startswith('http'):
                url = f"{self.base_url}/job/{url}" if '/' not in url else f"{self.base_url}{url}"
            
            location = item.get('location', '') or default_location or 'USA'
            
            return {
                'title': title,
                'company': company,
                'url': url or self.base_url,
                'location': location,
                'description': item.get('description', '')[:300],
                'posted_date': 'Recently',
                'posted_timestamp': 0,
                'salary': item.get('salary', 'Not specified'),
                'salary_numeric': 0,
                'job_type': 'Full-time',
                'source': 'BUILTIN',
                'remote': remote or 'remote' in str(location).lower(),
                'work_type': 'Remote' if remote or 'remote' in str(location).lower() else 'On-site'
            }
        except:
            return None


class USAJobsScraper:
    """Scraper for USAJobs.gov - Federal US Government jobs (USA)"""
    
    def __init__(self):
        self.name = "USAJobs.gov (USA)"
        self.api_url = "https://data.usajobs.gov/api/search"
    
    def scrape(self, job_title, location, remote=False):
        """Scrape from USAJobs API (no auth needed for basic search)"""
        print(f"🏛️ {self.name}: Searching for '{job_title}'...")
        
        headers = {
            'User-Agent': 'jobscraper@example.com',
            'Host': 'data.usajobs.gov',
        }
        
        params = {
            'Keyword': job_title,
            'ResultsPerPage': 50,
        }
        
        if location and location.lower() not in ('remote', 'usa', 'us', 'united states', ''):
            params['LocationName'] = location
        
        if remote:
            params['RemoteIndicator'] = 'True'
        
        try:
            time.sleep(random.uniform(1.0, 2.0))
            response = requests.get(self.api_url, headers=headers, params=params, timeout=15)
            
            if response.status_code != 200:
                print(f"   ❌ {self.name}: API returned {response.status_code}")
                return []
            
            data = response.json()
            results = data.get('SearchResult', {}).get('SearchResultItems', [])
            
            if not results:
                print(f"   ⚠️ {self.name}: No results from API")
                return []
            
            jobs = []
            for item in results:
                try:
                    match = item.get('MatchedObjectDescriptor', {})
                    
                    title = match.get('PositionTitle', '')
                    if not title:
                        continue
                    
                    org = match.get('OrganizationName', 'US Government')
                    
                    # Location
                    locations = match.get('PositionLocation', [])
                    loc_name = 'USA'
                    if locations:
                        loc_parts = []
                        for loc in locations[:2]:
                            n = loc.get('LocationName', '')
                            if n:
                                loc_parts.append(n)
                        loc_name = '; '.join(loc_parts) or 'USA'
                    
                    # Salary
                    remun = match.get('PositionRemuneration', [{}])
                    salary = 'Not specified'
                    salary_numeric = 0
                    if remun:
                        r = remun[0]
                        sal_min = r.get('MinimumRange', '')
                        sal_max = r.get('MaximumRange', '')
                        if sal_min and sal_max:
                            try:
                                salary = f"${int(float(sal_min)):,} - ${int(float(sal_max)):,}/yr"
                                salary_numeric = int((float(sal_min) + float(sal_max)) / 2)
                            except:
                                salary = f"${sal_min} - ${sal_max}"
                    
                    # URL
                    url = match.get('PositionURI', '') or match.get('ApplyURI', [''])[0]
                    
                    # Date
                    pub_date = match.get('PublicationStartDate', '')
                    posted_date = self._parse_date(pub_date)
                    
                    is_remote = remote or 'remote' in loc_name.lower() or 'telework' in str(match).lower()
                    
                    jobs.append({
                        'title': title,
                        'company': org,
                        'url': url,
                        'location': loc_name,
                        'description': match.get('UserArea', {}).get('Details', {}).get('MajorDuties', [''])[0][:500] if match.get('UserArea') else '',
                        'posted_date': posted_date,
                        'posted_timestamp': self._get_timestamp(pub_date),
                        'salary': salary,
                        'salary_numeric': salary_numeric,
                        'job_type': match.get('PositionSchedule', [{}])[0].get('Name', 'Full-time') if match.get('PositionSchedule') else 'Full-time',
                        'source': 'USAJOBS',
                        'remote': is_remote,
                        'work_type': 'Remote' if is_remote else 'On-site'
                    })
                except Exception as e:
                    continue
            
            if jobs:
                print(f"✅ {self.name}: Found {len(jobs)} jobs")
            else:
                print(f"⚠️ {self.name}: Parsed 0 jobs from {len(results)} results")
            return jobs
            
        except Exception as e:
            print(f"   ❌ {self.name}: Error - {str(e)[:100]}")
            return []
    
    def _parse_date(self, date_str):
        if not date_str:
            return 'Recently'
        try:
            dt = datetime.fromisoformat(str(date_str).replace('Z', '+00:00'))
            days = (datetime.now() - dt.replace(tzinfo=None)).days
            formatted = dt.strftime('%b %d')
            if days == 0: return f"{formatted} (Today)"
            elif days == 1: return f"{formatted} (1 day ago)"
            elif days < 30: return f"{formatted} ({days} days ago)"
            else: return dt.strftime('%B %d, %Y')
        except:
            return date_str
    
    def _get_timestamp(self, date_str):
        if not date_str:
            return 0
        try:
            dt = datetime.fromisoformat(str(date_str).replace('Z', '+00:00'))
            return int(dt.replace(tzinfo=None).timestamp())
        except:
            return 0
