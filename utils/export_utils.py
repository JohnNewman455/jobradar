"""
Export utilities for job data
"""

try:
    import pandas as pd
except ImportError:
    pd = None

from io import BytesIO, StringIO
from typing import List, Dict


def export_to_csv(jobs: List[Dict]) -> str:
    """Export jobs to CSV format"""
    if not jobs:
        return "No jobs to export"
    
    if pd:
        df = pd.DataFrame(jobs)
        columns_order = [
            'title', 'company', 'location', 'salary', 
            'job_type', 'remote', 'url', 'description',
            'posted_date', 'source', 'scraped_at'
        ]
        columns_order = [col for col in columns_order if col in df.columns]
        df = df[columns_order]
        return df.to_csv(index=False)
    else:
        # Fallback: stdlib csv
        import csv as _csv
        columns_order = [
            'title', 'company', 'location', 'salary',
            'job_type', 'remote', 'url', 'description',
            'posted_date', 'source', 'scraped_at'
        ]
        columns_order = [col for col in columns_order if col in jobs[0]]
        output = StringIO()
        writer = _csv.DictWriter(output, fieldnames=columns_order, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(jobs)
        return output.getvalue()


def export_to_excel(jobs: List[Dict]) -> bytes:
    """Export jobs to Excel format"""
    if not jobs:
        return b""
    
    if not pd:
        # Fallback: return CSV bytes if pandas not available
        return export_to_csv(jobs).encode('utf-8')
    
    df = pd.DataFrame(jobs)
    columns_order = [
        'title', 'company', 'location', 'salary',
        'job_type', 'remote', 'url', 'description',
        'posted_date', 'source', 'scraped_at'
    ]
    columns_order = [col for col in columns_order if col in df.columns]
    df = df[columns_order]
    
    output = BytesIO()
    try:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Jobs')
            worksheet = writer.sheets['Jobs']
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).apply(len).max(),
                    len(col)
                )
                worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 50)
    except Exception:
        # openpyxl not available, return CSV bytes
        return export_to_csv(jobs).encode('utf-8')
    
    output.seek(0)
    return output.getvalue()


def export_to_csv_file(jobs, filepath):
    """Save jobs to a CSV file on disk."""
    import csv
    if not jobs:
        return filepath
    keys = ['title', 'company', 'location', 'match_score', 'work_type', 'url', 'source', 'posted_date']
    keys = [k for k in keys if any(k in j for j in jobs)]
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(jobs)
    return filepath


def export_to_json(jobs: List[Dict]) -> str:
    """Export jobs to JSON format"""
    import json
    return json.dumps(jobs, indent=2)


def generate_summary_stats(jobs: List[Dict]) -> Dict:
    """Generate summary statistics from jobs"""
    if pd:
        df = pd.DataFrame(jobs)
        stats = {
            'total_jobs': len(df),
            'unique_companies': df['company'].nunique() if 'company' in df else 0,
            'remote_jobs': df['remote'].sum() if 'remote' in df else 0,
            'jobs_by_site': df.groupby('source').size().to_dict() if 'source' in df else {},
            'jobs_by_location': df.groupby('location').size().head(10).to_dict() if 'location' in df else {}
        }
    else:
        from collections import Counter
        stats = {
            'total_jobs': len(jobs),
            'unique_companies': len(set(j.get('company', '') for j in jobs)),
            'remote_jobs': sum(1 for j in jobs if j.get('remote')),
            'jobs_by_site': dict(Counter(j.get('source', '') for j in jobs)),
            'jobs_by_location': dict(Counter(j.get('location', '') for j in jobs).most_common(10))
        }
    return stats
