"""
Unified Job Scraper using JobSpy library
Supports: Indeed, LinkedIn, ZipRecruiter, Glassdoor
"""

try:
    from jobspy import scrape_jobs
    JOBSPY_AVAILABLE = True
except ImportError:
    JOBSPY_AVAILABLE = False

from datetime import datetime
import time


class JobSpyScraper:
    """Unified scraper using JobSpy library for multiple job sites"""
    
    def __init__(self, sites=["indeed", "linkedin", "zip_recruiter", "glassdoor"]):
        """
        Initialize JobSpy scraper
        
        Args:
            sites: List of sites to scrape (indeed, linkedin, zip_recruiter, glassdoor)
        """
        self.sites = sites
        self.name = f"JobSpy ({', '.join([s.title() for s in sites])})"
        
        if not JOBSPY_AVAILABLE:
            print("⚠️  JobSpy not installed. Run: pip install python-jobspy")
    
    def scrape(self, job_title, location, remote=False):
        """
        Scrape jobs using JobSpy
        
        Args:
            job_title: Job title to search for
            location: Location (city, state, or country)
            remote: Whether to search for remote jobs
            
        Returns:
            List of job dictionaries
        """
        if not JOBSPY_AVAILABLE:
            print(f"❌ {self.name}: JobSpy not available")
            return []
        
        jobs = []
        
        try:
            print(f"🔍 {self.name}: Searching for '{job_title}' in '{location}'...")
            print(f"📡 {self.name}: Contacting job boards (this may take 5-10 seconds)...")
            start_time = time.time()
            
            # Map location to country for Indeed/Glassdoor
            country_indeed = self._map_location_to_country(location)
            
            # Call JobSpy
            df = scrape_jobs(
                site_name=self.sites,
                search_term=job_title,
                location=location,
                results_wanted=1000,  # INCREASED to 1000 for Indeed 100+ jobs
                hours_old=8760,  # 365 days (1 year) - get ALL jobs regardless of age
                country_indeed=country_indeed,
                is_remote=remote,
                verbose=0  # Suppress JobSpy logs
            )
            
            elapsed = time.time() - start_time
            
            if df is None or df.empty:
                print(f"❌ {self.name}: No '{job_title}' jobs found in '{location}' ({elapsed:.1f}s)")
                return []
            
            # Convert DataFrame to our job format
            for _, row in df.iterrows():
                try:
                    location_str = self._format_location(row)
                    is_remote = bool(row.get('is_remote', False))
                    
                    # Detect work type from location/description
                    work_type = self._detect_work_type(location_str, str(row.get('description', '')), is_remote)
                    
                    job = {
                        'title': str(row.get('title', 'N/A')),
                        'company': str(row.get('company', 'N/A')),
                        'location': location_str,
                        'description': str(row.get('description', ''))[:500],  # Truncate
                        'url': str(row.get('job_url', '')),
                        'date_posted': self._format_date(row.get('date_posted')),
                        'posted_timestamp': self._get_timestamp(row.get('date_posted')),
                        'job_type': str(row.get('job_type', 'Full-time')),
                        'salary': self._format_salary(row),
                        'salary_numeric': self._get_numeric_salary(row),
                        'source': str(row.get('site', 'JobSpy')).upper(),
                        'remote': is_remote,
                        'work_type': work_type
                    }
                    jobs.append(job)
                except Exception as e:
                    print(f"⚠️  {self.name}: Error parsing job: {e}")
                    continue
            
            print(f"✅ {self.name}: Found {len(jobs)} jobs ({elapsed:.1f}s)")
            
        except Exception as e:
            print(f"❌ {self.name}: Error - {e}")
        
        return jobs
    
    def _map_location_to_country(self, location):
        """Map location string to Indeed country parameter"""
        location_lower = location.lower()
        
        # Common country mappings
        country_map = {
            'canada': 'Canada',
            'ca': 'Canada',
            'ontario': 'Canada',
            'quebec': 'Canada',
            'british columbia': 'Canada',
            'alberta': 'Canada',
            'usa': 'USA',
            'us': 'USA',
            'united states': 'USA',
            'california': 'USA',
            'new york': 'USA',
            'texas': 'USA',
            'florida': 'USA',
            'uk': 'UK',
            'united kingdom': 'UK',
            'london': 'UK',
            'australia': 'Australia',
            'sydney': 'Australia',
            'india': 'India',
            'bangalore': 'India',
            'mumbai': 'India'
        }
        
        for key, country in country_map.items():
            if key in location_lower:
                return country
        
        return 'USA'  # Default
    
    def _format_location(self, row):
        """Format location from DataFrame row"""
        parts = []
        
        if row.get('city'):
            parts.append(str(row['city']))
        if row.get('state'):
            parts.append(str(row['state']))
        if row.get('country'):
            parts.append(str(row['country']))
        
        return ', '.join(parts) if parts else 'Remote'
    
    def _format_date(self, date_posted):
        """Format date_posted to readable string"""
        if not date_posted:
            return 'Recently'
        
        try:
            if isinstance(date_posted, str):
                # Try to parse string dates
                try:
                    from dateutil import parser
                    date_posted = parser.parse(date_posted)
                except:
                    return date_posted
            
            # If it's a datetime object
            if hasattr(date_posted, 'strftime'):
                days_ago = (datetime.now() - date_posted).days
                if days_ago == 0:
                    return 'Today'
                elif days_ago == 1:
                    return '1 day ago'
                elif days_ago < 7:
                    return f'{days_ago} days ago'
                elif days_ago < 30:
                    weeks = days_ago // 7
                    return f'{weeks} week{"s" if weeks > 1 else ""} ago'
                else:
                    return date_posted.strftime('%B %d, %Y')
        except:
            pass
        
        return 'Recently'
    
    def _get_timestamp(self, date_posted):
        """Get numeric timestamp for sorting"""
        try:
            if isinstance(date_posted, str):
                try:
                    from dateutil import parser
                    date_posted = parser.parse(date_posted)
                except:
                    return 0
            
            if hasattr(date_posted, 'timestamp'):
                return date_posted.timestamp()
        except:
            pass
        
        return 0
    
    def _get_numeric_salary(self, row):
        """Get numeric salary value for sorting"""
        min_amt = row.get('min_amount', 0)
        max_amt = row.get('max_amount', 0)
        
        if max_amt and max_amt > 0:
            return float(max_amt)
        elif min_amt and min_amt > 0:
            return float(min_amt)
        
        return 0
    
    def _detect_work_type(self, location, description, is_remote):
        """Detect if job is Remote, Hybrid, or On-site"""
        location_lower = location.lower() if location else ''
        desc_lower = description.lower() if description else ''
        
        # Check for remote
        if is_remote or 'remote' in location_lower or 'remote' in desc_lower:
            return 'Remote'
        
        # Check for hybrid
        if 'hybrid' in location_lower or 'hybrid' in desc_lower:
            return 'Hybrid'
        
        # Default to on-site
        return 'On-site'
    
    def _format_salary(self, row):
        """Format salary information"""
        min_amt = row.get('min_amount')
        max_amt = row.get('max_amount')
        interval = row.get('interval', 'yearly')
        
        if not min_amt and not max_amt:
            return 'N/A'
        
        # Format amounts
        def format_amount(amt):
            if amt and amt > 0:
                return f"${int(amt):,}"
            return None
        
        min_str = format_amount(min_amt)
        max_str = format_amount(max_amt)
        
        if min_str and max_str:
            salary = f"{min_str} - {max_str}"
        elif min_str:
            salary = f"From {min_str}"
        elif max_str:
            salary = f"Up to {max_str}"
        else:
            return 'N/A'
        
        # Add interval
        if interval:
            interval_map = {
                'yearly': '/year',
                'monthly': '/month',
                'weekly': '/week',
                'daily': '/day',
                'hourly': '/hr'
            }
            salary += interval_map.get(str(interval).lower(), '')
        
        return salary


# Individual site scrapers for backward compatibility
class JobSpyIndeedScraper(JobSpyScraper):
    """JobSpy scraper for Indeed only"""
    def __init__(self):
        super().__init__(sites=["indeed"])
        self.name = "Indeed (JobSpy)"


class JobSpyLinkedInScraper(JobSpyScraper):
    """JobSpy scraper for LinkedIn only"""
    def __init__(self):
        super().__init__(sites=["linkedin"])
        self.name = "LinkedIn (JobSpy)"
    
    def scrape(self, job_title, location, remote=False):
        """Override scrape to increase results for LinkedIn"""
        if not JOBSPY_AVAILABLE:
            print(f"❌ {self.name}: JobSpy not available")
            return []
        
        jobs = []
        
        try:
            print(f"🔍 {self.name}: Searching for '{job_title}' in '{location}'...")
            start_time = time.time()
            
            country_indeed = self._map_location_to_country(location)
            
            # Call JobSpy with LinkedIn-optimized parameters
            df = scrape_jobs(
                site_name=["linkedin"],
                search_term=job_title,
                location=location,
                results_wanted=1000,  # Get MORE LinkedIn results
                hours_old=8760,  # 365 days
                country_indeed=country_indeed,
                is_remote=remote,
                linkedin_fetch_description=False,  # Faster without full descriptions
                verbose=0
            )
            
            elapsed = time.time() - start_time
            
            if df is None or df.empty:
                print(f"❌ {self.name}: No jobs found ({elapsed:.1f}s)")
                return []
            
            # Convert to our format
            for _, row in df.iterrows():
                try:
                    location_str = self._format_location(row)
                    is_remote = bool(row.get('is_remote', False))
                    work_type = self._detect_work_type(location_str, str(row.get('description', '')), is_remote)
                    
                    job = {
                        'title': str(row.get('title', 'N/A')),
                        'company': str(row.get('company', 'N/A')),
                        'location': location_str,
                        'description': str(row.get('description', ''))[:500],
                        'url': str(row.get('job_url', '')),
                        'date_posted': self._format_date(row.get('date_posted')),
                        'posted_timestamp': self._get_timestamp(row.get('date_posted')),
                        'job_type': str(row.get('job_type', 'Full-time')),
                        'salary': self._format_salary(row),
                        'salary_numeric': self._get_numeric_salary(row),
                        'source': 'LINKEDIN',
                        'remote': is_remote,
                        'work_type': work_type
                    }
                    jobs.append(job)
                except Exception as e:
                    continue
            
            print(f"✅ {self.name}: Found {len(jobs)} jobs ({elapsed:.1f}s)")
            
        except Exception as e:
            print(f"❌ {self.name}: Error - {e}")
        
        return jobs


class JobSpyZipRecruiterScraper(JobSpyScraper):
    """JobSpy scraper for ZipRecruiter only"""
    def __init__(self):
        super().__init__(sites=["zip_recruiter"])
        self.name = "ZipRecruiter (JobSpy)"
    
    def scrape(self, job_title, location, remote=False):
        """Override scrape with ZipRecruiter-optimized parameters"""
        if not JOBSPY_AVAILABLE:
            print(f"❌ {self.name}: JobSpy not available")
            return []
        
        jobs = []
        
        try:
            print(f"🔍 {self.name}: Searching for '{job_title}' in '{location}'...")
            start_time = time.time()
            
            # ZipRecruiter works best with US locations
            if not any(x in location.lower() for x in ['usa', 'us', 'united states', 'america']):
                location = f"{location}, USA"  # Add USA for better results
            
            # Call JobSpy
            df = scrape_jobs(
                site_name=["zip_recruiter"],
                search_term=job_title,
                location=location,
                results_wanted=500,  # ZipRecruiter has good volume
                hours_old=8760,
                country_indeed="USA",  # ZipRecruiter is US-focused
                is_remote=remote,
                verbose=0
            )
            
            elapsed = time.time() - start_time
            
            if df is None or df.empty:
                print(f"❌ {self.name}: No jobs found ({elapsed:.1f}s)")
                return []
            
            # Convert to our format
            for _, row in df.iterrows():
                try:
                    location_str = self._format_location(row)
                    is_remote = bool(row.get('is_remote', False))
                    work_type = self._detect_work_type(location_str, str(row.get('description', '')), is_remote)
                    
                    job = {
                        'title': str(row.get('title', 'N/A')),
                        'company': str(row.get('company', 'N/A')),
                        'location': location_str,
                        'description': str(row.get('description', ''))[:500],
                        'url': str(row.get('job_url', '')),
                        'date_posted': self._format_date(row.get('date_posted')),
                        'posted_timestamp': self._get_timestamp(row.get('date_posted')),
                        'job_type': str(row.get('job_type', 'Full-time')),
                        'salary': self._format_salary(row),
                        'salary_numeric': self._get_numeric_salary(row),
                        'source': 'ZIPRECRUITER',
                        'remote': is_remote,
                        'work_type': work_type
                    }
                    jobs.append(job)
                except Exception as e:
                    continue
            
            print(f"✅ {self.name}: Found {len(jobs)} jobs ({elapsed:.1f}s)")
            
        except Exception as e:
            print(f"❌ {self.name}: Error - {e}")
        
        return jobs
    
    def _map_location_to_country(self, location):
        """ZipRecruiter works best with USA locations"""
        # ZipRecruiter is primarily US/Canada
        return 'USA'


class JobSpyGlassdoorScraper(JobSpyScraper):
    """JobSpy scraper for Glassdoor only"""
    def __init__(self):
        super().__init__(sites=["glassdoor"])
        self.name = "Glassdoor (JobSpy)"


class JobSpyAllScraper(JobSpyScraper):
    """JobSpy scraper for all supported sites"""
    def __init__(self):
        super().__init__(sites=["indeed", "linkedin", "zip_recruiter", "glassdoor"])
        self.name = "JobSpy (All Sites)"
