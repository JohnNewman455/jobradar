"""
Job Scraper Tool - Main Application
Real-time job scraping with live updates
"""

from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
import json
import os
import time
import random
import threading
from datetime import datetime, timedelta
import re as _re

# --- Safe scraper imports: if a package is missing, the scraper is set to None ---

def _safe_import(module, names):
    """Import names from a module, returning None for each on failure."""
    results = {}
    try:
        mod = __import__(module, fromlist=names)
        for name in names:
            results[name] = getattr(mod, name, None)
    except Exception as e:
        print(f"⚠️  Could not import {module}: {e}")
        for name in names:
            results[name] = None
    return results

# JobSpy scrapers (working for Indeed, ZipRecruiter, Glassdoor)
_jobspy = _safe_import('scrapers.jobspy_scraper', ['JobSpyIndeedScraper', 'JobSpyZipRecruiterScraper', 'JobSpyGlassdoorScraper', 'JobSpyAllScraper'])
JobSpyIndeedScraper = _jobspy['JobSpyIndeedScraper']
JobSpyZipRecruiterScraper = _jobspy['JobSpyZipRecruiterScraper']
JobSpyGlassdoorScraper = _jobspy['JobSpyGlassdoorScraper']
JobSpyAllScraper = _jobspy['JobSpyAllScraper']

# LinkedIn Guest Scraper (replacement for JobSpy LinkedIn)
_li = _safe_import('scrapers.linkedin_guest_scraper', ['LinkedInGuestScraper'])
LinkedInGuestScraper = _li['LinkedInGuestScraper']

# Working scrapers
_rok = _safe_import('scrapers.remoteok_scraper', ['RemoteOKScraper'])
RemoteOKScraper = _rok['RemoteOKScraper']

_wwr = _safe_import('scrapers.weworkremotely_scraper', ['WeWorkRemotelyScraper'])
WeWorkRemotelyScraper = _wwr['WeWorkRemotelyScraper']

_snc = _safe_import('scrapers.servicenow_careers_scraper', ['ServiceNowCareersScraper'])
ServiceNowCareersScraper = _snc['ServiceNowCareersScraper']

_ser = _safe_import('scrapers.serper_scraper', ['SerperGoogleJobsScraper'])
SerperGoogleJobsScraper = _ser['SerperGoogleJobsScraper']

_nf = _safe_import('scrapers.nelson_frank_scraper', ['NelsonFrankScraper', 'NelsonFrankAPIScraper'])
NelsonFrankScraper = _nf['NelsonFrankScraper']
NelsonFrankAPIScraper = _nf['NelsonFrankAPIScraper']

_snp = _safe_import('scrapers.sn_pro_api_scraper', ['SNProAPIScraper', 'SNProScraper'])
SNProAPIScraper = _snp['SNProAPIScraper']
SNProScraper = _snp['SNProScraper']

_gfb = _safe_import('scrapers.google_fallback_scraper', ['GoogleFallbackScraper'])
GoogleFallbackScraper = _gfb['GoogleFallbackScraper']

# Canadian scrapers
_ca = _safe_import('scrapers.canadian_scrapers', ['ElutaScraper', 'JobTomeScraper', 'JobRapidoScraper'])
ElutaScraper = _ca['ElutaScraper']
JobTomeScraper = _ca['JobTomeScraper']
JobRapidoScraper = _ca['JobRapidoScraper']

_wp = _safe_import('scrapers.workopolis_scraper', ['WorkopolisScraper'])
WorkopolisScraper = _wp['WorkopolisScraper']

_rr = _safe_import('scrapers.remoterocketship_scraper', ['RemoteRocketshipScraper'])
RemoteRocketshipScraper = _rr['RemoteRocketshipScraper']

# Backup scrapers (may be blocked)
_gj = _safe_import('scrapers.google_jobs_scraper', ['GoogleJobsScraper'])
GoogleJobsScraper = _gj['GoogleJobsScraper']

_dc = _safe_import('scrapers.dice_scraper', ['DiceScraper'])
DiceScraper = _dc['DiceScraper']

_tc = _safe_import('scrapers.talent_com_scraper', ['TalentComScraper'])
TalentComScraper = _tc['TalentComScraper']

_jb = _safe_import('scrapers.jooble_scraper', ['JoobleScraper'])
JoobleScraper = _jb['JoobleScraper']

_wf = _safe_import('scrapers.wellfound_scraper', ['WellfoundScraper'])
WellfoundScraper = _wf['WellfoundScraper']

_shca = _safe_import('scrapers.simplyhired_ca_scraper', ['SimplyHiredCAScraper'])
SimplyHiredCAScraper = _shca['SimplyHiredCAScraper']

_adz = _safe_import('scrapers.adzuna_scraper', ['AdzunaScraper'])
AdzunaScraper = _adz['AdzunaScraper']

# New scrapers (2026 updates)
_zrg = _safe_import('scrapers.ziprecruiter_google_scraper', ['ZipRecruiterGoogleScraper'])
ZipRecruiterGoogleScraper = _zrg['ZipRecruiterGoogleScraper']

_sh = _safe_import('scrapers.simplyhired_scraper', ['SimplyHiredScraper'])
SimplyHiredScraper = _sh['SimplyHiredScraper']

_rco = _safe_import('scrapers.remote_co_scraper', ['RemoteCoScraper'])
RemoteCoScraper = _rco['RemoteCoScraper']

_us = _safe_import('scrapers.us_scrapers', ['BuiltInScraper', 'USAJobsScraper'])
BuiltInScraper = _us['BuiltInScraper']
USAJobsScraper = _us['USAJobsScraper']

from utils.job_storage import JobStorage
from utils.export_utils import export_to_csv, export_to_excel
from utils.text_utils import strip_html, truncate_text, get_time_ago, is_job_relevant, calculate_relevance_score, detect_work_type
from utils.scorer import calculate_match_score
from utils.optimizer import optimize_resume
from utils.scheduler import scheduler
from utils.ghost_detector import ghost_detector
from utils.generator import generate_cover_letter, generate_cold_message, rewrite_bullet, generate_thank_you
from utils.market_analytics import market_pulse, salary_distribution, skill_demand, source_quality
import queue

# Global resume text (can be updated via API)
resume_text = None

app = Flask(__name__)
CORS(app)

# Global storage for jobs and scraping status
job_storage = JobStorage()
scraping_active = False
job_queue = queue.Queue()
custom_sources = []  # Store custom user-added sources

# Progress tracking
current_site = None
site_progress = {}  # {site_name: progress_percentage}
total_sites = 0
completed_sites = 0
scraper_results = {}  # {site_name: {total: N, relevant: N, status: 'ok'|'error'|'zero', time: X}}

# Available scrapers (JobSpy = working, others = may be blocked)
SCRAPERS = {
    # 🚀 JOBSPY SCRAPERS (working with anti-bot bypass)
    'indeed': JobSpyIndeedScraper,  # ✅ JobSpy - WORKING!
    'linkedin': LinkedInGuestScraper,  # ✅ LinkedIn Guest API - WORKING BETTER!
    'ziprecruiter': ZipRecruiterGoogleScraper,  # ✅ Google Search Method - WORKING!
    'glassdoor': JobSpyGlassdoorScraper,  # ✅ JobSpy - WORKING!
    'jobspy_all': JobSpyAllScraper,  # ✅ Indeed + Glassdoor + ZipRecruiter (without LinkedIn)
    
    # 🔧 WORKING SCRAPERS (official APIs)
    'remoteok': RemoteOKScraper,  # ✅ Official API
    'servicenow': ServiceNowCareersScraper,  # ✅ Official careers
    'nelsonfrank': NelsonFrankAPIScraper,  # ✅ UPGRADED: Multi-platform scraper
    'snpro': SNProAPIScraper,  # ✅ UPGRADED: Algolia API scraper
    'weworkremotely': WeWorkRemotelyScraper,  # ✅ WORKS
    'serper': SerperGoogleJobsScraper,  # ✅ Google Jobs aggregator
    
    # 🇨🇦 CANADIAN JOB SITES
    'jobrapido': JobRapidoScraper,  # ✅ JobRapido Canada
    'simplyhired_ca': SimplyHiredCAScraper,  # ✅ SimplyHired Canada
    
    # ⚠️  BACKUP SCRAPERS
    'dice': DiceScraper,  # ✅ Multi-strategy
    'simplyhired': SimplyHiredScraper,  # ✅ curl_cffi
    'remotecom': RemoteCoScraper,  # ✅ Remote.co
    'builtin': BuiltInScraper,  # ✅ US tech startup jobs
    'usajobs': USAJobsScraper,  # ✅ US Government jobs
    'talent': TalentComScraper,  # ✅ Talent.com (rewritten)
    'adzuna': AdzunaScraper,  # ✅ Actually Jobicy + Remotive APIs
    
    # ❌ DISABLED — dead/broken sites
    # 'eluta': ElutaScraper,  # Defunct since 2023
    # 'workopolis': WorkopolisScraper,  # Redirects to Indeed
    # 'google': GoogleJobsScraper,  # JS-rendered, needs Selenium
    # 'wellfound': WellfoundScraper,  # React SPA, parser broken
    # 'remoterocketship': RemoteRocketshipScraper,  # Selectors broken
    # 'jobtome': JobTomeScraper,  # Guess selectors
    # 'jooble': JoobleScraper,  # Hard IP blocks
}


@app.route('/')
def index():
    """Render the main dashboard"""
    return render_template('index_v2.html')


@app.route('/reports/<filename>')
def serve_report(filename):
    """Serve saved email reports."""
    from flask import send_from_directory
    reports_dir = os.path.join(os.path.dirname(__file__), 'reports')
    return send_from_directory(reports_dir, filename)


@app.route('/api/start', methods=['POST'])
def start_scraping():
    """Start the scraping process"""
    global scraping_active
    
    if scraping_active:
        return jsonify({'error': 'Scraping already in progress'}), 400
    
    data = request.json
    job_title = data.get('job_title', 'Software Engineer')
    location = data.get('location', 'United States')
    remote = data.get('remote', True)
    sites = data.get('sites', ['indeed', 'remoteok', 'weworkremotely'])  # Sites in user-defined order
    
    # Clear previous results
    job_storage.clear()
    
    # Start scraping in background thread
    scraping_active = True
    thread = threading.Thread(
        target=run_scrapers,
        args=(job_title, location, remote, sites)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'status': 'started',
        'message': 'Scraping started successfully',
        'sites': sites
    })


@app.route('/api/stop', methods=['POST'])
def stop_scraping():
    """Stop the scraping process"""
    global scraping_active
    scraping_active = False
    return jsonify({'status': 'stopped', 'message': 'Scraping stopped'})


@app.route('/api/status')
def get_status():
    """Get current scraping status"""
    global current_site, site_progress, total_sites, completed_sites
    
    status_data = {
        'active': scraping_active,
        'total_jobs': job_storage.count(),
        'duplicates_removed': job_storage.duplicates_removed,
        'sites_scraped': job_storage.get_site_stats(),
        'current_site': current_site,
        'site_progress': site_progress,
        'total_sites': total_sites,
        'completed_sites': completed_sites,
        'scraper_results': scraper_results,
    }
    
    # DEBUG: Periodically log status
    if scraping_active and completed_sites % 5 == 0:  # Every 5 sites
        print(f"📊 Status check: {completed_sites}/{total_sites} sites, {job_storage.count()} jobs")
    
    return jsonify(status_data)


@app.route('/api/jobs')
def get_jobs():
    """Get all scraped jobs"""
    filters = {
        'site': request.args.get('site'),
        'min_salary': request.args.get('min_salary'),
        'remote_only': request.args.get('remote_only') == 'true'
    }
    
    jobs = job_storage.get_all(filters)
    
    # Sort by match_score descending by default
    sort_by = request.args.get('sort', 'match_score')
    if sort_by == 'match_score':
        jobs = sorted(jobs, key=lambda j: j.get('match_score', 0), reverse=True)
    elif sort_by == 'recent':
        jobs = sorted(jobs, key=lambda j: j.get('posted_timestamp', 0), reverse=True)
    elif sort_by == 'salary':
        jobs = sorted(jobs, key=lambda j: j.get('salary_numeric', 0), reverse=True)
    
    return jsonify({'jobs': jobs, 'count': len(jobs)})


@app.route('/api/debug/test-indeed')
def debug_test_indeed():
    """Debug endpoint to test Indeed scraper directly"""
    try:
        from scrapers.indeed_scraper import IndeedScraper
        scraper = IndeedScraper()
        jobs = scraper.scrape('QA Automation engineer', 'Canada', remote=True)
        return jsonify({
            'success': True,
            'jobs_found': len(jobs),
            'sample': jobs[0] if jobs else None,
            'error': None
        })
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/stream')
def stream_jobs():
    """Server-Sent Events stream for real-time job updates.
    Has a max lifetime of 60s to avoid blocking gunicorn workers forever.
    Client will reconnect automatically via EventSource."""
    def generate():
        last_count = 0
        start = time.time()
        max_lifetime = 60  # seconds – prevents blocking gunicorn workers
        while time.time() - start < max_lifetime:
            current_count = job_storage.count()
            
            if current_count > last_count:
                new_jobs = job_storage.get_recent(current_count - last_count)
                for job in new_jobs:
                    data = json.dumps(job)
                    yield f"data: {data}\n\n"
                last_count = current_count
            
            if not scraping_active and job_queue.empty():
                yield f"data: {json.dumps({'status': 'complete'})}\n\n"
                return
                
            time.sleep(1)
        # Timeout reached — send a reconnect hint
        yield f"data: {json.dumps({'status': 'reconnect'})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


@app.route('/api/export/<format>')
def export_jobs(format):
    """Export jobs to CSV, Excel, or JSON"""
    jobs = job_storage.get_all()
    
    if format == 'csv':
        csv_data = export_to_csv(jobs)
        return Response(
            csv_data,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=jobs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
        )
    elif format == 'excel':
        excel_data = export_to_excel(jobs)
        return Response(
            excel_data,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': f'attachment; filename=jobs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'}
        )
    elif format == 'json':
        from utils.export_utils import export_to_json
        json_data = export_to_json(jobs)
        return Response(
            json_data,
            mimetype='application/json',
            headers={'Content-Disposition': f'attachment; filename=jobs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'}
        )
    else:
        return jsonify({'error': 'Invalid format'}), 400


def run_scrapers(job_title, location, remote, sites):
    """Run all selected scrapers in the specified order"""
    global scraping_active, current_site, site_progress, total_sites, completed_sites, scraper_results
    
    relevant_count = 0
    filtered_count = 0
    
    # Initialize progress tracking
    total_sites = len(sites)
    completed_sites = 0
    site_progress = {site: 0 for site in sites}
    scraper_results = {site: {'total': 0, 'relevant': 0, 'status': 'pending', 'time': 0} for site in sites}
    
    for idx, site in enumerate(sites, 1):
        if not scraping_active:
            break
        
        # Update current site
        current_site = site
        site_progress[site] = 0
        
        if site in SCRAPERS:
            scraper_class = SCRAPERS[site]
            
            # Skip if scraper not implemented (None)
            if scraper_class is None:
                print(f"⚠️  {site}: Not implemented (requires API or authentication)")
                site_progress[site] = 100
                completed_sites += 1
                scraper_results[site] = {'total': 0, 'relevant': 0, 'status': 'needs_api', 'time': 0}
                continue
            
            try:
                print(f"\n{'='*60}")
                print(f"🔍 [{idx}/{len(sites)}] Starting scan: {site.upper()}")
                print(f"{'='*60}")
                site_progress[site] = 25
                
                # ADD RANDOM DELAY (Anti-bot protection)
                delay = random.uniform(1.5, 3.5)
                print(f"⏳ Waiting {delay:.1f}s before scraping (anti-bot)...")
                # Split delay into small chunks so stop is responsive
                waited = 0
                while waited < delay and scraping_active:
                    time.sleep(0.3)
                    waited += 0.3
                if not scraping_active:
                    break
                
                scraper = scraper_class()
                print(f"📡 {site}: Connecting to source...")
                site_progress[site] = 50
                
                start_time = time.time()
                jobs = scraper.scrape(job_title, location, remote)
                elapsed = time.time() - start_time
                
                site_progress[site] = 100
                completed_sites += 1
                
                # Track per-scraper totals
                site_total = len(jobs)
                site_relevant = 0
                
                # IMPROVED LOGGING
                if len(jobs) > 0:
                    print(f"✅ [{idx}/{len(sites)}] {site.upper()}: Found {len(jobs)} jobs in {elapsed:.1f}s")
                else:
                    print(f"⚠️  [{idx}/{len(sites)}] {site.upper()}: Found 0 jobs in {elapsed:.1f}s")
                    
                    # 🔄 ONLY use Google Fallback for major JobSpy sites to avoid rate limiting
                    major_sites = ['indeed', 'linkedin', 'glassdoor', 'ziprecruiter']
                    if site.lower() in major_sites:
                        print(f"   💡 Attempting Google Fallback for major site...")
                        try:
                            fallback_scraper = GoogleFallbackScraper()
                            backup_jobs = fallback_scraper.scrape(site, job_title, location)
                            
                            if len(backup_jobs) > 0:
                                print(f"✅ Google Fallback found {len(backup_jobs)} jobs for {site.upper()}!")
                                jobs = backup_jobs
                                site_total = len(jobs)
                            else:
                                print(f"❌ Google Fallback: No additional jobs found")
                        except Exception as fallback_error:
                            print(f"❌ Google Fallback: {str(fallback_error)[:100]}")
                    else:
                        print(f"   ℹ️  Skipping Google Fallback to avoid rate limits")
                
                for job in jobs:
                    # --- DATA SANITIZATION: ensure string fields are actually strings ---
                    for _field in ('title', 'company', 'location', 'description', 'url'):
                        val = job.get(_field)
                        if val is not None and not isinstance(val, str):
                            if isinstance(val, dict):
                                job[_field] = val.get('name', '') or val.get('label', '') or str(val)
                            else:
                                job[_field] = str(val)
                    
                    # VERY RELAXED FILTER: Only check if main keyword present (e.g., "ServiceNow")
                    # Show ALL jobs with ServiceNow mentioned anywhere in title or description
                    if not is_job_relevant(job, job_title):
                        filtered_count += 1
                        continue
                    
                    relevance_score = calculate_relevance_score(job, job_title)
                    
                    # Process job data
                    job['source'] = site
                    job['relevance_score'] = relevance_score
                    job['scraped_at'] = datetime.now().isoformat()
                    
                    # Clean up description (strip HTML)
                    if job.get('description'):
                        clean_desc = strip_html(job['description'])
                        job['description'] = clean_desc
                        job['description_preview'] = truncate_text(clean_desc, 200)
                    
                    # --- UUID CLEANUP: Strip Supabase/internal UUIDs from display fields ---
                    _uuid_re = _re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', _re.I)
                    for field in ('company', 'location', 'title'):
                        val = job.get(field, '')
                        if val and _uuid_re.fullmatch(str(val).strip()):
                            if field == 'company':
                                job[field] = 'Company Not Listed'
                            elif field == 'location':
                                job[field] = 'Location Not Listed'
                            else:
                                job[field] = 'Untitled Position'
                    # Strip UUIDs embedded in descriptions
                    if job.get('description'):
                        job['description'] = _uuid_re.sub('', job['description']).strip()
                        job['description_preview'] = truncate_text(job['description'], 200)
                    # Fix URL that is just a UUID
                    url_val = job.get('url', '')
                    if url_val and _uuid_re.fullmatch(str(url_val).strip()):
                        job['url'] = ''
                    
                    # Ensure work_type is set
                    if not job.get('work_type'):
                        job_remote = job.get('remote', False)
                        job_location = job.get('location', '')
                        desc = job.get('description', '')
                        job['work_type'] = detect_work_type(job_location, desc, job_remote)
                    
                    # Ensure numeric fields for sorting
                    if not job.get('salary_numeric'):
                        job['salary_numeric'] = 0
                    
                    # --- DATE HANDLING: Always provide an exact date ---
                    now = datetime.now()
                    scraped_ts = int(now.timestamp())
                    
                    # 1) Normalize posted_date from various scraper fields
                    raw_date = job.get('posted_date') or job.get('date_posted') or ''
                    
                    # If the date is vague/empty, try timestamp; last resort = scraped_at
                    if raw_date in ('', 'Recently', 'N/A', 'Unknown', None):
                        ts = job.get('posted_timestamp') or 0
                        if ts and int(ts) > 0:
                            try:
                                raw_dt = datetime.fromtimestamp(int(ts))
                                raw_date = raw_dt.strftime('%b %d, %Y')
                            except Exception:
                                raw_date = ''
                        if not raw_date or raw_date in ('Recently', ''):
                            # Fallback: use today's date (when we scraped it)
                            raw_date = now.strftime('%b %d, %Y')
                    
                    # 2) Convert relative dates ("3 days ago") to exact dates
                    m_days = _re.search(r'(\d+)\s*days?\s*ago', str(raw_date), _re.I)
                    m_weeks = _re.search(r'(\d+)\s*weeks?\s*ago', str(raw_date), _re.I)
                    m_months = _re.search(r'(\d+)\s*months?\s*ago', str(raw_date), _re.I)
                    
                    if str(raw_date).strip().lower() in ('today', 'just now', 'just posted'):
                        raw_date = now.strftime('%b %d, %Y')
                    elif str(raw_date).strip().lower() in ('yesterday',):
                        raw_date = (now - timedelta(days=1)).strftime('%b %d, %Y')
                    elif m_days:
                        d = int(m_days.group(1))
                        raw_date = (now - timedelta(days=d)).strftime('%b %d, %Y')
                    elif m_weeks:
                        w = int(m_weeks.group(1))
                        raw_date = (now - timedelta(weeks=w)).strftime('%b %d, %Y')
                    elif m_months:
                        mo = int(m_months.group(1))
                        raw_date = (now - timedelta(days=mo * 30)).strftime('%b %d, %Y')
                    
                    # 3) Try to parse any ISO / full date format into consistent "Feb 12, 2026"
                    try:
                        for fmt in ('%Y-%m-%dT%H:%M:%S', '%Y-%m-%d', '%B %d, %Y', '%b %d, %Y', '%d/%m/%Y', '%m/%d/%Y'):
                            try:
                                parsed = datetime.strptime(str(raw_date)[:19], fmt)
                                raw_date = parsed.strftime('%b %d, %Y')
                                break
                            except ValueError:
                                continue
                    except Exception:
                        pass
                    
                    job['posted_date'] = raw_date
                    
                    # 4) Ensure posted_timestamp is always set (for sorting)
                    if not job.get('posted_timestamp') or int(job.get('posted_timestamp', 0)) == 0:
                        # Try to derive from the cleaned date
                        try:
                            pts = datetime.strptime(raw_date, '%b %d, %Y')
                            job['posted_timestamp'] = int(pts.timestamp())
                        except Exception:
                            job['posted_timestamp'] = scraped_ts
                    
                    # Calculate resume match score
                    job['match_score'] = calculate_match_score(
                        job.get('description', ''),
                        job.get('title', ''),
                        resume_text
                    )

                    # Ghost job detection
                    ghost = ghost_detector.analyse(job)
                    job['ghost_score'] = ghost['ghost_score']
                    job['is_ghost'] = ghost['is_ghost']
                    job['ghost_flags'] = ghost['flags']
                    
                    job_storage.add(job)
                    job_queue.put(job)
                    relevant_count += 1
                    site_relevant += 1
                    
                # Record scraper results
                scraper_results[site] = {
                    'total': site_total,
                    'relevant': site_relevant,
                    'status': 'ok' if site_relevant > 0 else ('zero' if site_total == 0 else 'filtered'),
                    'time': round(elapsed, 1)
                }
                    
            except Exception as e:
                print(f"\n❌ ERROR scraping {site.upper()}:")
                print(f"   Error type: {type(e).__name__}")
                print(f"   Error message: {str(e)}")
                print(f"\n📋 Full traceback:")
                import traceback
                traceback.print_exc()
                print(f"{'='*60}\n")
                site_progress[site] = 100
                completed_sites += 1
                scraper_results[site] = {'total': 0, 'relevant': 0, 'status': 'error', 'time': 0, 'error': str(e)[:100]}
                continue
    
    # Mark as complete
    scraping_active = False
    current_site = None
    
    # DEBUG: Print final counts
    total_jobs_stored = job_storage.count()
    print(f"\n{'='*60}")
    print(f"✅ Scraping complete!")
    print(f"📊 FINAL BACKEND STATS:")
    print(f"   Total jobs collected: {relevant_count}")
    print(f"   Jobs filtered out: {filtered_count}")
    print(f"   Jobs in storage: {total_jobs_stored}")
    print(f"   Sites scraped: {completed_sites}/{total_sites}")
    if total_jobs_stored != relevant_count:
        print(f"⚠️  WARNING: Storage count ({total_jobs_stored}) != collected count ({relevant_count})")
    print(f"{'='*60}\n")


@app.route('/api/sites')
def get_available_sites():
    """Get list of available job sites"""
    
    # Built-in sources (JobSpy = working)
    built_in_sites = [
        # ✅ JOBSPY SCRAPERS (anti-bot bypass working!)
        {'id': 'indeed', 'name': '✅ Indeed (JobSpy)', 'enabled': True, 'requires_api': False, 'country': 'Global', 'status': 'working'},
        {'id': 'linkedin', 'name': '✅ LinkedIn (Guest API)', 'enabled': True, 'requires_api': False, 'country': 'Global', 'status': 'working'},
        {'id': 'glassdoor', 'name': '✅ Glassdoor (JobSpy)', 'enabled': True, 'requires_api': False, 'country': 'Global', 'status': 'working'},
        {'id': 'ziprecruiter', 'name': '✅ ZipRecruiter (Google)', 'enabled': True, 'requires_api': False, 'country': 'USA', 'status': 'working'},
        
        # ✅ WORKING SCRAPERS (official APIs + ServiceNow-specific)
        {'id': 'nelsonfrank', 'name': '🌟 Nelson Frank (ServiceNow)', 'enabled': True, 'requires_api': False, 'country': 'Global', 'status': 'working'},
        {'id': 'snpro', 'name': '🌟 SN Pro Jobs (ServiceNow)', 'enabled': True, 'requires_api': False, 'country': 'Remote', 'status': 'working'},
        {'id': 'remoteok', 'name': '✅ RemoteOK (API)', 'enabled': True, 'requires_api': False, 'country': 'Remote', 'status': 'working'},
        {'id': 'servicenow', 'name': '✅ ServiceNow Careers', 'enabled': True, 'requires_api': False, 'country': 'Global', 'status': 'working'},
        {'id': 'weworkremotely', 'name': '✅ WeWorkRemotely', 'enabled': True, 'requires_api': False, 'country': 'Remote', 'status': 'working'},
        
        # 🇨🇦 CANADIAN JOB SITES
        {'id': 'jobrapido', 'name': '🇨🇦 JobRapido Canada', 'enabled': True, 'requires_api': False, 'country': 'Canada', 'status': 'working'},
        {'id': 'simplyhired_ca', 'name': '🇨🇦 SimplyHired CA', 'enabled': True, 'requires_api': False, 'country': 'Canada', 'status': 'working'},
        
        # ⚠️  BACKUP SCRAPERS
        {'id': 'serper', 'name': 'Google Jobs (Serper)', 'enabled': True, 'requires_api': True, 'country': 'Global', 'status': 'limited'},
        {'id': 'dice', 'name': '✅ Dice.com', 'enabled': True, 'requires_api': False, 'country': 'US', 'status': 'working'},
        {'id': 'simplyhired', 'name': '✅ SimplyHired', 'enabled': True, 'requires_api': False, 'country': 'US', 'status': 'working'},
        {'id': 'remotecom', 'name': '✅ Remote.co', 'enabled': True, 'requires_api': False, 'country': 'Remote', 'status': 'working'},
        
        # 🇺🇸 US-SPECIFIC JOB SITES
        {'id': 'builtin', 'name': '🇺🇸 BuiltIn (USA)', 'enabled': True, 'requires_api': False, 'country': 'USA', 'status': 'working'},
        {'id': 'usajobs', 'name': '🇺🇸 USAJobs.gov (USA)', 'enabled': True, 'requires_api': False, 'country': 'USA', 'status': 'working'},
        
        # 🆕 NEW SOURCES
        {'id': 'talent', 'name': '✅ Talent.com', 'enabled': True, 'requires_api': False, 'country': 'Global', 'status': 'working'},
        {'id': 'adzuna', 'name': '✅ Jobicy + Remotive (Remote)', 'enabled': True, 'requires_api': False, 'country': 'Remote', 'status': 'working'},
    ]
    
    return jsonify({
        'sites': built_in_sites,
        'custom_sites': custom_sources
    })


@app.route('/api/resume', methods=['POST'])
def update_resume():
    """Update the resume text for matching"""
    global resume_text
    data = request.json
    resume_text = data.get('resume_text', '')
    return jsonify({'status': 'success', 'length': len(resume_text)})


@app.route('/api/resume', methods=['GET'])
def get_resume():
    """Get current resume text"""
    return jsonify({'resume_text': resume_text or ''})


@app.route('/api/dupes')
def get_dupes():
    """Get list of rejected duplicates for verification"""
    return jsonify({
        'dupes': job_storage.get_rejected_dupes(),
        'count': len(job_storage.get_rejected_dupes()),
        'total_removed': job_storage.duplicates_removed
    })


@app.route('/api/rescore', methods=['POST'])
def rescore_jobs():
    """Re-score all existing jobs with current resume"""
    if not resume_text:
        return jsonify({'error': 'No resume saved'}), 400
    
    count = 0
    for job in job_storage.jobs:
        job['match_score'] = calculate_match_score(
            job.get('description', ''),
            job.get('title', ''),
            resume_text
        )
        count += 1
    
    return jsonify({'status': 'success', 'rescored': count})


@app.route('/api/sites/add', methods=['POST'])
def add_custom_site():
    """Add a custom job site"""
    data = request.json
    
    custom_site = {
        'id': f"custom_{len(custom_sources)}",
        'name': data.get('name'),
        'url': data.get('url'),
        'enabled': True,
        'custom': True
    }
    
    custom_sources.append(custom_site)
    
    return jsonify({'status': 'success', 'site': custom_site})


@app.route('/api/progress')
def get_scraping_progress():
    """Get real-time scraping progress for each site"""
    # This will be updated by scrapers
    return jsonify({
        'active': scraping_active,
        'progress': job_storage.get_progress_by_site()
    })


# === RESUME OPTIMIZER ===

@app.route('/api/optimize', methods=['POST'])
def optimize_resume_endpoint():
    """Optimize resume against a specific job description."""
    data = request.json
    resume = data.get('resume_text', '') or resume_text or ''
    job_desc = data.get('job_description', '')
    if not resume or not job_desc:
        return jsonify({'error': 'Both resume and job description are required'}), 400
    result = optimize_resume(resume, job_desc)
    return jsonify(result)


# === SCHEDULER ===

@app.route('/api/schedule', methods=['GET'])
def get_schedule():
    """Get scheduler config."""
    return jsonify(scheduler.get_config())


@app.route('/api/schedule', methods=['POST'])
def update_schedule():
    """Update scheduler config."""
    data = request.json
    config = scheduler.update_config(data)
    # Start/stop based on enabled flag
    if config.get('enabled') and not scheduler.running:
        scheduler.start()
    elif not config.get('enabled') and scheduler.running:
        scheduler.stop()
    return jsonify(scheduler.get_config())


@app.route('/api/schedule/test', methods=['POST'])
def test_schedule_email():
    """Test email: send a real email via Gmail SMTP or save report locally."""
    try:
        data = request.json or {}
        if data:
            scheduler.update_config(data)
    except Exception:
        pass

    email_cfg = scheduler.config.get('email', {})
    recipient = email_cfg.get('to', '')
    sender = email_cfg.get('sender', '') or email_cfg.get('username', '') or recipient
    app_pw = email_cfg.get('app_password', '') or email_cfg.get('password', '')

    if not recipient:
        return jsonify({'status': 'failed', 'error': 'Enter your email address first.'}), 400
    if not app_pw:
        return jsonify({'status': 'failed', 'error': 'App Password required. See the setup instructions above.'}), 400

    # Use real jobs if available, otherwise sample data
    jobs = job_storage.get_all()
    if jobs:
        test_jobs = jobs[:10]
    else:
        test_jobs = [
            {'title': 'ServiceNow Developer (TEST)', 'company': 'Sample Company Inc.',
             'location': 'Toronto, ON', 'match_score': 85, 'url': 'https://example.com/job/1',
             'work_type': 'Remote', 'source': 'test'},
            {'title': 'Senior ITSM Consultant (TEST)', 'company': 'Tech Solutions Ltd.',
             'location': 'Vancouver, BC', 'match_score': 72, 'url': 'https://example.com/job/2',
             'work_type': 'Hybrid', 'source': 'test'},
            {'title': 'Software QA Engineer (TEST)', 'company': 'Digital Corp.',
             'location': 'Remote, Canada', 'match_score': 90, 'url': 'https://example.com/job/3',
             'work_type': 'Remote', 'source': 'test'},
        ]

    try:
        from utils.email_service import send_job_report
        ok, err = send_job_report(sender, app_pw, recipient, test_jobs)
        if ok:
            return jsonify({
                'status': 'sent',
                'jobs_count': len(test_jobs),
                'message': f'✅ Email sent to {recipient} with {len(test_jobs)} jobs! Check your inbox.'
            })
        else:
            return jsonify({'status': 'failed', 'error': err or 'SMTP failed. Check your App Password.'})
    except Exception as e:
        return jsonify({'status': 'failed', 'error': f'Error: {str(e)[:200]}'})


# === RUN SCHEDULE NOW ===

@app.route('/api/schedule/run', methods=['POST'])
def run_schedule_now():
    """Trigger an immediate scrape + email cycle."""
    try:
        results = scheduler.run_now()
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# === APPLIED JOBS (for modal) ===

@app.route('/api/applied', methods=['POST'])
def get_applied_jobs():
    """Get jobs by IDs (for applied jobs modal). Client sends list of applied job IDs."""
    data = request.json
    applied_ids = set(data.get('ids', []))
    if not applied_ids:
        return jsonify({'jobs': [], 'count': 0})
    all_jobs = job_storage.get_all()
    # Match by URL or title+company combo (since localStorage tracks URLs)
    matched = [j for j in all_jobs if j.get('url', '') in applied_ids
               or f"{j.get('title', '')}|{j.get('company', '')}" in applied_ids]
    return jsonify({'jobs': matched, 'count': len(matched)})


# === GHOST JOB DETECTOR ===

@app.route('/api/ghost-check', methods=['POST'])
def ghost_check():
    """Check a single job for ghost indicators."""
    data = request.json
    result = ghost_detector.analyse(data)
    return jsonify(result)


@app.route('/api/ghost-check-all', methods=['GET'])
def ghost_check_all():
    """Run ghost detection on all stored jobs. Returns summary + flagged jobs."""
    all_jobs = job_storage.get_all()
    flagged = []
    total_ghosts = 0
    for job in all_jobs:
        result = ghost_detector.analyse(job)
        if result['is_ghost']:
            total_ghosts += 1
            flagged.append({
                'title': job.get('title', ''),
                'company': job.get('company', ''),
                'url': job.get('url', ''),
                'source': job.get('source', ''),
                **result,
            })
    flagged.sort(key=lambda x: x['ghost_score'], reverse=True)
    return jsonify({
        'total_jobs': len(all_jobs),
        'total_ghosts': total_ghosts,
        'ghost_pct': round(total_ghosts / max(len(all_jobs), 1) * 100, 1),
        'flagged': flagged[:50],
    })


# === AI CONTENT GENERATOR ===

@app.route('/api/generate/cover-letter', methods=['POST'])
def gen_cover_letter():
    """Generate a tailored cover letter."""
    data = request.json
    result = generate_cover_letter(
        resume_text=data.get('resume_text', '') or resume_text or '',
        job_description=data.get('job_description', ''),
        company=data.get('company', ''),
        job_title=data.get('job_title', ''),
        tone=data.get('tone', 'professional'),
    )
    return jsonify(result)


@app.route('/api/generate/cold-message', methods=['POST'])
def gen_cold_message():
    """Generate a cold outreach message."""
    data = request.json
    result = generate_cold_message(
        resume_text=data.get('resume_text', '') or resume_text or '',
        recruiter_name=data.get('recruiter_name', ''),
        job_title=data.get('job_title', ''),
        company=data.get('company', ''),
        platform=data.get('platform', 'linkedin'),
    )
    return jsonify(result)


@app.route('/api/generate/rewrite-bullet', methods=['POST'])
def gen_rewrite_bullet():
    """Rewrite a resume bullet point."""
    data = request.json
    result = rewrite_bullet(
        original_bullet=data.get('bullet', ''),
        target_skill=data.get('target_skill', ''),
        job_context=data.get('job_context', ''),
    )
    return jsonify(result)


@app.route('/api/generate/thank-you', methods=['POST'])
def gen_thank_you():
    """Generate a post-interview thank-you email."""
    data = request.json
    result = generate_thank_you(
        interviewer_name=data.get('interviewer_name', ''),
        job_title=data.get('job_title', ''),
        company=data.get('company', ''),
        discussion_points=data.get('discussion_points', ''),
    )
    return jsonify(result)


# === MARKET INTELLIGENCE ===

@app.route('/api/analytics/market-pulse', methods=['GET'])
def get_market_pulse():
    """Get full market intelligence dashboard data."""
    jobs = job_storage.get_all()
    dupes = job_storage.duplicates_removed
    return jsonify(market_pulse(jobs, dupes))


@app.route('/api/analytics/salary', methods=['GET'])
def get_salary_data():
    """Get salary distribution data."""
    jobs = job_storage.get_all()
    return jsonify(salary_distribution(jobs))


@app.route('/api/analytics/skills', methods=['GET'])
def get_skill_demand():
    """Get skill demand analysis."""
    jobs = job_storage.get_all()
    return jsonify(skill_demand(jobs))


@app.route('/api/analytics/sources', methods=['GET'])
def get_source_quality():
    """Get source quality rankings."""
    jobs = job_storage.get_all()
    return jsonify(source_quality(jobs, job_storage.duplicates_removed))


# ─── Scheduler initialization (runs for both dev & gunicorn) ───

def _scheduled_scrape(keywords, location, sites):
    """Run scrapers for the scheduler (background scheduled scrape)."""
    all_jobs = []
    for kw in keywords:
        for site_id in sites:
            if site_id in SCRAPERS and SCRAPERS[site_id]:
                try:
                    scraper = SCRAPERS[site_id]()
                    jobs = scraper.scrape(kw, location, False)
                    all_jobs.extend(jobs)
                except Exception as e:
                    print(f"[Scheduler] {site_id} error: {e}")
    return all_jobs

scheduler.set_scraper_fn(_scheduled_scrape)
if scheduler.config.get('enabled'):
    scheduler.start()


if __name__ == '__main__':
    print("\U0001f680 Job Scraper Tool Starting...")
    print("\U0001f4cd Open http://localhost:5001 in your browser")
    print("\U0001f4a1 Click 'Start Scraping' to begin searching for jobs")
    app.run(debug=True, host='0.0.0.0', port=5001, threaded=True, use_reloader=False)
