"""
Ghost Job Detector — flags fake, stale, or evergreen job postings.

A "ghost job" is a listing that was never meant to be filled, has been
open too long, or uses language indicating it's an evergreen/talent-pool
placeholder.  Each job gets a ghost_score (0-100) and is_ghost (bool).
"""

import re
from datetime import datetime, timedelta


# ── Red-flag phrases commonly found in ghost / evergreen postings ──────────
GHOST_PHRASES = [
    ('talent pool', 30),
    ('talent community', 30),
    ('talent network', 25),
    ('evergreen', 35),
    ('future opportunities', 30),
    ('pipeline', 20),
    ('general application', 30),
    ('always accepting', 25),
    ('ongoing recruitment', 25),
    ('continuous hiring', 20),
    ('expressions of interest', 25),
    ('proactive search', 20),
    ('rolling basis', 15),
    ('no specific opening', 35),
    ('we are always looking', 25),
    ('join our community', 20),
]


class GhostJobDetector:
    """Analyse a job dict and return ghost-likelihood metrics."""

    def __init__(self, stale_days: int = 60, short_desc_chars: int = 200):
        self.stale_days = stale_days
        self.short_desc_chars = short_desc_chars

    def analyse(self, job: dict) -> dict:
        """
        Returns {
            ghost_score: 0-100,
            is_ghost: bool,
            flags: [str, ...],
            confidence: 'low'|'medium'|'high',
        }
        """
        score = 0
        flags = []

        # 1. Age check
        age_days = self._estimate_age(job)
        if age_days is not None:
            if age_days > self.stale_days:
                pts = min(40, 20 + (age_days - self.stale_days) // 5)
                score += pts
                flags.append(f'Posted {age_days} days ago (stale >{self.stale_days}d)')
            elif age_days > 45:
                score += 10
                flags.append(f'Posted {age_days} days ago (aging)')

        # 2. Red-flag phrases
        text = (
            (job.get('title', '') + ' ' + job.get('description', '')).lower()
        )
        for phrase, pts in GHOST_PHRASES:
            if phrase in text:
                score += pts
                flags.append(f'Contains "{phrase}"')

        # 3. Very short / missing description
        desc = job.get('description', '')
        if len(desc) < self.short_desc_chars:
            score += 20
            flags.append(f'Very short description ({len(desc)} chars)')

        # 4. Hidden or generic company name
        company = (job.get('company') or '').strip()
        if not company or company.lower() in ('confidential', 'private', 'n/a', 'unknown', 'company name'):
            score += 15
            flags.append('Company name hidden or generic')

        # 5. Reposted indicator
        if job.get('reposted') or 'reposted' in text:
            score += 15
            flags.append('Listing has been reposted')

        # 6. No salary + no location (extra suspicious combo)
        sal = (job.get('salary') or '').lower()
        loc = (job.get('location') or '').lower()
        if sal in ('', 'not specified', 'competitive', 'n/a') and loc in ('', 'n/a', 'not specified'):
            score += 10
            flags.append('No salary AND no location specified')

        # 7. Overly broad title
        broad_titles = ['software engineer', 'developer', 'analyst', 'consultant', 'engineer']
        title_low = job.get('title', '').lower()
        if title_low in broad_titles:
            score += 5
            flags.append('Very generic job title')

        score = min(score, 100)
        is_ghost = score >= 50

        if score >= 70:
            confidence = 'high'
        elif score >= 50:
            confidence = 'medium'
        else:
            confidence = 'low'

        return {
            'ghost_score': score,
            'is_ghost': is_ghost,
            'flags': flags,
            'confidence': confidence,
        }

    def _estimate_age(self, job: dict):
        """Return estimated age in days, or None if unknown."""
        # Try posted_timestamp first
        ts = job.get('posted_timestamp')
        if ts and ts > 0:
            try:
                posted = datetime.fromtimestamp(ts)
                return (datetime.now() - posted).days
            except Exception:
                pass

        # Try posted_date text
        text = (job.get('posted_date') or '').lower().strip()
        if not text or text in ('recently', 'n/a', ''):
            return None

        # "X days ago"
        m = re.search(r'(\d+)\s*day', text)
        if m:
            return int(m.group(1))
        # "X hours ago" → 0 days
        if 'hour' in text or 'just now' in text or 'today' in text:
            return 0
        # "X weeks ago"
        m = re.search(r'(\d+)\s*week', text)
        if m:
            return int(m.group(1)) * 7
        # "X months ago"
        m = re.search(r'(\d+)\s*month', text)
        if m:
            return int(m.group(1)) * 30

        return None


# Singleton for convenience
ghost_detector = GhostJobDetector()
