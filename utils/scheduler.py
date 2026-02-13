"""
Job Scheduler — APScheduler-based background scheduling with Gmail email delivery.
Runs scraping at configurable cron times and emails results via Gmail App Password.
"""

import json
import os
import csv
import time
import threading
from datetime import datetime, timedelta

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    APSCHEDULER_AVAILABLE = True
except ImportError:
    BackgroundScheduler = None
    APSCHEDULER_AVAILABLE = False

try:
    from utils.email_service import send_job_report
except ImportError:
    send_job_report = None

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scheduler_config.json')
REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reports')


class JobScheduler:
    def __init__(self):
        self.config = self._load_config()
        if APSCHEDULER_AVAILABLE:
            self.ap_scheduler = BackgroundScheduler(daemon=True)
            self.ap_scheduler.start()
        else:
            self.ap_scheduler = None
            print('⚠️  APScheduler not installed. Scheduling disabled.')
        self.running = False
        self.last_run = None
        self.last_result = None
        self._scraper_fn = None
        self._last_report_path = None

    # ─── Config ────────────────────────────────────────────

    def _load_config(self):
        default = {
            'enabled': False,
            'schedule_time': '08:00',
            'frequency': 'daily',
            'day_of_week': 'monday',
            'keywords': ['ServiceNow', 'ITSM'],
            'location': 'Canada',
            'sites': ['indeed', 'linkedin', 'snpro', 'nelsonfrank'],
            'email': {
                'enabled': True,
                'to': '',
                'sender': '',
                'app_password': '',
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'username': '',
                'password': '',
            },
            'format': 'html',
            'filters': {
                'min_score': 0,
                'work_type': '',
                'max_age_days': 1,
            }
        }
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    saved = json.load(f)
                for k, v in saved.items():
                    if isinstance(v, dict) and isinstance(default.get(k), dict):
                        default[k].update(v)
                    else:
                        default[k] = v
            except Exception:
                pass
        return default

    def _save_config(self):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"[Scheduler] Config save error: {e}")

    def update_config(self, new_config):
        for key, val in new_config.items():
            if key in ('email', 'filters') and isinstance(val, dict) and isinstance(self.config.get(key), dict):
                if key == 'email':
                    for pw_field in ('app_password', 'password'):
                        incoming = val.get(pw_field, None)
                        if incoming == '••••••••':
                            val.pop(pw_field, None)
                self.config[key].update(val)
            else:
                self.config[key] = val
        self._save_config()

        # Re-schedule if running
        if self.running:
            self._schedule_job()

        return self.config

    def get_config(self):
        safe = dict(self.config)
        if 'email' in safe:
            safe['email'] = dict(safe['email'])
            for pw_field in ('app_password', 'password'):
                if safe['email'].get(pw_field):
                    safe['email'][pw_field] = '••••••••'
        safe['last_run'] = self.last_run
        safe['running'] = self.running
        return safe

    # ─── Scheduler control ─────────────────────────────────

    def set_scraper_fn(self, fn):
        self._scraper_fn = fn

    def start(self):
        if self.running:
            return {'status': 'already_running'}
        self.running = True
        self._schedule_job()
        print("[Scheduler] ✅ Scheduler started")
        return {'status': 'started'}

    def stop(self):
        self.running = False
        try:
            if self.ap_scheduler:
                self.ap_scheduler.remove_job('daily_scrape')
        except Exception:
            pass
        print("[Scheduler] Scheduler stopped")
        return {'status': 'stopped'}

    def _schedule_job(self):
        """Register or update the APScheduler cron job."""
        if not self.ap_scheduler:
            print('[Scheduler] \u26a0\ufe0f APScheduler not available. Job not scheduled.')
            return
        try:
            self.ap_scheduler.remove_job('daily_scrape')
        except Exception:
            pass

        target_time = self.config.get('schedule_time', '08:00')
        try:
            hour, minute = map(int, target_time.split(':'))
        except ValueError:
            hour, minute = 8, 0

        freq = self.config.get('frequency', 'daily')
        if freq == 'weekly':
            day = self.config.get('day_of_week', 'monday')[:3].lower()
            self.ap_scheduler.add_job(
                self._execute_scheduled_run, 'cron',
                hour=hour, minute=minute, day_of_week=day,
                id='daily_scrape', replace_existing=True
            )
            print(f"[Scheduler] 📅 Weekly: {day} at {hour:02d}:{minute:02d}")
        else:
            self.ap_scheduler.add_job(
                self._execute_scheduled_run, 'cron',
                hour=hour, minute=minute,
                id='daily_scrape', replace_existing=True
            )
            print(f"[Scheduler] 📅 Daily at {hour:02d}:{minute:02d}")

    def run_now(self):
        """Run a scrape + email cycle immediately."""
        return self._execute_scheduled_run()

    def _execute_scheduled_run(self):
        """Execute one scraping + email cycle."""
        self.last_run = datetime.now().isoformat()
        results = {'jobs_found': 0, 'email_sent': False, 'errors': []}

        try:
            if not self._scraper_fn:
                results['errors'].append('No scraper function registered')
                self.last_result = results
                return results

            print(f"[Scheduler] 🔄 Running scheduled scrape...")
            jobs = self._scraper_fn(
                keywords=self.config.get('keywords', ['ServiceNow']),
                location=self.config.get('location', 'Canada'),
                sites=self.config.get('sites', ['indeed']),
            )

            filtered = self._filter_jobs(jobs)
            results['jobs_found'] = len(filtered)
            print(f"[Scheduler] Found {len(filtered)} jobs after filtering")

            if not filtered:
                results['errors'].append('No jobs matched filters')
                self.last_result = results
                return results

            # Send email
            sent = self._send_email(filtered)
            results['email_sent'] = (sent is True)
            if sent == 'saved':
                results['report_saved'] = True

        except Exception as e:
            results['errors'].append(str(e))
            print(f"[Scheduler] ❌ Error: {e}")

        self.last_result = results
        return results

    def _filter_jobs(self, jobs):
        filters = self.config.get('filters', {})
        min_score = filters.get('min_score', 0)
        work_type = filters.get('work_type', '')
        max_age = filters.get('max_age_days', 1)
        cutoff = datetime.now() - timedelta(days=max_age)

        filtered = []
        for job in jobs:
            if job.get('match_score', 0) < min_score:
                continue
            if work_type and job.get('work_type', '') != work_type:
                continue
            ts = job.get('posted_timestamp', 0)
            if ts and ts > 0:
                try:
                    if datetime.fromtimestamp(ts) < cutoff:
                        continue
                except Exception:
                    pass
            filtered.append(job)
        return filtered

    # ─── Email delivery ────────────────────────────────────

    def _send_email(self, jobs):
        """Send email using email_service. Falls back to saving report."""
        email_cfg = self.config.get('email', {})
        recipient = email_cfg.get('to', '')
        if not recipient:
            print("[Scheduler] No recipient email configured")
            return False

        sender = email_cfg.get('sender', '') or email_cfg.get('username', '') or recipient
        app_pw = email_cfg.get('app_password', '') or email_cfg.get('password', '')

        # Generate attachment if requested
        attachment_path = None
        fmt = self.config.get('format', 'html')
        if fmt in ('csv', 'excel'):
            attachment_path = self._generate_attachment(jobs, fmt)

        if sender and app_pw:
            ok, err = send_job_report(sender, app_pw, recipient, jobs, attachment_path)
            if ok:
                return True
            print(f"[Scheduler] SMTP failed: {err}")

        # Fallback: save report locally
        report_path = self._save_report_html(jobs)
        self._last_report_path = report_path
        print(f"[Scheduler] 📄 Report saved: {report_path}")
        return 'saved'

    def send_test_email(self, jobs):
        """Send test email — used by /api/schedule/test endpoint."""
        return self._send_email(jobs)

    def _generate_attachment(self, jobs, fmt):
        os.makedirs(REPORTS_DIR, exist_ok=True)
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        if fmt == 'csv':
            filepath = os.path.join(REPORTS_DIR, f'jobs_{ts}.csv')
            try:
                keys = ['title', 'company', 'location', 'match_score', 'work_type', 'url', 'source']
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=keys, extrasaction='ignore')
                    writer.writeheader()
                    writer.writerows(jobs)
                return filepath
            except Exception as e:
                print(f"[Scheduler] CSV error: {e}")
        elif fmt == 'excel':
            try:
                from utils.export_utils import export_to_excel
                filepath = os.path.join(REPORTS_DIR, f'jobs_{ts}.xlsx')
                data = export_to_excel(jobs)
                with open(filepath, 'wb') as f:
                    f.write(data)
                return filepath
            except Exception as e:
                print(f"[Scheduler] Excel error: {e}")
        return None

    def _save_report_html(self, jobs):
        os.makedirs(REPORTS_DIR, exist_ok=True)
        filename = f'job_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
        filepath = os.path.join(REPORTS_DIR, filename)
        html = self._build_email_html(jobs)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        return filepath

    def _build_email_html(self, jobs):
        rows = ''
        for job in jobs[:50]:
            title = job.get('title', 'Unknown')
            company = job.get('company', 'Unknown')
            location = job.get('location', '')
            score = job.get('match_score', 0)
            url = job.get('url', '#')
            work_type = job.get('work_type', '')
            source = job.get('source', '')
            color = '#22c55e' if score >= 70 else '#eab308' if score >= 50 else '#ef4444'
            rows += f'''
            <tr style="border-bottom:1px solid #eee;">
                <td style="padding:10px;font-weight:600;">
                    <a href="{url}" style="color:#2563eb;text-decoration:none;">{title}</a>
                </td>
                <td style="padding:10px;">{company}</td>
                <td style="padding:10px;">{location}</td>
                <td style="padding:10px;text-align:center;">
                    <span style="background:{color};color:#fff;padding:2px 8px;border-radius:10px;font-size:13px;">{score}%</span>
                </td>
                <td style="padding:10px;">{work_type}</td>
                <td style="padding:10px;font-size:12px;color:#888;">{source}</td>
            </tr>'''

        kw = ', '.join(self.config.get('keywords', []))
        return f'''
        <html>
        <body style="font-family:Arial,sans-serif;max-width:800px;margin:0 auto;padding:20px;">
            <h2 style="color:#2563eb;">🎯 JobRadar Daily Report</h2>
            <p style="color:#666;">Found <strong>{len(jobs)}</strong> matching jobs for <strong>{kw}</strong></p>
            <table style="width:100%;border-collapse:collapse;margin-top:15px;">
                <thead>
                    <tr style="background:#f8fafc;border-bottom:2px solid #e2e8f0;">
                        <th style="padding:10px;text-align:left;">Title</th>
                        <th style="padding:10px;text-align:left;">Company</th>
                        <th style="padding:10px;text-align:left;">Location</th>
                        <th style="padding:10px;text-align:center;">Score</th>
                        <th style="padding:10px;text-align:left;">Type</th>
                        <th style="padding:10px;text-align:left;">Source</th>
                    </tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
            <p style="margin-top:20px;font-size:12px;color:#999;">
                Generated by JobRadar on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
            </p>
        </body>
        </html>
        '''


# Global scheduler instance
scheduler = JobScheduler()
