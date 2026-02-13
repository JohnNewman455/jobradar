#!/usr/bin/env python3
"""
Scraper Diagnostic Tool
Tests all scrapers and reports which ones are working
"""

import sys
sys.path.append('.')

from scrapers.jobspy_scraper import JobSpyIndeedScraper, JobSpyLinkedInScraper, JobSpyGlassdoorScraper, JobSpyZipRecruiterScraper
from scrapers.remoteok_scraper import RemoteOKScraper
from scrapers.weworkremotely_scraper import WeWorkRemotelyScraper
from scrapers.servicenow_careers_scraper import ServiceNowCareersScraper
from scrapers.nelson_frank_scraper import NelsonFrankScraper
from scrapers.adzuna_scraper import AdzunaScraper
from scrapers.dice_scraper import DiceScraper
from scrapers.talent_com_scraper import TalentComScraper
from scrapers.jooble_scraper import JoobleScraper
import time

# Test configuration
JOB_TITLE = "ServiceNow Developer"
LOCATION = "Canada"
REMOTE = True

scrapers_to_test = [
    ("Indeed (JobSpy)", JobSpyIndeedScraper),
    ("LinkedIn (JobSpy)", JobSpyLinkedInScraper),
    ("Glassdoor (JobSpy)", JobSpyGlassdoorScraper),
    ("ZipRecruiter (JobSpy)", JobSpyZipRecruiterScraper),
    ("RemoteOK", RemoteOKScraper),
    ("WeWorkRemotely", WeWorkRemotelyScraper),
    ("ServiceNow Careers", ServiceNowCareersScraper),
    ("Nelson Frank", NelsonFrankScraper),
    ("Adzuna", AdzunaScraper),
    ("Dice", DiceScraper),
    ("Talent.com", TalentComScraper),
    ("Jooble", JoobleScraper),
]

print("="*70)
print("🔬 SCRAPER DIAGNOSTIC TEST")
print("="*70)
print(f"Search: {JOB_TITLE} in {LOCATION} (Remote: {REMOTE})")
print("="*70)
print()

results = []

for name, scraper_class in scrapers_to_test:
    print(f"\n{'='*70}")
    print(f"Testing: {name}")
    print(f"{'='*70}")
    
    try:
        start = time.time()
        scraper = scraper_class()
        jobs = scraper.scrape(JOB_TITLE, LOCATION, REMOTE)
        elapsed = time.time() - start
        
        status = "✅ PASS" if len(jobs) > 0 else "⚠️  ZERO RESULTS"
        color = "\033[92m" if len(jobs) > 0 else "\033[93m"
        reset = "\033[0m"
        
        print(f"{color}{status}{reset} - {len(jobs)} jobs in {elapsed:.1f}s")
        
        if len(jobs) > 0:
            print(f"\n📋 Sample jobs:")
            for i, job in enumerate(jobs[:3], 1):
                print(f"  {i}. {job.get('title', 'N/A')} at {job.get('company', 'N/A')}")
                print(f"     Posted: {job.get('posted_date', 'N/A')}")
                print(f"     Remote: {job.get('remote', False)}")
        
        results.append({
            'name': name,
            'status': 'PASS' if len(jobs) > 0 else 'ZERO',
            'count': len(jobs),
            'time': elapsed
        })
        
    except Exception as e:
        print(f"\033[91m❌ FAIL\033[0m - {type(e).__name__}: {str(e)}")
        results.append({
            'name': name,
            'status': 'FAIL',
            'count': 0,
            'time': 0,
            'error': str(e)
        })
    
    time.sleep(2)  # Delay between tests

# Summary
print("\n\n" + "="*70)
print("📊 SUMMARY REPORT")
print("="*70)

passing = [r for r in results if r['status'] == 'PASS']
zero = [r for r in results if r['status'] == 'ZERO']
failing = [r for r in results if r['status'] == 'FAIL']

print(f"\n✅ WORKING ({len(passing)}):")
for r in passing:
    print(f"   {r['name']}: {r['count']} jobs in {r['time']:.1f}s")

print(f"\n⚠️  ZERO RESULTS ({len(zero)}):")
for r in zero:
    print(f"   {r['name']}: May be blocked or no matching jobs ({r['time']:.1f}s)")

print(f"\n❌ FAILING ({len(failing)}):")
for r in failing:
    print(f"   {r['name']}: {r.get('error', 'Unknown error')}")

print(f"\n{'='*70}")
print(f"Total Tested: {len(results)}")
print(f"Working: {len(passing)}/{len(results)}")
print(f"Success Rate: {len(passing)/len(results)*100:.1f}%")
print(f"{'='*70}")

if len(passing) < 4:
    print("\n⚠️  WARNING: Less than 4 scrapers working!")
    print("   This is below expected performance.")
    print("   Recommended: Focus on fixing JobSpy scrapers first.")
