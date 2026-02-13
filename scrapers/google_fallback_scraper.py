try:
    import requests
except ImportError:
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

import time
import random
from urllib.parse import quote
from datetime import datetime

class GoogleFallbackScraper:
    """
    Google Fallback Scraper - Uses Google Search to find jobs when direct scrapers fail
    This is a backup strategy that queries Google with site-specific searches
    """
    
    def __init__(self):
        # Map scraper names to their actual domains
        self.site_domains = {
            'dice': 'dice.com',
            'ziprecruiter': 'ziprecruiter.com',
            'jobspy_ziprecruiter': 'ziprecruiter.com',
            'servicenow': 'careers.servicenow.com',
            'servicenow_careers': 'careers.servicenow.com',
            'glassdoor': 'glassdoor.com',
            'jobspy_glassdoor': 'glassdoor.com',
            'simplyhired': 'simplyhired.com',
            'simplyhired_ca': 'simplyhired.ca',
            'indeed': 'indeed.com',
            'jobspy_indeed': 'indeed.com',
            'linkedin': 'linkedin.com/jobs',
            'jobspy_linkedin': 'linkedin.com/jobs',
            'nelsonfrank': 'nelsonfrank.com',
            'nelson_frank': 'nelsonfrank.com',
            'snpro': 'snpro.jobs',
            'sn_pro_jobs': 'snpro.jobs',
            'talent': 'talent.com',
            'talent_com': 'talent.com',
            'weworkremotely': 'weworkremotely.com',
            'remoteok': 'remoteok.com'
        }
    
    def scrape(self, target_site, job_title, location):
        """
        Use Google to find jobs from a specific site
        
        Args:
            target_site: Name of the site (e.g., 'dice', 'ziprecruiter')
            job_title: Job title to search for
            location: Location filter
        
        Returns:
            List of job dictionaries found via Google
        """
        # Get the domain for this site
        domain = self.site_domains.get(target_site.lower())
        if not domain:
            print(f"⚠️ Google Fallback: No domain mapping for '{target_site}'")
            return []
        
        # Construct Google Dork query
        # Example: site:dice.com "ServiceNow Developer" "Remote"
        query_parts = [f'site:{domain}', f'"{job_title}"']
        
        if location and location.lower() not in ['remote', 'anywhere', '']:
            query_parts.append(f'"{location}"')
        
        query = ' '.join(query_parts)
        url = f"https://www.google.com/search?q={quote(query)}&num=30"
        
        print(f"🔍 Google Fallback: Searching '{query}'")
        print(f"📡 Google URL: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br'
        }
        
        try:
            # Sleep to avoid Google rate limits (429 errors)
            delay = random.uniform(2, 4)
            print(f"⏳ Waiting {delay:.1f}s to avoid Google rate limit...")
            time.sleep(delay)
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 429:
                print("❌ Google Fallback: Rate limited (429). Try again later.")
                return []
            
            if response.status_code != 200:
                print(f"❌ Google Fallback: Status {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            jobs = []
            
            # Parse Google search results
            # Google uses <div class="g"> for each result
            results = soup.select('.g, div[data-sokoban-container]')
            
            if not results:
                print(f"⚠️ Google Fallback: No results found for {target_site}")
                return []
            
            print(f"✅ Google Fallback: Found {len(results)} search results")
            
            for result in results[:20]:  # Limit to 20 results
                try:
                    # Find title (usually in h3)
                    title_elem = result.select_one('h3')
                    
                    # Find link (usually in a tag)
                    link_elem = result.select_one('a')
                    
                    # Find snippet/description
                    desc_elem = result.select_one('[data-sncf], .VwiC3b, .s')
                    
                    if title_elem and link_elem:
                        title = title_elem.text.strip()
                        job_url = link_elem.get('href', '')
                        
                        # Skip non-job URLs
                        if not job_url.startswith('http'):
                            continue
                        
                        # Extract company from title or URL
                        company = target_site.replace('_', ' ').title()
                        if ' - ' in title:
                            parts = title.split(' - ')
                            if len(parts) > 1:
                                company = parts[-1].strip()
                                title = parts[0].strip()
                        
                        description = desc_elem.text.strip() if desc_elem else "Found via Google Search"
                        
                        job = {
                            'title': title,
                            'company': company,
                            'url': job_url,
                            'location': location or 'Remote',
                            'source': f'{target_site}_google',  # Mark as Google fallback
                            'description': description[:500],
                            'salary': 'Not specified',
                            'posted_date': 'Recently',
                            'job_type': 'Full-time',
                            'remote': True,
                            'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'via_fallback': True  # Flag for tracking
                        }
                        
                        jobs.append(job)
                
                except Exception as e:
                    print(f"⚠️ Error parsing Google result: {e}")
                    continue
            
            if jobs:
                print(f"✅ Google Fallback: Extracted {len(jobs)} jobs")
            
            return jobs
            
        except requests.Timeout:
            print(f"❌ Google Fallback: Request timeout")
            return []
        except requests.RequestException as e:
            print(f"❌ Google Fallback: Network error - {e}")
            return []
        except Exception as e:
            print(f"❌ Google Fallback: Unexpected error - {e}")
            return []

if __name__ == "__main__":
    # Test the fallback scraper
    print("🧪 Testing Google Fallback Scraper\n")
    scraper = GoogleFallbackScraper()
    
    test_sites = ['dice', 'ziprecruiter', 'servicenow_careers']
    for site in test_sites:
        print(f"\n{'='*60}")
        print(f"Testing: {site}")
        print('='*60)
        jobs = scraper.scrape(site, "ServiceNow Developer", "Remote")
        print(f"Found {len(jobs)} jobs\n")
        
        if jobs:
            for i, job in enumerate(jobs[:3], 1):
                print(f"  {i}. {job['title']}")
                print(f"     Company: {job['company']}")
                print(f"     URL: {job['url'][:80]}...")
