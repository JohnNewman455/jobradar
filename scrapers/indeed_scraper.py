"""
Indeed Job Scraper
Scrapes jobs from Indeed.com using curl_cffi
"""

try:
    from curl_cffi import requests
    CURL_CFFI_AVAILABLE = True
except ImportError:
    import requests
    CURL_CFFI_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

import re


class IndeedScraper:
    """Scraper for Indeed.com with curl_cffi bypass"""
    
    def __init__(self):
        self.base_url = "https://www.indeed.com"
    
    def scrape(self, job_title, location, remote=False):
        """Scrape jobs from Indeed"""
        jobs = []
        
        print(f"🔍 Indeed: Searching for '{job_title}' in '{location}'...")
        
        # Build search URL
        params = f"?q={job_title.replace(' ', '+')}"
        if location:
            params += f"&l={location.replace(' ', '+')}"
        if remote:
            params += "&remotejob=032b3046-06a3-4876-8dfd-474eb5e7ed11"
        params += "&fromage=14&sort=date"
        
        url = f"{self.base_url}/jobs{params}"
        
        try:
            print(f"📡 Indeed: Fetching {url}")
            
            # This bypasses 403 Forbidden errors
            if CURL_CFFI_AVAILABLE:
                response = requests.get(url, impersonate="chrome110", timeout=15)
            else:
                response = requests.get(url, timeout=15)
            
            print(f"✅ Indeed: Got response (status {response.status_code})")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                jobs = self.parse_jobs(soup)
                print(f"✅ Indeed: Found {len(jobs)} jobs")
            else:
                print(f"❌ Indeed: Failed with status {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Indeed error: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return jobs
    
    def parse_jobs(self, soup):
        """Parse job listings from Indeed HTML"""
        jobs = []
        
        # Find job cards - Indeed uses various class names
        job_cards = soup.find_all('div', class_=re.compile(r'job_seen_beacon|jobsearch-SerpJobCard|slider_item'))
        
        if not job_cards:
            # Try alternative selector
            job_cards = soup.find_all('td', class_='resultContent')
        
        print(f"🎯 Indeed: Found {len(job_cards)} job cards in HTML")
        
        for card in job_cards[:50]:
            try:
                job = self._parse_job_card(card)
                if job and job.get('title') != 'N/A':
                    jobs.append(job)
            except Exception as e:
                print(f"⚠️  Indeed: Error parsing card: {str(e)}")
                continue
        
        return jobs
    
    def _parse_job_card(self, card):
        """Parse individual job card"""
        try:
            # Title and URL
            title_elem = card.find('h2', class_='jobTitle')
            if not title_elem:
                title_elem = card.find('a', class_='jcs-JobTitle')
            if not title_elem:
                title_elem = card.find('span', {'title': True})
            
            if not title_elem:
                return None
            
            title_link = title_elem.find('a') if title_elem.name != 'a' else title_elem
            title = title_link.get_text(strip=True) if title_link else title_elem.get_text(strip=True)
            
            job_url = ''
            if title_link and title_link.get('href'):
                job_url = f"{self.base_url}{title_link['href']}" if title_link['href'].startswith('/') else title_link['href']
            
            # Company
            company_elem = card.find('span', class_='companyName')
            if not company_elem:
                company_elem = card.find('span', {'data-testid': 'company-name'})
            company = company_elem.get_text(strip=True) if company_elem else 'N/A'
            
            # Location
            location_elem = card.find('div', class_='companyLocation')
            if not location_elem:
                location_elem = card.find('div', {'data-testid': 'text-location'})
            location = location_elem.get_text(strip=True) if location_elem else 'Remote'
            
            # Salary
            salary_elem = card.find('div', class_='salary-snippet')
            if not salary_elem:
                salary_elem = card.find('span', class_='salary')
            if not salary_elem:
                salary_elem = card.find('div', {'data-testid': 'attribute_snippet_testid'})
            salary = salary_elem.get_text(strip=True) if salary_elem else 'Not specified'
            
            # Description
            description_elem = card.find('div', class_='job-snippet')
            if not description_elem:
                description_elem = card.find('div', {'data-testid': 'job-snippet'})
            description = description_elem.get_text(strip=True) if description_elem else 'N/A'
            
            # Posted date
            date_elem = card.find('span', class_='date')
            if not date_elem:
                date_elem = card.find('span', {'data-testid': 'myJobsStateDate'})
            posted_date = date_elem.get_text(strip=True) if date_elem else 'Recently'
            
            return {
                'title': title,
                'company': company,
                'location': location,
                'description': description,
                'url': job_url,
                'salary': salary,
                'posted_date': posted_date,
                'job_type': 'Full-time',
                'remote': 'remote' in location.lower() or 'remote' in description.lower(),
                'tags': []
            }
            
        except Exception as e:
            print(f"⚠️  Error parsing job card: {str(e)}")
            return None
    
    def _parse_job_card(self, card):
        """Parse individual job card"""
        try:
            # Title and URL
            title_elem = card.find('h2', class_='jobTitle')
            if not title_elem:
                title_elem = card.find('a', class_='jcs-JobTitle')
            
            title = title_elem.get_text(strip=True) if title_elem else 'N/A'
            job_url = title_elem.find('a')['href'] if title_elem and title_elem.find('a') else ''
            job_url = f"{self.base_url}{job_url}" if job_url and not job_url.startswith('http') else job_url
            
            # Company
            company_elem = card.find('span', class_='companyName')
            company = company_elem.get_text(strip=True) if company_elem else 'N/A'
            
            # Location
            location_elem = card.find('div', class_='companyLocation')
            location = location_elem.get_text(strip=True) if location_elem else 'N/A'
            
            # Salary
            salary_elem = card.find('div', class_='salary-snippet')
            if not salary_elem:
                salary_elem = card.find('span', class_='salary')
            salary = salary_elem.get_text(strip=True) if salary_elem else 'Not specified'
            
            # Description snippet
            description_elem = card.find('div', class_='job-snippet')
            description = description_elem.get_text(strip=True) if description_elem else 'N/A'
            
            # Posted date
            date_elem = card.find('span', class_='date')
            posted_date = date_elem.get_text(strip=True) if date_elem else 'N/A'
            
            return {
                'title': title,
                'company': company,
                'location': location,
                'description': description,
                'url': job_url,
                'salary': salary,
                'posted_date': posted_date,
                'remote': 'remote' in location.lower() or 'remote' in description.lower()
            }
            
        except Exception as e:
            print(f"Error parsing job card: {str(e)}")
            return None
