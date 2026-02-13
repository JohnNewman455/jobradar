"""
Talent.com Scraper — Feb 2026
Parses article[data-testid="job-card-server"] elements from Talent.com search.
"""

from .base_scraper import BaseScraper


class TalentComScraper(BaseScraper):
    """Scraper for Talent.com job search"""

    def __init__(self):
        super().__init__()
        self.name = "Talent.com"
        self.base_url = "https://www.talent.com"

    def scrape(self, job_title, location, remote=False):
        jobs = []
        print(f"🔎 {self.name}: Searching for '{job_title}'...")

        for page in range(1, 6):  # up to 5 pages
            try:
                params = {
                    'k': job_title,
                    'l': location if location else '',
                    'p': page,
                }
                if remote:
                    params['wfh'] = '1'

                response = self.get_page(f"{self.base_url}/jobs", params=params)
                if not response:
                    break

                soup = self.parse_html(response.text)

                # Talent.com renders job cards as <article data-testid="job-card-server">
                articles = soup.select('article[data-testid="job-card-server"]')
                if not articles:
                    # Fallback: any article element
                    articles = soup.select('article')
                if not articles:
                    if page == 1:
                        print(f"   ⚠️ {self.name}: No job cards found on page {page}")
                    break

                page_count = 0
                for article in articles:
                    try:
                        job = self._parse_article(article)
                        if job and job.get('title') and job['title'] != 'N/A':
                            jobs.append(self.standardize_job(job))
                            page_count += 1
                    except Exception:
                        continue

                print(f"   📄 {self.name} page {page}: {page_count} jobs (total: {len(jobs)})")
                if page_count == 0:
                    break

            except Exception as e:
                print(f"   ❌ {self.name} page {page} error: {str(e)[:80]}")
                break

        print(f"✅ {self.name}: Found {len(jobs)} total jobs")
        return jobs

    def _parse_article(self, article):
        """Parse a talent.com article element.
        
        Structure:
          <article data-testid="job-card-server">
            <a href="/view?id=...">Show more</a>
            <h2>Job Title</h2>
            <p>Company Name</p>
            <p>Location</p>
            <span>Full-time</span>
          </article>
        """
        # Title from h2 (primary) or h3 fallback
        title_el = article.select_one('h2') or article.select_one('h3') or article.select_one('h1')
        title = title_el.get_text(strip=True) if title_el else 'N/A'

        # URL from the /view?id= link
        link_el = article.select_one('a[href*="/view?id="]') or article.select_one('a[href]')
        url = ''
        if link_el and link_el.get('href'):
            href = link_el['href']
            url = href if href.startswith('http') else f"{self.base_url}{href}"

        # Company + location from <p> tags (first p = company, second p = location)
        p_tags = article.select('p')
        company = p_tags[0].get_text(strip=True) if len(p_tags) > 0 else 'Unknown'
        location = p_tags[1].get_text(strip=True) if len(p_tags) > 1 else ''

        # Job type from span (Full-time, Part-time, Contract etc.)
        span_el = article.select_one('span')
        job_type = span_el.get_text(strip=True) if span_el else ''

        # Not much else available in SSR cards; build a description
        desc = f"{title} at {company}"
        if location:
            desc += f" — {location}"
        if job_type:
            desc += f" ({job_type})"

        if not title or title == 'N/A':
            return None

        return {
            'title': title,
            'company': company,
            'url': url,
            'location': location,
            'description': desc,
            'salary': 'Not specified',
            'posted_date': '',
            'remote': 'remote' in (location + ' ' + title + ' ' + job_type).lower(),
        }
