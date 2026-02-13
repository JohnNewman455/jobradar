"""
Nelson Frank Scraper - 2026 WORKING VERSION v2
Multi-strategy: tries link-based extraction first, falls back to CSS selectors.
Scrapes ALL jobs globally, tags with location; softer Canada filter.
"""

try:
    import requests
except ImportError:
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

from datetime import datetime
import time
import random
import re


class NelsonFrankScraper:
    """Scraper for Nelson Frank - The #1 ServiceNow recruitment firm"""

    def __init__(self):
        self.name = "Nelson Frank"
        self.base_url = "https://www.nelsonfrank.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Referer': 'https://www.nelsonfrank.com/',
        }

    def scrape(self, job_title, location, remote=False):
        """Scrape ServiceNow jobs from Nelson Frank — all regions, all pages."""
        all_jobs = []

        print(f"🔍 {self.name}: Searching for '{job_title}'...")

        max_pages = 6
        for page in range(1, max_pages + 1):
            try:
                url = f"{self.base_url}/servicenow-jobs"
                if page > 1:
                    url += f"?page={page}"

                if page > 1:
                    time.sleep(random.uniform(1.0, 2.5))

                response = requests.get(url, headers=self.headers, timeout=20)
                if response.status_code != 200:
                    print(f"   ⚠️ {self.name}: Page {page} → HTTP {response.status_code}")
                    break

                soup = BeautifulSoup(response.content, 'html.parser')

                # ── Strategy 1: link-based ── grab every <a href="/job/...">
                job_links = soup.select('a[href^="/job/"]')
                seen_urls = set()
                unique_links = []
                for lk in job_links:
                    href = lk.get('href', '')
                    if href and href not in seen_urls:
                        seen_urls.add(href)
                        unique_links.append(lk)

                if unique_links:
                    page_jobs = self._parse_from_links(unique_links, location, remote)
                    if page_jobs:
                        print(f"   ✅ {self.name}: {len(page_jobs)} jobs on page {page} (link strategy)")
                        all_jobs.extend(page_jobs)
                        if len(unique_links) < 8:
                            break
                        continue

                # ── Strategy 2: CSS selectors (.jobTitle) ──
                job_titles = soup.select('.jobTitle')
                if job_titles:
                    page_jobs = self._parse_from_selectors(soup, job_titles, location, remote)
                    print(f"   ✅ {self.name}: {len(page_jobs)} jobs on page {page} (selector strategy)")
                    all_jobs.extend(page_jobs)
                    if len(job_titles) < 8:
                        break
                    continue

                # Nothing found on this page → done
                if page == 1:
                    print(f"   ⚠️ {self.name}: No jobs found on page 1")
                break

            except Exception as e:
                print(f"   ❌ {self.name}: Error page {page}: {str(e)[:120]}")
                break

        if all_jobs:
            print(f"✅ {self.name}: {len(all_jobs)} total jobs across {min(page, max_pages)} pages")
        else:
            print(f"⚠️ {self.name}: No jobs found")

        return all_jobs

    # ── Strategy 1: link-based parsing ────────────────────────────────

    def _parse_from_links(self, links, default_location, remote):
        """Parse jobs from <a href='/job/...'> elements."""
        jobs = []
        for link in links:
            try:
                href = link.get('href', '')
                job_url = self.base_url + href

                # The link text often contains title + location + salary info
                full_text = link.get_text(' ', strip=True)
                if not full_text or len(full_text) < 5:
                    continue

                # Extract title: first meaningful line
                lines = [l.strip() for l in link.stripped_strings]
                title = lines[0] if lines else full_text[:100]
                if len(title) < 3:
                    continue

                # Location: look for country/city patterns
                job_location = self._extract_location(full_text, lines) or default_location
                salary = self._extract_salary(full_text) or 'Not specified'
                job_type = self._extract_role_type(full_text)
                seniority = self._extract_seniority(full_text)
                skills_text = self._extract_skills_text(full_text)

                # Build description from available text
                description = full_text[:500]
                if seniority:
                    description = f"Seniority: {seniority}. {description}"
                if skills_text:
                    description = f"Skills: {skills_text}. {description}"

                # Remote detection
                text_lower = full_text.lower()
                is_remote = any(kw in text_lower for kw in ['remote', 'work from home', 'wfh', 'anywhere'])

                job = {
                    'title': title,
                    'company': 'Nelson Frank',
                    'location': job_location,
                    'description': description,
                    'url': job_url,
                    'salary': salary,
                    'salary_numeric': self._parse_salary_numeric(salary),
                    'posted_date': 'Recently',
                    'posted_timestamp': 0,
                    'job_type': job_type,
                    'source': 'NELSONFRANK',
                    'remote': is_remote or remote,
                    'work_type': 'Remote' if (is_remote or remote) else ('Hybrid' if 'hybrid' in text_lower else 'On-site'),
                }
                jobs.append(job)

            except Exception:
                continue

        return jobs

    # ── Strategy 2: CSS selector parsing (original approach) ──────────

    def _parse_from_selectors(self, soup, job_titles, default_location, remote):
        """Parse jobs using .jobTitle, .location, .particulars selectors."""
        jobs = []
        for title_elem in job_titles:
            try:
                title = title_elem.get_text(strip=True)
                if not title or len(title) < 3:
                    continue

                overview = title_elem.parent
                if not overview:
                    continue

                # Find job link
                job_link = None
                parent = overview
                for _ in range(5):
                    if parent is None:
                        break
                    link = parent.find('a', href=lambda h: h and h.startswith('/job/'))
                    if link:
                        job_link = link
                        break
                    parent = parent.parent
                if not job_link:
                    job_link = overview.find('a', href=lambda h: h and h.startswith('/job/'))

                job_url = (self.base_url + job_link['href']) if job_link else f"{self.base_url}/servicenow-jobs"

                # Location
                loc_elem = overview.select_one('.location, p.location')
                job_location = loc_elem.get_text(strip=True) if loc_elem else default_location

                # Particulars
                salary = 'Not specified'
                job_type = 'Full-time'
                seniority = ''
                skills = ''
                particulars = overview.select_one('.particulars, ul.particulars')
                if particulars:
                    for item in particulars.select('li'):
                        text = item.get_text(strip=True)
                        if any(c in text for c in ('$', '£', '€')) or 'to' in text.lower():
                            salary = text
                        elif 'seniority' in text.lower():
                            seniority = text.replace('Seniority:', '').strip()
                        elif 'role' in text.lower():
                            job_type = text
                        elif 'skill' in text.lower():
                            skills = text

                desc_elem = overview.select_one('.jobDescription, .jobDetail')
                if not desc_elem and overview.parent:
                    desc_elem = overview.parent.select_one('.jobDescription, .jobDetail')
                description = desc_elem.get_text(strip=True)[:500] if desc_elem else ''
                if seniority:
                    description = f"Seniority: {seniority}. {description}"
                if skills:
                    description = f"{skills}. {description}"

                card_text = overview.get_text().lower()
                is_remote = any(kw in card_text for kw in ['remote', 'work from home', 'wfh'])

                job = {
                    'title': title,
                    'company': 'Nelson Frank',
                    'location': job_location,
                    'description': description,
                    'url': job_url,
                    'salary': salary,
                    'salary_numeric': self._parse_salary_numeric(salary),
                    'posted_date': 'Recently',
                    'posted_timestamp': 0,
                    'job_type': job_type,
                    'source': 'NELSONFRANK',
                    'remote': is_remote or remote,
                    'work_type': 'Remote' if (is_remote or remote) else 'On-site',
                }
                jobs.append(job)
            except Exception:
                continue
        return jobs

    # ── Helper extractors ─────────────────────────────────────────────

    def _extract_location(self, text, lines):
        """Extract location from card text."""
        countries = ['USA', 'United States', 'Canada', 'UK', 'England', 'Ireland',
                     'Australia', 'Germany', 'Netherlands', 'Singapore', 'France',
                     'Switzerland', 'Belgium', 'Poland', 'Italy', 'New Zealand', 'India']
        cities = ['Toronto', 'Vancouver', 'Montreal', 'Ottawa', 'Calgary',
                  'London', 'New York', 'Chicago', 'San Francisco', 'Austin',
                  'Dallas', 'Boston', 'Seattle', 'Denver', 'Atlanta', 'Napa',
                  'Virginia', 'Massachusetts', 'Texas', 'California', 'Illinois']
        for line in lines:
            for country in countries:
                if country.lower() in line.lower():
                    return line[:80]
            for city in cities:
                if city.lower() in line.lower():
                    return line[:80]
        return None

    def _extract_salary(self, text):
        """Extract salary from text."""
        patterns = [
            r'(?:US?\$|£|€|CA?\$)\s*[\d,]+(?:\s*to\s*(?:US?\$|£|€|CA?\$)?\s*[\d,]+)?(?:\s*(?:USD|GBP|EUR|CAD))?',
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return m.group(0).strip()
        return None

    def _extract_role_type(self, text):
        """Extract role type (Developer, Consultant, etc.)."""
        for role in ['Developer', 'Consultant', 'Administrator', 'Architect',
                     'Manager', 'Analyst', 'Engineer', 'Lead', 'Director']:
            if role.lower() in text.lower():
                return f"{role} Role"
        return 'Full-time'

    def _extract_seniority(self, text):
        """Extract seniority level."""
        for level in ['Senior', 'Mid-level', 'Junior', 'Lead', 'Principal', 'Staff']:
            if f'seniority: {level.lower()}' in text.lower() or f'seniority:{level.lower()}' in text.lower():
                return level
            if level.lower() in text.lower():
                return level
        return ''

    def _extract_skills_text(self, text):
        """Extract skills mention."""
        m = re.search(r'skills?:\s*(.+?)(?:seniority|role|\n|$)', text, re.IGNORECASE)
        return m.group(1).strip()[:120] if m else ''

    def _parse_salary_numeric(self, salary_str):
        """Convert salary string to numeric (annual) for sorting."""
        if not salary_str or salary_str == 'Not specified':
            return 0
        nums = re.findall(r'[\d,]+', salary_str.replace(',', ''))
        if not nums:
            return 0
        try:
            val = int(nums[-1])
            # If less than 500, likely hourly rate
            if val < 500:
                return val * 2080
            # If less than 5000, likely daily rate
            if val < 5000:
                return val * 260
            return val
        except ValueError:
            return 0


# Alias for backward compatibility
NelsonFrankAPIScraper = NelsonFrankScraper
