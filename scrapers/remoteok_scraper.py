"""
RemoteOK Job Scraper
Scrapes remote jobs from RemoteOK.com
"""

from .base_scraper import BaseScraper
import json


class RemoteOKScraper(BaseScraper):
    """Scraper for RemoteOK.com - Has a public API!"""
    
    def __init__(self):
        super().__init__()
        self.api_url = "https://remoteok.com/api"
    
    def scrape(self, job_title, location, remote=False):
        """Scrape jobs from RemoteOK"""
        jobs = []
        
        try:
            # RemoteOK has a public API
            response = self.get_page(self.api_url)
            if not response:
                return jobs
            
            data = response.json()
            
            # Skip first item (it's metadata)
            job_listings = data[1:] if len(data) > 1 else []
            
            # Filter by job title
            search_terms = job_title.lower().split()
            
            for job_data in job_listings[:50]:  # Limit to 50
                try:
                    # Check if job matches search criteria
                    job_position = job_data.get('position', '').lower()
                    job_tags = [tag.lower() for tag in job_data.get('tags', [])]
                    
                    # Match if any search term is in position or tags
                    if any(term in job_position or term in ' '.join(job_tags) for term in search_terms):
                        job = self._parse_job(job_data)
                        if job:
                            jobs.append(self.standardize_job(job))
                
                except Exception as e:
                    print(f"Error parsing RemoteOK job: {str(e)}")
                    continue
            
            print(f"✅ RemoteOK: Found {len(jobs)} jobs")
            
        except Exception as e:
            print(f"❌ RemoteOK scraping error: {str(e)}")
        
        return jobs
    
    def _parse_job(self, job_data):
        """Parse job from API response"""
        try:
            salary_min = job_data.get('salary_min', 0)
            salary_max = job_data.get('salary_max', 0)
            
            if salary_min and salary_max:
                salary = f"${salary_min:,} - ${salary_max:,}"
            elif salary_min:
                salary = f"${salary_min:,}+"
            else:
                salary = "Not specified"
            
            # Parse date - RemoteOK can give timestamp or ISO date string
            posted_date = 'Recently'
            posted_timestamp = 0
            date_value = job_data.get('date') or job_data.get('epoch')
            if date_value:
                try:
                    from datetime import datetime
                    # Try parsing as Unix timestamp first
                    try:
                        dt = datetime.fromtimestamp(int(date_value))
                        posted_timestamp = int(date_value)
                    except (ValueError, TypeError):
                        # If not timestamp, try ISO format string
                        dt = datetime.fromisoformat(str(date_value).replace('Z', '+00:00'))
                        posted_timestamp = int(dt.timestamp())
                    
                    # Remove timezone info for comparison
                    dt_naive = dt.replace(tzinfo=None) if dt.tzinfo else dt
                    days_ago = (datetime.now() - dt_naive).days
                    
                    if days_ago == 0:
                        posted_date = 'Today'
                    elif days_ago == 1:
                        posted_date = '1 day ago'
                    elif days_ago < 7:
                        posted_date = f'{days_ago} days ago'
                    elif days_ago < 30:
                        weeks = days_ago // 7
                        posted_date = f'{weeks} week{"s" if weeks > 1 else ""} ago'
                    else:
                        posted_date = dt_naive.strftime('%B %d, %Y')
                except Exception as e:
                    # Silently fail - don't spam console
                    posted_date = 'Recently'
                    posted_timestamp = 0
            
            return {
                'title': job_data.get('position', 'N/A'),
                'company': job_data.get('company', 'N/A'),
                'location': job_data.get('location', 'Remote'),
                'description': job_data.get('description', 'N/A'),
                'url': job_data.get('url', 'N/A'),
                'salary': salary,
                'job_type': job_data.get('employment_type', 'Full-time'),
                'remote': True,
                'posted_date': posted_date,
                'posted_timestamp': posted_timestamp,  # Use the already-converted timestamp
                'tags': job_data.get('tags', [])
            }
            
        except Exception as e:
            print(f"Error parsing RemoteOK job: {str(e)}")
            return None
