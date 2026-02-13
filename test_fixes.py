#!/usr/bin/env python3
"""
Test script to verify the fixes
"""

# Test 1: Relevance filtering
print("=" * 60)
print("TEST 1: Relevance Filtering")
print("=" * 60)

from utils.text_utils import is_job_relevant

# Test jobs
test_jobs = [
    {
        'title': 'ServiceNow Developer',
        'description': 'Looking for ServiceNow platform developer',
        'company': 'Tech Corp'
    },
    {
        'title': 'Senior Software Engineer',
        'description': 'React and Node.js developer needed',
        'company': 'Startup Inc'
    },
    {
        'title': 'Full Stack Developer',
        'description': 'Work with ServiceNow integrations and custom apps',
        'company': 'Enterprise Co'
    },
    {
        'title': 'Shopify Web Developer',
        'description': 'Build Shopify themes and apps',
        'company': 'E-commerce Agency'
    }
]

search_query = "ServiceNow Developer"
print(f"\nSearch Query: '{search_query}'")
print(f"Filter Logic: ALL keywords must be present\n")

for i, job in enumerate(test_jobs, 1):
    is_relevant = is_job_relevant(job, search_query)
    status = "✅ PASS" if is_relevant else "❌ FILTERED"
    print(f"{status} Job {i}: {job['title']}")
    print(f"  Company: {job['company']}")
    print(f"  Description: {job['description'][:50]}...")
    print()

# Test 2: Time formatting
print("=" * 60)
print("TEST 2: Time Formatting")
print("=" * 60)

from utils.text_utils import get_time_ago
from datetime import datetime, timedelta, timezone

test_times = [
    (datetime.now(timezone.utc) - timedelta(hours=2), "2 hours ago"),
    (datetime.now(timezone.utc) - timedelta(days=1), "1 day ago"),
    (datetime.now(timezone.utc) - timedelta(days=5), "5 days ago"),
    (datetime.now(timezone.utc) - timedelta(weeks=2), "2 weeks ago"),
    ("2026-02-07T02:00:33+00:00", "should show days ago"),
]

for timestamp, expected in test_times:
    result = get_time_ago(timestamp)
    print(f"Input: {timestamp}")
    print(f"Output: {result}")
    print()

# Test 3: HTML stripping
print("=" * 60)
print("TEST 3: HTML Stripping")
print("=" * 60)

from utils.text_utils import strip_html

html_samples = [
    '<p><b>Company Description</b></p><p>&nbsp;</p><p><b>POWERING CRYPTO WITH DATA</b></p>',
    'Are you a talented Senior Developer looking for a remote job?',
    '<div>Test <span>with</span> tags</div>',
]

for html in html_samples:
    clean = strip_html(html)
    print(f"HTML: {html[:50]}...")
    print(f"Clean: {clean}")
    print()

print("=" * 60)
print("✅ All tests complete!")
print("=" * 60)
