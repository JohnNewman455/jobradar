"""
Email Service — Gmail App Password SMTP delivery.
Works reliably with Gmail + App Password (16 chars).
Also supports Outlook, Yahoo, iCloud SMTP.
"""

import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime


# Auto-detect SMTP settings from email domain
SMTP_PROVIDERS = {
    'gmail.com':      ('smtp.gmail.com', 587),
    'googlemail.com': ('smtp.gmail.com', 587),
    'outlook.com':    ('smtp-mail.outlook.com', 587),
    'hotmail.com':    ('smtp-mail.outlook.com', 587),
    'live.com':       ('smtp-mail.outlook.com', 587),
    'yahoo.com':      ('smtp.mail.yahoo.com', 587),
    'yahoo.ca':       ('smtp.mail.yahoo.com', 587),
    'aol.com':        ('smtp.aol.com', 587),
    'icloud.com':     ('smtp.mail.me.com', 587),
    'me.com':         ('smtp.mail.me.com', 587),
}


def send_job_report(sender_email, app_password, recipient_email, jobs, attachment_path=None):
    """
    Send HTML job report email with optional CSV/Excel attachment.
    
    Args:
        sender_email: Gmail (or other) address
        app_password: App Password (16 chars for Gmail) or regular password
        recipient_email: Where to send the report
        jobs: List of job dicts
        attachment_path: Optional file path to attach (CSV or Excel)
    
    Returns:
        (True, None) on success, (False, error_string) on failure
    """
    if not sender_email or not app_password:
        return False, "Sender email and App Password are required"
    if not recipient_email:
        return False, "Recipient email is required"

    # Build email
    msg = MIMEMultipart('alternative')
    msg['From'] = f"JobRadar <{sender_email}>"
    msg['To'] = recipient_email
    msg['Subject'] = f"JobRadar: {len(jobs)} New Jobs Found — {datetime.now().strftime('%b %d, %Y')}"

    # HTML body
    html_body = _build_html(jobs)
    msg.attach(MIMEText(html_body, 'html'))

    # Attach file if provided
    if attachment_path and os.path.exists(attachment_path):
        try:
            with open(attachment_path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(attachment_path)}"')
            msg.attach(part)
        except Exception as e:
            print(f"[Email] Attachment error: {e}")

    # Detect SMTP server from domain
    domain = sender_email.split('@')[-1].lower()
    smtp_server, smtp_port = SMTP_PROVIDERS.get(domain, ('smtp.gmail.com', 587))

    # Send
    try:
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(sender_email, app_password)
        server.send_message(msg)
        server.quit()
        print(f"[Email] ✅ Sent to {recipient_email} via {smtp_server}")
        return True, None
    except smtplib.SMTPAuthenticationError as e:
        err = f"Login failed — check your App Password. ({e.smtp_code}: {e.smtp_error})"
        print(f"[Email] ❌ {err}")
        return False, err
    except Exception as e:
        err = str(e)[:200]
        print(f"[Email] ❌ {err}")
        return False, err


def _build_html(jobs):
    """Build clean HTML email body."""
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

    return f'''
    <html>
    <body style="font-family:Arial,sans-serif;max-width:800px;margin:0 auto;padding:20px;">
        <h2 style="color:#2563eb;">🎯 JobRadar Daily Report</h2>
        <p style="color:#666;">Found <strong>{len(jobs)}</strong> matching jobs</p>
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
