"""
Market Intelligence Engine — salary normalizer, skill demand tracker,
source quality scoring.

Analyses the current job collection and returns dashboard-ready data.
"""

import re
from collections import Counter, defaultdict
from datetime import datetime


# ═══════════════════════════════════════════════════════════════════════════════
#  SALARY NORMALIZER
# ═══════════════════════════════════════════════════════════════════════════════

def normalize_salary(salary_str: str) -> dict:
    """
    Parse a messy salary string into structured data.
    Returns { min, max, currency, period, annual_min, annual_max }.
    """
    if not salary_str or salary_str.lower() in ('not specified', 'competitive', 'n/a', ''):
        return {'raw': salary_str, 'annual_min': 0, 'annual_max': 0, 'parseable': False}

    text = salary_str.replace(',', '').replace('\u00a0', ' ').strip()

    # Detect currency
    currency = 'USD'
    if '£' in text or 'GBP' in text.upper():
        currency = 'GBP'
    elif '€' in text or 'EUR' in text.upper():
        currency = 'EUR'
    elif 'CA$' in text or 'CAD' in text.upper() or 'C$' in text:
        currency = 'CAD'

    # Extract numbers
    nums = [int(n) for n in re.findall(r'\d+', text) if int(n) > 0]
    if not nums:
        return {'raw': salary_str, 'annual_min': 0, 'annual_max': 0, 'parseable': False}

    low = min(nums)
    high = max(nums)

    # Detect period
    text_lower = text.lower()
    if any(w in text_lower for w in ['hour', 'hr', '/hr', 'hourly']):
        period = 'hourly'
        annual_low = low * 2080
        annual_high = high * 2080
    elif any(w in text_lower for w in ['day', 'daily', '/day']):
        period = 'daily'
        annual_low = low * 260
        annual_high = high * 260
    elif any(w in text_lower for w in ['week', 'weekly', '/wk']):
        period = 'weekly'
        annual_low = low * 52
        annual_high = high * 52
    elif any(w in text_lower for w in ['month', 'monthly', '/mo']):
        period = 'monthly'
        annual_low = low * 12
        annual_high = high * 12
    else:
        period = 'annual'
        # If values are very small, they're probably hourly rates
        if high < 500:
            period = 'hourly'
            annual_low = low * 2080
            annual_high = high * 2080
        elif high < 5000:
            period = 'daily'
            annual_low = low * 260
            annual_high = high * 260
        else:
            annual_low = low
            annual_high = high

    # Currency conversion (approximate, for ranking purposes)
    fx = {'USD': 1.0, 'CAD': 0.73, 'GBP': 1.27, 'EUR': 1.09}
    rate = fx.get(currency, 1.0)
    annual_usd_low = int(annual_low * rate)
    annual_usd_high = int(annual_high * rate)

    return {
        'raw': salary_str,
        'parseable': True,
        'currency': currency,
        'period': period,
        'min': low,
        'max': high,
        'annual_min': annual_low,
        'annual_max': annual_high,
        'annual_usd_min': annual_usd_low,
        'annual_usd_max': annual_usd_high,
        'midpoint_usd': (annual_usd_low + annual_usd_high) // 2,
    }


def salary_distribution(jobs: list) -> dict:
    """
    Analyse salary distribution across all jobs.
    Returns histogram buckets & stats for the frontend.
    """
    salaries = []
    for job in jobs:
        parsed = normalize_salary(job.get('salary', ''))
        if parsed.get('parseable') and parsed.get('midpoint_usd', 0) > 10000:
            salaries.append(parsed['midpoint_usd'])

    if not salaries:
        return {'available': False, 'message': 'Not enough salary data', 'count': 0}

    salaries.sort()
    n = len(salaries)
    avg = int(sum(salaries) / n)
    median = salaries[n // 2]
    low = salaries[0]
    high = salaries[-1]

    # Build histogram (6 buckets)
    bucket_size = max((high - low) // 6, 10000)
    buckets = []
    for i in range(6):
        lo = low + i * bucket_size
        hi = lo + bucket_size
        count = sum(1 for s in salaries if lo <= s < hi)
        buckets.append({
            'range': f"${lo // 1000}K - ${hi // 1000}K",
            'count': count,
            'low': lo,
            'high': hi,
        })

    # Percentiles
    p25 = salaries[n // 4] if n >= 4 else low
    p75 = salaries[3 * n // 4] if n >= 4 else high

    return {
        'available': True,
        'count': n,
        'average': avg,
        'median': median,
        'min': low,
        'max': high,
        'p25': p25,
        'p75': p75,
        'buckets': buckets,
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  SKILL DEMAND TRACKER
# ═══════════════════════════════════════════════════════════════════════════════

# Skills to track (ServiceNow ecosystem)
TRACKED_SKILLS = [
    'ITSM', 'ITOM', 'ITBM', 'CSM', 'HRSD', 'SAM', 'HAM',
    'Flow Designer', 'Integration Hub', 'Virtual Agent',
    'Service Portal', 'Service Catalog', 'CMDB', 'Discovery',
    'Business Rules', 'Client Scripts', 'Script Includes',
    'UI Policies', 'UI Actions', 'ACLs', 'REST API', 'SOAP',
    'GlideRecord', 'ATF', 'JavaScript', 'AngularJS', 'React',
    'Agile', 'ITIL', 'Scrum',
    'CSA', 'CIS-ITSM', 'CIS-SAM', 'CAD', 'CIS-CSM',
    'NowAssist', 'GenAI', 'Predictive Intelligence',
    'App Engine', 'Creator Workflow', 'Performance Analytics',
    'SecOps', 'GRC', 'IRM', 'TPRM',
    'FSM', 'Field Service', 'Telecom',
    'Domain Separation', 'Multi-Instance',
    'Cloud', 'Azure', 'AWS',
    'Python', 'PowerShell', 'SQL',
]


def skill_demand(jobs: list) -> dict:
    """
    Count how often each skill appears across ALL job descriptions.
    Returns sorted list of {skill, count, percentage, trend}.
    """
    total = len(jobs)
    if total == 0:
        return {'skills': [], 'total_jobs': 0}

    skill_counts = Counter()

    for job in jobs:
        text = (job.get('title', '') + ' ' + job.get('description', '')).lower()
        seen = set()
        for skill in TRACKED_SKILLS:
            sl = skill.lower()
            if sl in text and sl not in seen:
                skill_counts[skill] += 1
                seen.add(sl)

    # Sort by frequency
    results = []
    for skill, count in skill_counts.most_common(30):
        pct = round(count / total * 100, 1)
        # Classify demand heat
        if pct >= 50:
            heat = 'hot'
        elif pct >= 25:
            heat = 'warm'
        elif pct >= 10:
            heat = 'moderate'
        else:
            heat = 'niche'

        results.append({
            'skill': skill,
            'count': count,
            'percentage': pct,
            'heat': heat,
        })

    return {
        'skills': results,
        'total_jobs': total,
        'top_5': [r['skill'] for r in results[:5]],
        'emerging': [r['skill'] for r in results if r['heat'] == 'niche'][:5],
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  SOURCE QUALITY SCORING
# ═══════════════════════════════════════════════════════════════════════════════

def source_quality(jobs: list, dupes_removed: int = 0) -> dict:
    """
    Rank job sources by quality: unique jobs, salary data, description quality.
    """
    source_data = defaultdict(lambda: {
        'total': 0, 'with_salary': 0, 'with_desc': 0,
        'avg_desc_len': 0, 'desc_lens': [], 'salary_values': [],
        'with_url': 0,
    })

    for job in jobs:
        src = job.get('source', 'unknown').upper()
        d = source_data[src]
        d['total'] += 1
        sal = job.get('salary', '')
        if sal and sal.lower() not in ('not specified', 'competitive', 'n/a', ''):
            d['with_salary'] += 1
            parsed = normalize_salary(sal)
            if parsed.get('parseable'):
                d['salary_values'].append(parsed['midpoint_usd'])
        desc = job.get('description', '')
        if desc and len(desc) > 50:
            d['with_desc'] += 1
            d['desc_lens'].append(len(desc))
        if job.get('url', '').startswith('http'):
            d['with_url'] += 1

    results = []
    for src, d in source_data.items():
        total = d['total']
        if total == 0:
            continue

        # Quality scoring (0-100)
        score = 0
        # Volume (up to 25)
        score += min(total * 2, 25)
        # Salary data completeness (up to 25)
        sal_pct = d['with_salary'] / total * 100
        score += int(sal_pct * 0.25)
        # Description richness (up to 25)
        desc_pct = d['with_desc'] / total * 100
        avg_len = int(sum(d['desc_lens']) / len(d['desc_lens'])) if d['desc_lens'] else 0
        score += int(desc_pct * 0.15) + min(avg_len // 50, 10)
        # URL completeness (up to 15)
        url_pct = d['with_url'] / total * 100
        score += int(url_pct * 0.15)
        # Cap
        score = min(score, 100)

        # Grade
        if score >= 80:
            grade = 'A'
        elif score >= 60:
            grade = 'B'
        elif score >= 40:
            grade = 'C'
        else:
            grade = 'D'

        results.append({
            'source': src,
            'total_jobs': total,
            'quality_score': score,
            'grade': grade,
            'salary_coverage': round(sal_pct, 1),
            'desc_coverage': round(desc_pct, 1),
            'avg_desc_length': avg_len,
            'avg_salary': int(sum(d['salary_values']) / len(d['salary_values'])) if d['salary_values'] else 0,
        })

    results.sort(key=lambda x: x['quality_score'], reverse=True)

    return {
        'sources': results,
        'total_jobs': len(jobs),
        'total_sources': len(results),
        'best_source': results[0]['source'] if results else 'N/A',
        'dupes_removed': dupes_removed,
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  MARKET PULSE (aggregate dashboard)
# ═══════════════════════════════════════════════════════════════════════════════

def market_pulse(jobs: list, dupes_removed: int = 0) -> dict:
    """
    Aggregate market intelligence dashboard.
    Combines salary, skills, sources, and location analysis.
    """
    # Location breakdown
    loc_counter = Counter()
    remote_count = 0
    for job in jobs:
        loc = (job.get('location') or 'Unknown').strip()
        if loc:
            # Simplify to country/state level
            simplified = _simplify_location(loc)
            loc_counter[simplified] += 1
        wt = (job.get('work_type') or '').lower()
        if 'remote' in wt or job.get('remote'):
            remote_count += 1

    # Work type breakdown
    work_types = Counter()
    for job in jobs:
        wt = job.get('work_type', 'Unknown')
        work_types[wt] += 1

    return {
        'salary': salary_distribution(jobs),
        'skills': skill_demand(jobs),
        'sources': source_quality(jobs, dupes_removed),
        'locations': {
            'top': [{'location': loc, 'count': cnt} for loc, cnt in loc_counter.most_common(10)],
            'remote_count': remote_count,
            'remote_pct': round(remote_count / max(len(jobs), 1) * 100, 1),
        },
        'work_types': [{'type': t, 'count': c} for t, c in work_types.most_common()],
        'total_jobs': len(jobs),
        'generated_at': datetime.now().isoformat(),
    }


def _simplify_location(loc: str) -> str:
    """Simplify a location string to a broad region."""
    loc_lower = loc.lower()
    # Canada provinces
    ca_map = {
        'toronto': 'Ontario, CA', 'ontario': 'Ontario, CA',
        'vancouver': 'BC, CA', 'british columbia': 'BC, CA',
        'montreal': 'Quebec, CA', 'quebec': 'Quebec, CA',
        'ottawa': 'Ontario, CA', 'calgary': 'Alberta, CA',
        'alberta': 'Alberta, CA', 'canada': 'Canada',
    }
    for key, val in ca_map.items():
        if key in loc_lower:
            return val

    # US states
    us_map = {
        'new york': 'New York, US', 'california': 'California, US',
        'texas': 'Texas, US', 'virginia': 'Virginia, US',
        'massachusetts': 'Massachusetts, US', 'illinois': 'Illinois, US',
        'usa': 'United States', 'united states': 'United States',
    }
    for key, val in us_map.items():
        if key in loc_lower:
            return val

    # UK/Europe
    if 'london' in loc_lower or 'england' in loc_lower or 'uk' in loc_lower:
        return 'United Kingdom'
    if 'remote' in loc_lower:
        return 'Remote'

    return loc[:40]
