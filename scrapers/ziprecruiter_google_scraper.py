"""
ZipRecruiter Scraper - 2026 Working Version
Uses curl_cffi to bypass anti-bot + parses embedded JSON data
Falls back to /Jobs/ HTML parsing if needed
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


class ZipRecruiterGoogleScraper:
    """Scraper for ZipRecruiter using embedded JSON (bypasses anti-bot with curl_cffi)"""
    
    def __init__(self):
        self.name = "ZipRecruiter"
    
    def scrape(self, job_title, location, remote=False):
        """
        Scrape ZipRecruiter jobs using multiple strategies
        
        Strategy 1: curl_cffi + embedded JSON from /jobs-search
        Strategy 2: curl_cffi + HTML/LD+JSON from /Jobs/ page  
        Strategy 3: Regular requests + LD+JSON as last resort
        """
        print(f"🔎 {self.name}: Searching for '{job_title}' in '{location}'...")
        
        jobs = []
        
        # Strategy 1: Embedded JSON (best - gets structured data)
        if CURL_CFFI_AVAILABLE:
            jobs = self._scrape_embedded_json(job_title, location, remote)
            if jobs:
                print(f"✅ {self.name}: Found {len(jobs)} jobs via embedded JSON")
                return jobs
        
            # Strategy 2: HTML parsing from /Jobs/ page
            jobs = self._scrape_jobs_page(job_title, location, remote)
            if jobs:
                print(f"✅ {self.name}: Found {len(jobs)} jobs via HTML parse")
                return jobs
        
        # Strategy 3: Regular requests fallback
        jobs = self._scrape_fallback(job_title, location, remote)
        if jobs:
            print(f"✅ {self.name}: Found {len(jobs)} jobs via fallback")
            return jobs
            
        print(f"⚠️ {self.name}: No jobs found across all strategies")
        return []
    
    def _scrape_embedded_json(self, job_title, location, remote):
        """Extract job data from hydrateJobCardsResponse embedded JSON"""
        jobs = []
        try:
            url = f"https://www.ziprecruiter.com/jobs-search?search={quote(job_title)}&location={quote(location)}"
            if remote:
                url += "&refine_by_location_type=only_remote"
            
            delay = random.uniform(1, 3)
            print(f"   ⏳ Waiting {delay:.1f}s...")
            time.sleep(delay)
            
            response = cffi_requests.get(url, impersonate="chrome120", timeout=20)
            
            if response.status_code != 200:
                print(f"   ⚠️ {self.name}: Status {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the script containing hydrateJobCardsResponse
            for script in soup.select('script'):
                text = script.string or ''
                if 'hydrateJobCardsResponse' in text:
                    try:
                        data = json.loads(text)
                        job_cards = data.get('hydrateJobCardsResponse', {}).get('jobCards', [])
                        
                        if not job_cards:
                            continue
                        
                        print(f"   📊 {self.name}: Found {len(job_cards)} jobs in embedded JSON")
                        
                        for card in job_cards:
                            try:
                                posted_at = card.get('status', {}).get('postedAtUtc', '')
                                pay = card.get('pay', {})
                                
                                loc_types = card.get('locationTypes', [])
                                is_remote = any(
                                    lt.get('label', '').lower() == 'remote' 
                                    for lt in loc_types
                                ) if loc_types else False
                                
                                emp_types = card.get('employmentTypes', [])
                                job_type = emp_types[0].get('label', 'Full-time') if emp_types else 'Full-time'
                                
                                loc_data = card.get('location', {})
                                job_location = loc_data.get('city', '')
                                if loc_data.get('state'):
                                    job_location += f", {loc_data['state']}"
                                if not job_location:
                                    job_location = location
                                
                                redirect_url = card.get('jobRedirectPageUrl', '')
                                if redirect_url and not redirect_url.startswith('http'):
                                    redirect_url = f"https://www.ziprecruiter.com{redirect_url}"
                                
                                job = {
                                    'title': card.get('title', 'Unknown'),
                                    'company': card.get('company', 'ZipRecruiter Listing'),
                                    'url': redirect_url,
                                    'location': job_location,
                                    'description': card.get('shortDescription', '')[:500],
                                    'posted_date': self._format_date(posted_at),
                                    'posted_timestamp': self._get_timestamp(posted_at),
                                    'salary': self._format_salary(pay),
                                    'salary_numeric': 0,
                                    'job_type': job_type,
                                    'source': 'ZIPRECRUITER',
                                    'remote': is_remote or remote,
                                    'work_type': 'Remote' if (is_remote or remote) else 'On-site'
                                }
                                jobs.append(job)
                            except Exception:
                                continue
                        
                        return jobs
                    except json.JSONDecodeError:
                        continue
            
        except Exception as e:
            print(f"   ❌ {self.name}: Embedded JSON error - {str(e)[:100]}")
        return jobs
    
    def _scrape_jobs_page(self, job_title, location, remote):
        """Parse the /Jobs/ page using LD+JSON structured data"""
        jobs = []
        try:
            slug = job_title.replace(' ', '-')
            url = f"https://www.ziprecruiter.com/Jobs/{quote(slug)}"
            
            time.sleep(random.uniform(1, 3))
            response = cffi_requests.get(url, impersonate="chrome120", timeout=20)
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Parse LD+JSON structured data (ItemList of JobPostings)
            for script in soup.select('script[type="application/ld+json"]'):
                try:
                    data = json.loads(script.text)
                    if isinstance(data, dict) and data.get('@type') == 'ItemList':
                        items = data.get('itemListElement', [])
                        for item in items:
                            listing = item.get('item', item)
                            if listing.get('@type') == 'JobPosting':
                                jobs.append({
                                    'title': listing.get('title', 'Unknown'),
                                    'company': listing.get('hiringOrganization', {}).get('name', 'ZipRecruiter'),
                                    'url': listing.get('url', ''),
                                    'location': self._extract_ld_location(listing),
                                    'description': BeautifulSoup(listing.get('description', ''), 'html.parser').get_text()[:500],
                                    'posted_date': self._format_date(listing.get('datePosted', '')),
                                    'posted_timestamp': self._get_timestamp(listing.get('datePosted', '')),
                                    'salary': self._extract_ld_salary(listing),
                                    'salary_numeric': 0,
                                    'job_type': listing.get('employmentType', 'Full-time'),
                                    'source': 'ZIPRECRUITER',
                                    'remote': remote,
                                    'work_type': 'Remote' if remote else 'On-site'
                                })
                except Exception:
                    continue
            
            if jobs:
                return jobs
            
            # Fallback: parse article elements
            articles = soup.select('article')
            for article in articles[:50]:
                try:
                    title_el = article.select_one('h2, [class*="title"], a[class*="title"]')
                    company_el = article.select_one('[class*="company"]')
                    link_el = article.select_one('a[href]')
                    location_el = article.select_one('[class*="location"]')
                    
                    if title_el and link_el:
                        href = link_el.get('href', '')
                        if not href.startswith('http'):
                            href = f"https://www.ziprecruiter.com{href}"
                        
                        jobs.append({
                            'title': title_el.text.strip(),
                            'company': company_el.text.strip() if company_el else 'ZipRecruiter',
                            'url': href,
                            'location': location_el.text.strip() if location_el else location,
                            'description': article.get_text()[:300],
                            'posted_date': 'Recently',
                            'posted_timestamp': 0,
                            'salary': 'Not specified',
                            'salary_numeric': 0,
                            'job_type': 'Full-time',
                            'source': 'ZIPRECRUITER',
                            'remote': remote,
                            'work_type': 'Remote' if remote else 'On-site'
                        })
                except Exception:
                    continue
            
        except Exception as e:
            print(f"   ❌ {self.name}: HTML parse error - {str(e)[:100]}")
        return jobs
    
    def _scrape_fallback(self, job_title, location, remote):
        """Last resort: regular requests + LD+JSON"""
        try:
            url = f"https://www.ziprecruiter.com/Jobs/{quote(job_title.replace(' ', '-'))}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml',
            }
            time.sleep(random.uniform(2, 4))
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            jobs = []
            
            for script in soup.select('script[type="application/ld+json"]'):
                try:
                    data = json.loads(script.text)
                    if isinstance(data, dict) and data.get('@type') == 'ItemList':
                        for item in data.get('itemListElement', []):
                            listing = item.get('item', item)
                            if listing.get('@type') == 'JobPosting':
                                jobs.append({
                                    'title': listing.get('title', 'Unknown'),
                                    'company': listing.get('hiringOrganization', {}).get('name', 'ZipRecruiter'),
                                    'url': listing.get('url', ''),
                                    'location': self._extract_ld_location(listing),
                                    'description': BeautifulSoup(listing.get('description', ''), 'html.parser').get_text()[:500],
                                    'posted_date': self._format_date(listing.get('datePosted', '')),
                                    'posted_timestamp': 0,
                                    'salary': self._extract_ld_salary(listing),
                                    'salary_numeric': 0,
                                    'job_type': 'Full-time',
                                    'source': 'ZIPRECRUITER',
                                    'remote': remote,
                                    'work_type': 'Remote' if remote else 'On-site'
                                })
                except Exception:
                    continue
            return jobs
        except Exception as e:
            print(f"   ❌ {self.name}: Fallback error - {str(e)[:100]}")
            return []
    
    def _extract_ld_location(self, listing):
        """Extract location from LD+JSON JobPosting"""
        loc = listing.get('jobLocation', {})
        if isinstance(loc, dict):
            addr = loc.get('address', {})
            if isinstance(addr, dict):
                parts = [addr.get('addressLocality', ''), addr.get('addressRegion', '')]
                return ', '.join(p for p in parts if p) or 'Unknown'
        return 'Unknown'
    
    def _extract_ld_salary(self, listing):
        """Extract salary from LD+JSON"""
        salary = listing.get('baseSalary', {})
        if isinstance(salary, dict):
            value = salary.get('value', {})
            if isinstance(value, dict):
                min_val = value.get('minValue', '')
                max_val = value.get('maxValue', '')
                if min_val and max_val:
                    return f"${float(min_val):,.0f} - ${float(max_val):,.0f}"
                elif min_val:
                    return f"${float(min_val):,.0f}+"
        return 'Not specified'
    
    def _format_salary(self, pay_data):
        """Format salary from ZipRecruiter pay metadata"""
        try:
            meta = pay_data.get('metadata', {})
            min_a = meta.get('minAnnualSalary')
            max_a = meta.get('maxAnnualSalary')
            min_h = meta.get('minHourlySalary')
            max_h = meta.get('maxHourlySalary')
            
            if min_a and max_a:
                return f"${min_a:,.0f} - ${max_a:,.0f}/yr"
            elif min_h and max_h:
                return f"${min_h:.0f} - ${max_h:.0f}/hr"
            
            display = meta.get('salaryDisplayString', '')
            if display:
                return display
        except Exception:
            pass
        return 'Not specified'
    
    def _format_date(self, date_str):
        """Format ISO datetime to relative time"""
        try:
            if not date_str:
                return 'Recently'
            job_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            now = datetime.now(job_date.tzinfo)
            days = (now - job_date).days
            if days == 0: return 'Today'
            elif days == 1: return '1 day ago'
            elif days < 7: return f'{days} days ago'
            elif days < 30:
                w = days // 7
                return f'{w} week{"s" if w > 1 else ""} ago'
            else:
                m = days // 30
                return f'{m} month{"s" if m > 1 else ""} ago'
        except:
            return 'Recently'
    
    def _get_timestamp(self, date_str):
        """Convert date string to Unix timestamp"""
        try:
            if not date_str: return 0
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return int(dt.timestamp())
        except:
            return 0
