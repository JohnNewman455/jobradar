"""
Dice.com Scraper - 2026 Working Version
Uses curl_cffi to bypass Cloudflare + parses LD+JSON and HTML
Falls back to multiple strategies
"""

try:
    from curl_cffi import requests as cffi_requests
    CURL_CFFI_AVAILABLE = True
except ImportError:
    CURL_CFFI_AVAILABLE = False

import requests
from bs4 import BeautifulSoup
import json
import time
import random
from urllib.parse import quote
from datetime import datetime


class DiceScraper:
    """Scraper for Dice.com tech jobs"""
    
    def __init__(self):
        self.name = "Dice"
        self.base_url = "https://www.dice.com"
    
    def scrape(self, job_title, location, remote=False):
        """
        Scrape jobs from Dice.com using multiple strategies
        
        Strategy 1: curl_cffi + search page HTML/JSON
        Strategy 2: curl_cffi + /jobs page with LD+JSON
        Strategy 3: Regular requests as fallback
        """
        print(f"🎲 {self.name}: Searching for '{job_title}'...")
        
        jobs = []
        
        if CURL_CFFI_AVAILABLE:
            # Strategy 1: Search page with curl_cffi
            jobs = self._scrape_search_page(job_title, location, remote)
            if jobs:
                print(f"✅ {self.name}: Found {len(jobs)} jobs via search page")
                return jobs
            
            # Strategy 2: Detail pages via LD+JSON
            jobs = self._scrape_detail_pages(job_title, location, remote)
            if jobs:
                print(f"✅ {self.name}: Found {len(jobs)} jobs via detail pages")
                return jobs
        
        # Strategy 3: Regular requests fallback  
        jobs = self._scrape_fallback(job_title, location, remote)
        if jobs:
            print(f"✅ {self.name}: Found {len(jobs)} jobs via fallback")
            return jobs
        
        print(f"⚠️ {self.name}: No jobs found")
        return []
    
    def _scrape_search_page(self, job_title, location, remote):
        """Scrape Dice search results page"""
        jobs = []
        try:
            url = f"https://www.dice.com/jobs?q={quote(job_title)}"
            if location and location.lower() not in ('remote', ''):
                url += f"&location={quote(location)}"
            if remote:
                url += "&filters.isRemote=true"
            
            delay = random.uniform(1, 3)
            time.sleep(delay)
            
            response = cffi_requests.get(url, impersonate="chrome120", timeout=20)
            
            if response.status_code != 200:
                print(f"   ⚠️ {self.name}: Search page returned {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for Next.js data
            next_data = soup.select_one('script#__NEXT_DATA__')
            if next_data:
                try:
                    data = json.loads(next_data.text)
                    page_props = data.get('props', {}).get('pageProps', {})
                    
                    # Look for search results in various locations
                    search_data = (
                        page_props.get('searchResults', {}) or 
                        page_props.get('initialSearchResults', {}) or
                        page_props.get('jobs', []) or
                        page_props
                    )
                    
                    # Extract jobs from data/jobs array
                    job_list = []
                    if isinstance(search_data, dict):
                        job_list = search_data.get('data', []) or search_data.get('jobs', [])
                    elif isinstance(search_data, list):
                        job_list = search_data
                    
                    if job_list:
                        print(f"   📊 {self.name}: Found {len(job_list)} jobs in Next.js data")
                        for item in job_list[:50]:
                            job = self._parse_nextjs_job(item, location, remote)
                            if job:
                                jobs.append(job)
                        return jobs
                except json.JSONDecodeError:
                    pass
            
            # Fallback: parse HTML directly
            # Look for job cards using various selectors
            selectors = [
                'dhi-search-card',   # Custom element
                '[data-cy="search-card"]',
                'a[data-cy="card-title-link"]',
                '.card-title-link',
                'a[href*="/job-detail/"]',
            ]
            
            for selector in selectors:
                cards = soup.select(selector)
                if cards:
                    print(f"   📊 {self.name}: Found {len(cards)} cards with {selector}")
                    for card in cards[:50]:
                        job = self._parse_html_card(card, location, remote)
                        if job:
                            jobs.append(job)
                    if jobs:
                        return jobs
            
            # Last resort: find all links to job details
            detail_links = soup.select('a[href*="/job-detail/"]')
            if detail_links:
                print(f"   📊 {self.name}: Found {len(detail_links)} raw job links")
                seen_urls = set()
                skip_texts = {'easy apply', 'apply now', 'save', 'share', ''}
                for link in detail_links:
                    href = link.get('href', '')
                    # Normalize URL (strip query params for dedup)
                    base_href = href.split('?')[0]
                    if base_href in seen_urls:
                        continue
                    
                    if not href.startswith('http'):
                        href = f"https://www.dice.com{href}"
                    
                    # Prefer the 'title' attribute (clean) over inner text (garbled)
                    title = link.get('title', '').strip()
                    if not title or len(title) < 5:
                        raw = link.get_text(strip=True)
                        # Skip UI buttons that appear as links
                        if raw.lower() in skip_texts:
                            continue
                        title = raw
                    
                    if not title or len(title) < 5:
                        continue
                    
                    # Clean title: strip trailing company/location noise
                    # Dice title attrs look like: "Job Title | City, ST | Type (uuid)"
                    # Remove the trailing UUID in parens
                    import re as _re
                    title = _re.sub(r'\s*\([0-9a-f]{20,}\)\s*$', '', title)
                    
                    seen_urls.add(base_href)
                    jobs.append({
                        'title': title[:120],
                        'company': 'Dice Listing',
                        'url': href,
                        'location': location or 'USA',
                        'description': '',
                        'posted_date': 'Recently',
                        'posted_timestamp': 0,
                        'salary': 'Not specified',
                        'salary_numeric': 0,
                        'job_type': 'Contract/Full-time',
                        'source': 'DICE',
                        'remote': remote,
                        'work_type': 'Remote' if remote else 'On-site'
                    })
                    
                    if len(jobs) >= 50:
                        break
                print(f"   📊 {self.name}: {len(jobs)} unique jobs after cleanup")
            
        except Exception as e:
            print(f"   ❌ {self.name}: Search page error - {str(e)[:100]}")
        
        return jobs
    
    def _scrape_detail_pages(self, job_title, location, remote):
        """Try individual job detail pages for LD+JSON"""
        # This is more of a backup, iterating detail pages
        return []
    
    def _scrape_fallback(self, job_title, location, remote):
        """Regular requests fallback"""
        jobs = []
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml',
            }
            
            url = f"https://www.dice.com/jobs?q={quote(job_title)}"
            if location:
                url += f"&location={quote(location)}"
            
            time.sleep(random.uniform(2, 4))
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try to find job links
            links = soup.select('a[href*="/job-detail/"]')
            seen = set()
            skip_texts = {'easy apply', 'apply now', 'save', 'share', ''}
            for link in links[:100]:
                href = link.get('href', '')
                base_href = href.split('?')[0]
                if base_href in seen:
                    continue
                
                if not href.startswith('http'):
                    href = f"https://www.dice.com{href}"
                
                title = link.get('title', '').strip()
                if not title or len(title) < 5:
                    raw = link.get_text(strip=True)
                    if raw.lower() in skip_texts:
                        continue
                    title = raw
                
                if title and len(title) > 5:
                    import re as _re
                    title = _re.sub(r'\s*\([0-9a-f]{20,}\)\s*$', '', title)
                    seen.add(base_href)
                    jobs.append({
                        'title': title,
                        'company': 'Dice Listing',
                        'url': href,
                        'location': location or 'USA',
                        'description': '',
                        'posted_date': 'Recently',
                        'posted_timestamp': 0,
                        'salary': 'Not specified',
                        'salary_numeric': 0,
                        'job_type': 'Contract/Full-time',
                        'source': 'DICE',
                        'remote': remote,
                        'work_type': 'Remote' if remote else 'On-site'
                    })
            
        except Exception as e:
            print(f"   ❌ {self.name}: Fallback error - {str(e)[:100]}")
        
        return jobs
    
    def _parse_nextjs_job(self, item, default_location, remote):
        """Parse a job from Next.js data"""
        try:
            title = item.get('title', '') or item.get('jobTitle', '')
            if not title:
                return None
            
            company = item.get('companyName', '') or item.get('company', '') or 'Dice Listing'
            
            # Location
            loc = item.get('jobLocation', {})
            if isinstance(loc, dict):
                location = loc.get('displayName', '') or loc.get('city', '')
            elif isinstance(loc, str):
                location = loc
            else:
                location = default_location
            
            # URL
            job_id = item.get('id', '') or item.get('jobId', '')
            url = item.get('detailsPageUrl', '') or item.get('url', '')
            if not url and job_id:
                url = f"https://www.dice.com/job-detail/{job_id}"
            elif url and not url.startswith('http'):
                url = f"https://www.dice.com{url}"
            
            # Salary
            salary = 'Not specified'
            sal_min = item.get('salary', '')
            sal_max = item.get('salaryMax', '')
            if sal_min and sal_max:
                salary = f"${sal_min:,} - ${sal_max:,}"
            elif sal_min:
                salary = f"${sal_min:,}+"
            
            # Date
            posted_date = self._format_date(item.get('postedDate', ''))
            
            return {
                'title': title,
                'company': company,
                'url': url,
                'location': location or default_location,
                'description': item.get('summary', '')[:500],
                'posted_date': posted_date,
                'posted_timestamp': self._get_timestamp(item.get('postedDate', '')),
                'salary': salary,
                'salary_numeric': 0,
                'job_type': item.get('employmentType', 'Full-time'),
                'source': 'DICE',
                'remote': item.get('isRemote', remote),
                'work_type': 'Remote' if item.get('isRemote', remote) else 'On-site'
            }
        except:
            return None
    
    def _parse_html_card(self, card, default_location, remote):
        """Parse an HTML job card"""
        try:
            title_el = card.select_one('[data-cy="card-title"], h5, .card-title, a')
            company_el = card.select_one('[data-cy="search-result-company-name"], .company')
            location_el = card.select_one('[data-cy="search-result-location"], .location')
            link_el = card.select_one('a[href*="/job-detail/"]') or card if card.name == 'a' else None
            
            title = title_el.get_text(strip=True) if title_el else ''
            if not title:
                return None
            
            url = ''
            if link_el:
                url = link_el.get('href', '')
                if not url.startswith('http'):
                    url = f"https://www.dice.com{url}"
            
            return {
                'title': title,
                'company': company_el.get_text(strip=True) if company_el else 'Dice Listing',
                'url': url,
                'location': location_el.get_text(strip=True) if location_el else default_location,
                'description': card.get_text()[:300],
                'posted_date': 'Recently',
                'posted_timestamp': 0,
                'salary': 'Not specified',
                'salary_numeric': 0,
                'job_type': 'Full-time',
                'source': 'DICE',
                'remote': remote,
                'work_type': 'Remote' if remote else 'On-site'
            }
        except:
            return None
    
    def _format_date(self, date_str):
        """Format date to relative time"""
        try:
            if not date_str:
                return 'Recently'
            dt = datetime.fromisoformat(str(date_str).replace('Z', '+00:00'))
            days = (datetime.now() - dt.replace(tzinfo=None)).days
            if days == 0: return 'Today'
            elif days == 1: return '1 day ago'
            elif days < 7: return f'{days} days ago'
            elif days < 30:
                w = days // 7
                return f'{w} week{"s" if w > 1 else ""} ago'
            else: return dt.strftime('%B %d, %Y')
        except:
            return 'Recently'
    
    def _get_timestamp(self, date_str):
        """Convert date to Unix timestamp"""
        try:
            if not date_str: return 0
            dt = datetime.fromisoformat(str(date_str).replace('Z', '+00:00'))
            return int(dt.replace(tzinfo=None).timestamp())
        except:
            return 0
