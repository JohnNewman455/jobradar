"""
ServiceNow Careers Scraper — Multi-strategy
Strategy 1: Workday CXS API (wd1.myworkdayjobs.com)
Strategy 2: HTML scrape of careers.servicenow.com search results
"""

try:
    import requests
except ImportError:
    requests = None

import re

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

from .base_scraper import BaseScraper


class ServiceNowCareersScraper(BaseScraper):
    """Scraper for ServiceNow official careers"""

    # Workday endpoints to try (ServiceNow has changed these before)
    WORKDAY_URLS = [
        "https://servicenow.wd1.myworkdayjobs.com/wday/cxs/servicenow/ServiceNowCareers/jobs",
        "https://servicenow.wd1.myworkdayjobs.com/wday/cxs/servicenow/External/jobs",
        "https://servicenow.wd1.myworkdayjobs.com/wday/cxs/servicenow/careers/jobs",
        "https://servicenow.wd5.myworkdayjobs.com/wday/cxs/servicenow/ServiceNowCareers/jobs",
    ]

    def __init__(self):
        super().__init__()
        self.base_url = "https://careers.servicenow.com"

    def scrape(self, job_title, location, remote=False):
        """Scrape jobs — try Workday API first, fall back to HTML."""
        # Strategy 1: Workday CXS API
        jobs = self._try_workday_api(job_title, location)
        if jobs:
            print(f"✅ ServiceNow Careers (Workday API): Found {len(jobs)} jobs")
            return jobs

        # Strategy 2: HTML scrape of careers.servicenow.com
        jobs = self._try_html_scrape(job_title, location)
        if jobs:
            print(f"✅ ServiceNow Careers (HTML): Found {len(jobs)} jobs")
            return jobs

        print(f"⚠️ ServiceNow Careers: Workday API is down (maintenance). 0 jobs.")
        return []

    # ── Workday CXS API ──────────────────────────────────────────────

    def _try_workday_api(self, job_title, location):
        """Try each Workday endpoint until one works."""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
        }
        payload = {
            'appliedFacets': {},
            'limit': 50,
            'offset': 0,
            'searchText': job_title,
        }

        for url in self.WORKDAY_URLS:
            try:
                resp = self.session.post(url, json=payload, headers=headers, timeout=20)
                if resp.status_code == 200:
                    data = resp.json()
                    postings = data.get('jobPostings', [])
                    if postings:
                        return [
                            self.standardize_job(self._parse_workday(p))
                            for p in postings if self._parse_workday(p)
                        ]
            except Exception:
                continue
        return []

    def _parse_workday(self, job_data):
        """Parse one Workday job posting."""
        try:
            title = job_data.get('title', '')
            if not title:
                return None
            ext_path = job_data.get('externalPath', '')
            loc = job_data.get('locationsText', 'N/A')
            posted = job_data.get('postedOn', '')

            # Build URL: Workday external paths look like /job/...
            if ext_path:
                job_url = f"https://servicenow.wd1.myworkdayjobs.com/en-US/ServiceNowCareers{ext_path}"
            else:
                bullet = job_data.get('bulletFields', [''])[0] if job_data.get('bulletFields') else ''
                job_url = f"{self.base_url}/jobs/{bullet}" if bullet else self.base_url

            return {
                'title': title,
                'company': 'ServiceNow',
                'location': loc,
                'description': job_data.get('descriptionPlain', '') or 'ServiceNow career opportunity',
                'url': job_url,
                'salary': 'Competitive',
                'posted_date': posted or 'Recently',
                'job_type': 'Full-time',
                'remote': 'remote' in loc.lower(),
            }
        except Exception:
            return None

    # ── HTML fallback ─────────────────────────────────────────────────

    def _try_html_scrape(self, job_title, location):
        """Scrape the careers.servicenow.com search page."""
        jobs = []
        try:
            search_url = f"{self.base_url}/search"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
                'Accept': 'text/html',
            }
            params = {'q': job_title, 'location': location or ''}
            resp = self.session.get(search_url, headers=headers, params=params, timeout=20)

            if resp.status_code != 200:
                return []

            soup = BeautifulSoup(resp.content, 'html.parser')

            # Look for job links (pattern: /jobs/<id> or /en/jobs/<id>)
            for link in soup.select('a[href*="/jobs/"]'):
                try:
                    href = link.get('href', '')
                    title = link.get_text(strip=True)
                    if not title or len(title) < 5:
                        continue

                    full_url = href if href.startswith('http') else self.base_url + href
                    parent_text = link.parent.get_text(' ', strip=True) if link.parent else ''
                    loc = self._guess_location(parent_text) or location or 'ServiceNow Office'

                    jobs.append(self.standardize_job({
                        'title': title,
                        'company': 'ServiceNow',
                        'location': loc,
                        'description': parent_text[:400] or 'ServiceNow career opportunity',
                        'url': full_url,
                        'salary': 'Competitive',
                        'job_type': 'Full-time',
                        'remote': 'remote' in parent_text.lower(),
                    }))
                except Exception:
                    continue
        except Exception:
            pass
        return jobs

    @staticmethod
    def _guess_location(text):
        """Try to extract a location from surrounding text."""
        for pat in [
            r'(?:Location|Office):\s*(.+?)(?:\n|$|\|)',
            r'((?:Toronto|San Diego|Santa Clara|Hyderabad|London|Amsterdam|Sydney|Dublin|Singapore)[^,]*)',
        ]:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return m.group(1).strip()[:80]
        return None
