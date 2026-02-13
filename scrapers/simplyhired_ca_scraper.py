"""
SimplyHired Canada Scraper - 2026 Working Version
Parses __NEXT_DATA__ JSON from Next.js pages
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


class SimplyHiredCAScraper:
    """Scraper for SimplyHired Canada using Next.js __NEXT_DATA__"""
    
    def __init__(self):
        self.name = "SimplyHired CA"
        self.base_url = "https://www.simplyhired.ca"
    
    def scrape(self, job_title, location, remote=False):
        """Scrape jobs from SimplyHired Canada"""
        print(f"🇨🇦 {self.name}: Searching for '{job_title}'...")
        
        all_jobs = []
        max_pages = 3  # Canadian site usually has fewer results
        
        for page in range(1, max_pages + 1):
            url = f"{self.base_url}/search?q={quote(job_title)}&l={quote(location or 'Canada')}"
            if remote:
                url += "&fdb=rf"
            if page > 1:
                url += f"&pn={page}"
            
            jobs = self._fetch_page(url, location, remote, page)
            
            if not jobs:
                if page == 1:
                    print(f"   ⚠️ {self.name}: No jobs found on first page")
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
        """Fetch and parse a single page"""
        jobs = []
        try:
            time.sleep(random.uniform(1.0, 2.0))
            
            response = None
            if CURL_CFFI_AVAILABLE:
                try:
                    response = cffi_requests.get(
                        url,
                        impersonate="chrome120",
                        headers={
                            'Accept': 'text/html,application/xhtml+xml',
                            'Accept-Language': 'en-CA,en;q=0.9',
                            'Referer': f'{self.base_url}/',
                        },
                        timeout=15
                    )
                except:
                    response = None
            
            if not response or response.status_code != 200:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml',
                    'Accept-Language': 'en-CA,en;q=0.9',
                }
                response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Strategy 1: __NEXT_DATA__
            next_data = soup.select_one('script#__NEXT_DATA__')
            if next_data:
                try:
                    data = json.loads(next_data.text)
                    page_props = data.get('props', {}).get('pageProps', {})
                    job_list = page_props.get('jobs', [])
                    
                    if job_list:
                        for item in job_list:
                            job = self._parse_nextjs_job(item, default_location, remote)
                            if job:
                                jobs.append(job)
                        return jobs
                except (json.JSONDecodeError, KeyError):
                    pass
            
            # Strategy 2: LD+JSON
            ld_scripts = soup.select('script[type="application/ld+json"]')
            for script in ld_scripts:
                try:
                    ld_data = json.loads(script.text)
                    if isinstance(ld_data, dict) and ld_data.get('@type') == 'ItemList':
                        for item in ld_data.get('itemListElement', []):
                            posting = item.get('item', item)
                            if posting.get('@type') == 'JobPosting':
                                title = posting.get('title', '')
                                if title:
                                    company = ''
                                    org = posting.get('hiringOrganization', {})
                                    if isinstance(org, dict):
                                        company = org.get('name', '')
                                    
                                    jobs.append({
                                        'title': title,
                                        'company': company or 'SimplyHired CA',
                                        'url': posting.get('url', self.base_url),
                                        'location': default_location or 'Canada',
                                        'description': posting.get('description', '')[:500],
                                        'posted_date': 'Recently',
                                        'posted_timestamp': 0,
                                        'salary': 'Not specified',
                                        'salary_numeric': 0,
                                        'job_type': 'Full-time',
                                        'source': 'SIMPLYHIRED_CA',
                                        'remote': remote,
                                        'work_type': 'Remote' if remote else 'On-site'
                                    })
                        if jobs:
                            return jobs
                except:
                    continue
            
            # Strategy 3: HTML fallback
            for selector in ['a[href*="/job/"]', 'article', 'li[data-testid]']:
                cards = soup.select(selector)
                if len(cards) > 2:
                    seen = set()
                    for card in cards:
                        link = card.select_one('a[href*="/job/"]') or (card if card.name == 'a' else None)
                        title_el = card.select_one('h3, h2') or card
                        if link and title_el:
                            title = title_el.get_text(strip=True)
                            href = link.get('href', '')
                            if title and href and href not in seen:
                                seen.add(href)
                                if href.startswith('/'):
                                    href = f"{self.base_url}{href}"
                                jobs.append({
                                    'title': title,
                                    'company': 'SimplyHired CA',
                                    'url': href,
                                    'location': default_location or 'Canada',
                                    'description': '',
                                    'posted_date': 'Recently',
                                    'posted_timestamp': 0,
                                    'salary': 'Not specified',
                                    'salary_numeric': 0,
                                    'job_type': 'Full-time',
                                    'source': 'SIMPLYHIRED_CA',
                                    'remote': remote,
                                    'work_type': 'Remote' if remote else 'On-site'
                                })
                    if jobs:
                        return jobs
        
        except Exception as e:
            print(f"   ❌ {self.name}: Page {page_num} error - {str(e)[:100]}")
        
        return jobs
    
    def _parse_nextjs_job(self, item, default_location, remote):
        """Parse a job from __NEXT_DATA__ JSON"""
        try:
            title = item.get('title', '')
            if not title:
                return None
            
            company = item.get('company', '') or 'SimplyHired CA'
            location = item.get('location', '') or default_location or 'Canada'
            
            encoded_url = item.get('encodedUrl', '')
            job_key = item.get('jobKey', '')
            if encoded_url:
                url = f"{self.base_url}/job/{encoded_url}"
            elif job_key:
                url = f"{self.base_url}/job/{job_key}"
            else:
                url = self.base_url
            
            # Salary
            salary_info = item.get('salaryInfo', {})
            salary = 'Not specified'
            salary_numeric = 0
            if isinstance(salary_info, dict):
                sal_min = salary_info.get('min', 0)
                sal_max = salary_info.get('max', 0)
                if sal_min and sal_max:
                    salary = f"C${sal_min:,.0f} - C${sal_max:,.0f}"
                    salary_numeric = int((sal_min + sal_max) / 2)
                elif sal_min:
                    salary = f"C${sal_min:,.0f}+"
                    salary_numeric = int(sal_min)
            elif isinstance(salary_info, str) and salary_info:
                salary = salary_info
            
            snippet = item.get('snippet', '') or ''
            posted_date = item.get('dateOnIndeed', '')
            is_remote = remote or 'remote' in location.lower() or 'remote' in title.lower()
            
            return {
                'title': title,
                'company': company,
                'url': url,
                'location': location,
                'description': snippet[:500],
                'posted_date': self._parse_date(posted_date),
                'posted_timestamp': self._get_timestamp(posted_date),
                'salary': salary,
                'salary_numeric': salary_numeric,
                'job_type': item.get('employmentType', 'Full-time'),
                'source': 'SIMPLYHIRED_CA',
                'remote': is_remote,
                'work_type': 'Remote' if is_remote else 'On-site'
            }
        except:
            return None
    
    def _parse_date(self, date_str):
        try:
            if not date_str: return 'Recently'
            dt = datetime.fromisoformat(str(date_str).replace('Z', '+00:00'))
            days = (datetime.now() - dt.replace(tzinfo=None)).days
            if days == 0: return 'Today'
            elif days == 1: return '1 day ago'
            elif days < 7: return f'{days} days ago'
            elif days < 30:
                w = days // 7
                return f'{w} week{"s" if w > 1 else ""} ago'
            else: return dt.strftime('%B %d, %Y')
        except: return 'Recently'
    
    def _get_timestamp(self, date_str):
        try:
            if not date_str: return 0
            dt = datetime.fromisoformat(str(date_str).replace('Z', '+00:00'))
            return int(dt.replace(tzinfo=None).timestamp())
        except: return 0
