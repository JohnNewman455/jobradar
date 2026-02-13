"""
SN Pro Jobs Scraper - 2026 WORKING VERSION
Uses their Supabase API directly (62,000+ ServiceNow jobs in database)
"""

try:
    import requests
except ImportError:
    requests = None

from datetime import datetime
import time


class SNProAPIScraper:
    """Scraper for SN Pro Jobs using their Supabase API (62K+ jobs)"""
    
    def __init__(self):
        self.name = "SN Pro Jobs"
        self.supabase_url = "https://zddplrqvbnhvpewaqrwg.supabase.co"
        self.supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpkZHBscnF2Ym5odnBld2FxcndnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjU1ODg5MjgsImV4cCI6MjA4MTE2NDkyOH0.sUKdKSgPmBONAIJC4iyLSpXCQm3oU2ZLRkuJ20aMq5Y"
    
    def scrape(self, job_title, location, remote=False):
        """
        Query SN Pro's Supabase database for ServiceNow jobs
        
        Args:
            job_title: Job title to search for
            location: Location filter
            remote: Remote filter
        
        Returns:
            List of job dictionaries
        """
        jobs = []
        
        print(f"🔍 {self.name}: Querying Supabase API for '{job_title}'...")
        
        headers = {
            'apikey': self.supabase_key,
            'Authorization': f'Bearer {self.supabase_key}',
            'Content-Type': 'application/json',
        }
        
        # Build search query using full-text search or ILIKE
        # The table has: job_title, company_name, location_type, cities_lookup, 
        # countries_lookup, salary_range, application_link, description_html,
        # date_posted, company_logo_url, etc.
        
        try:
            # Strategy 1: Use search_text column with full-text search
            select_fields = (
                'id,job_title,company_name,company_logo_url,application_link,'
                'cities_lookup,countries_lookup,location_type,salary_range,'
                'salary_range_display,date_posted,description_html,'
                'requirements_summary,job_type,emp_type_mapped,role_type,'
                'app_lookup,certs_lookup,sn_relevance_score,slug,detail_page_url'
            )
            
            # Build location filter
            location_filter = ''
            loc_lower = location.lower() if location else ''
            if loc_lower and loc_lower not in ('remote', 'worldwide', ''):
                if 'canada' in loc_lower:
                    location_filter = ',countries_lookup.ilike.*Canada*'
                elif 'us' in loc_lower or 'united states' in loc_lower or 'usa' in loc_lower:
                    location_filter = ',countries_lookup.ilike.*United States*'
                else:
                    location_filter = f',or(cities_lookup.ilike.*{location}*,countries_lookup.ilike.*{location}*)'
            
            # Remote filter — skip the location_type column filter since Supabase
            # stores it as a UUID/foreign-key, not text.  We'll filter client-side instead.
            filter_remote_client = bool(remote)
            
            # Main search: job_title contains the search term
            # Split search into keywords for better matching
            keywords = job_title.split()
            main_keyword = keywords[0] if keywords else job_title
            
            params = {
                'select': select_fields,
                'job_title': f'ilike.*{main_keyword}*',
                'limit': '100',
                'order': 'date_posted.desc.nullslast',
            }
            
            # Add location filter if specified
            if location_filter and 'or(' not in location_filter:
                key, value = location_filter.lstrip(',').split('.', 1)
                params[key] = value
            
            # (remote filter applied client-side after fetch)
            
            time.sleep(0.5)  # Brief delay
            
            response = requests.get(
                f'{self.supabase_url}/rest/v1/Job%20Data',
                params=params,
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   📊 {self.name}: Got {len(data)} results from Supabase")
                
                for item in data:
                    job = self._parse_supabase_job(item, location, remote)
                    if job:
                        jobs.append(job)
            else:
                print(f"   ⚠️ {self.name}: Supabase query 1 failed ({response.status_code})")
                print(f"   Response: {response.text[:200]}")
            
            # Strategy 2: If few results, try broader search
            if len(jobs) < 20:
                params2 = {
                    'select': select_fields,
                    'or': f'(job_title.ilike.*{main_keyword}*,app_lookup.ilike.*{main_keyword}*,role_type.ilike.*{main_keyword}*)',
                    'limit': '100',
                    'order': 'date_posted.desc.nullslast',
                }
                
                if remote:
                    params2['location_type'] = 'ilike.*Remote*'
                
                response2 = requests.get(
                    f'{self.supabase_url}/rest/v1/Job%20Data',
                    params=params2,
                    headers=headers,
                    timeout=15
                )
                
                if response2.status_code == 200:
                    data2 = response2.json()
                    existing_ids = {j.get('url', '') for j in jobs}
                    
                    for item in data2:
                        job = self._parse_supabase_job(item, location, remote)
                        if job and job['url'] not in existing_ids:
                            jobs.append(job)
                            existing_ids.add(job['url'])
                    
                    print(f"   📊 {self.name}: Broader search found {len(data2)} more results")
            
            if jobs:
                print(f"✅ {self.name}: Found {len(jobs)} jobs total")
            else:
                print(f"⚠️ {self.name}: No matching jobs found")
            
            return jobs
            
        except requests.Timeout:
            print(f"❌ {self.name}: Request timeout")
            return []
        except Exception as e:
            print(f"❌ {self.name}: Error - {str(e)[:100]}")
            return []
    
    def _parse_supabase_job(self, item, default_location, remote):
        """Parse a Supabase job record into standard format"""
        try:
            title = item.get('job_title', '')
            if not title:
                return None
            
            company = item.get('company_name', '') or 'ServiceNow Partner'
            
            # Filter out UUIDs that sometimes appear as company names
            import re as _re
            _uuid_pat = _re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-', _re.I)
            _uuid_full = _re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', _re.I)
            if _uuid_pat.match(str(company)):
                company = 'ServiceNow Partner'
            if len(company) < 2:
                company = 'ServiceNow Partner'
            
            # Build location string
            city = item.get('cities_lookup', '')
            country = item.get('countries_lookup', '')
            loc_type = item.get('location_type', '')
            
            location_parts = []
            if city:
                location_parts.append(city)
            if country:
                location_parts.append(country)
            job_location = ', '.join(location_parts) if location_parts else default_location
            
            # Is remote?
            is_remote = 'remote' in (loc_type or '').lower() or 'remote' in (job_location or '').lower()
            
            # Salary
            salary = item.get('salary_range_display', '') or item.get('salary_range', '') or 'Not specified'
            
            # Posted date
            date_posted = item.get('date_posted', '')
            posted_date = self._format_date(date_posted)
            
            # URL
            app_link = item.get('application_link', '')
            detail_url = item.get('detail_page_url', '')
            slug = item.get('slug', '')
            
            if app_link:
                url = app_link
            elif detail_url:
                url = f"https://browse.snpro.jobs{detail_url}" if not detail_url.startswith('http') else detail_url
            elif slug:
                url = f"https://browse.snpro.jobs/jobs/{slug}"
            else:
                url = 'https://browse.snpro.jobs'
            
            # Description
            description = item.get('requirements_summary', '') or ''
            if not description:
                desc_html = item.get('description_html', '')
                if desc_html:
                    from bs4 import BeautifulSoup
                    description = BeautifulSoup(desc_html, 'html.parser').get_text()[:500]
            
            # Apps/certifications
            apps = item.get('app_lookup', '')
            certs = item.get('certs_lookup', '')
            if apps:
                description = f"ServiceNow Apps: {apps}. {description}"
            if certs:
                description = f"Certs: {certs}. {description}"
            
            # Job type
            job_type = item.get('emp_type_mapped', '') or item.get('job_type', '') or 'Full-time'
            
            # Work type
            work_type = 'Remote' if is_remote else 'On-site'
            if 'hybrid' in (loc_type or '').lower():
                work_type = 'Hybrid'
            
            return {
                'title': title,
                'company': company,
                'url': url if not _uuid_full.fullmatch(str(url).strip()) else 'https://browse.snpro.jobs',
                'location': job_location if not _uuid_full.fullmatch(str(job_location).strip()) else 'Not Listed',
                'description': _uuid_full.sub('', description)[:500],
                'posted_date': posted_date,
                'posted_timestamp': self._get_timestamp(date_posted),
                'salary': salary,
                'salary_numeric': 0,
                'job_type': job_type,
                'source': 'SNPRO',
                'remote': is_remote or remote,
                'work_type': work_type,
                'company_logo': item.get('company_logo_url', ''),
            }
            
        except Exception as e:
            return None
    
    def _format_date(self, date_str):
        """Format date to relative time"""
        try:
            if not date_str:
                return 'Recently'
            
            # Parse ISO date
            if 'T' in str(date_str):
                job_date = datetime.fromisoformat(str(date_str).replace('Z', '+00:00'))
            else:
                job_date = datetime.strptime(str(date_str)[:10], '%Y-%m-%d')
            
            now = datetime.now()
            if hasattr(job_date, 'tzinfo') and job_date.tzinfo:
                job_date = job_date.replace(tzinfo=None)
            
            days = (now - job_date).days
            
            if days < 0:
                return 'Today'
            elif days == 0:
                return 'Today'
            elif days == 1:
                return '1 day ago'
            elif days < 7:
                return f'{days} days ago'
            elif days < 30:
                w = days // 7
                return f'{w} week{"s" if w > 1 else ""} ago'
            else:
                m = days // 30
                return f'{m} month{"s" if m > 1 else ""} ago'
        except:
            return 'Recently'
    
    def _get_timestamp(self, date_str):
        """Convert date to Unix timestamp"""
        try:
            if not date_str:
                return 0
            if 'T' in str(date_str):
                dt = datetime.fromisoformat(str(date_str).replace('Z', '+00:00'))
            else:
                dt = datetime.strptime(str(date_str)[:10], '%Y-%m-%d')
            return int(dt.timestamp())
        except:
            return 0


# Alias for backward compatibility
SNProScraper = SNProAPIScraper
