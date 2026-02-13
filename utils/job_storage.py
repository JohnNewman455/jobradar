"""
Job Storage - In-memory storage with Fuzzy Deduplication
"""

import re
from datetime import datetime
from typing import List, Dict, Optional
from difflib import SequenceMatcher


def _normalize_company(name: str) -> str:
    """Normalize company name for dedup: 'Deloitte.' => 'deloitte', 'Accenture Inc' => 'accenture'"""
    if not name:
        return ''
    name = name.lower().strip()
    # Remove common suffixes
    for suffix in [' inc', ' inc.', ' ltd', ' ltd.', ' llc', ' corp', ' corp.',
                   ' limited', ' co.', ' co', ' group', ' plc', ' gmbh',
                   ' pvt', ' pvt.', ' private', ' consulting', ' services',
                   ' solutions', ' technologies', ' technology']:
        if name.endswith(suffix):
            name = name[:-len(suffix)].strip()
    # Remove trailing punctuation
    name = re.sub(r'[.\-,;:!]+$', '', name).strip()
    # Collapse whitespace
    name = re.sub(r'\s+', ' ', name)
    return name


def _make_fingerprint(job: Dict) -> str:
    """Create a fuzzy fingerprint for dedup: 'deloitte_servicenow dev_toronto'"""
    company = _normalize_company(job.get('company', ''))
    title = re.sub(r'[^a-z0-9 ]', '', job.get('title', '').lower().strip())[:30]
    location = job.get('location', '').lower().strip().split(',')[0].strip()[:15]
    return f"{company}_{title}_{location}"


class JobStorage:
    """Store and manage scraped jobs with fuzzy deduplication"""
    
    def __init__(self):
        self.jobs: List[Dict] = []
        self.site_stats = {}
        self._url_set: set = set()          # fast exact-URL dedup
        self._fingerprints: List[str] = []  # for fuzzy matching
        self.duplicates_removed: int = 0
        self._rejected_dupes: List[Dict] = []  # store rejected dupes for viewer
    
    def add(self, job: Dict) -> bool:
        """Add a job to storage. Returns False if duplicate detected."""
        url = job.get('url', '')
        
        # 1. Exact URL dedup (fast)
        if url and url in self._url_set:
            self.duplicates_removed += 1
            self._rejected_dupes.append({
                'title': job.get('title', ''),
                'company': job.get('company', ''),
                'url': url,
                'source': job.get('source', ''),
                'reason': 'Exact URL match'
            })
            return False
        
        # 2. Fuzzy fingerprint dedup (catches cross-site duplicates)
        fp = _make_fingerprint(job)
        if fp and len(fp) > 5:  # only check non-trivial fingerprints
            for existing_fp in self._fingerprints:
                similarity = SequenceMatcher(None, fp, existing_fp).ratio()
                if similarity > 0.92:  # ~92% match — tighter threshold
                    self.duplicates_removed += 1
                    self._rejected_dupes.append({
                        'title': job.get('title', ''),
                        'company': job.get('company', ''),
                        'url': url,
                        'source': job.get('source', ''),
                        'reason': f'Fuzzy match ({similarity:.0%}) with: {existing_fp}'
                    })
                    return False
        
        # Not a duplicate - add it
        if url:
            self._url_set.add(url)
        self._fingerprints.append(fp)
        self.jobs.append(job)
        
        # Update site stats
        source = job.get('source', 'unknown')
        self.site_stats[source] = self.site_stats.get(source, 0) + 1
        return True
    
    def get_all(self, filters: Optional[Dict] = None) -> List[Dict]:
        """Get all jobs with optional filtering"""
        if not filters:
            return self.jobs
        
        filtered_jobs = self.jobs
        
        if filters.get('site'):
            filtered_jobs = [j for j in filtered_jobs if j.get('source') == filters['site']]
        
        if filters.get('remote_only'):
            filtered_jobs = [j for j in filtered_jobs if j.get('remote') is True]
        
        if filters.get('min_salary'):
            try:
                threshold = int(filters['min_salary'])
                filtered_jobs = [j for j in filtered_jobs if (j.get('salary_numeric') or 0) >= threshold]
            except (ValueError, TypeError):
                pass
        
        return filtered_jobs
    
    def get_recent(self, count: int) -> List[Dict]:
        """Get most recent N jobs"""
        return self.jobs[-count:] if count <= len(self.jobs) else self.jobs
    
    def count(self) -> int:
        return len(self.jobs)
    
    def get_site_stats(self) -> Dict:
        return self.site_stats
    
    def get_progress_by_site(self) -> Dict:
        progress = {}
        for source, count in self.site_stats.items():
            progress[source] = {
                'count': count,
                'status': 'done' if count > 0 else 'scanning'
            }
        return progress
    
    def clear(self):
        self.jobs.clear()
        self.site_stats.clear()
        self._url_set.clear()
        self._fingerprints.clear()
        self.duplicates_removed = 0
        self._rejected_dupes.clear()
    
    def get_rejected_dupes(self) -> List[Dict]:
        """Return list of rejected duplicates for verification"""
        return self._rejected_dupes
    
    def search(self, query: str) -> List[Dict]:
        query_lower = query.lower()
        return [
            job for job in self.jobs
            if query_lower in job.get('title', '').lower()
            or query_lower in job.get('company', '').lower()
            or query_lower in job.get('description', '').lower()
        ]
