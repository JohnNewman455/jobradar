"""Text processing utilities for job data"""
import re
from datetime import datetime, timezone
from html.parser import HTMLParser


class HTMLStripper(HTMLParser):
    """Strip HTML tags from text"""
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = []
    
    def handle_data(self, data):
        self.text.append(data)
    
    def get_text(self):
        return ''.join(self.text)


def strip_html(html_text):
    """Remove HTML tags and return plain text"""
    if not html_text:
        return ""
    
    stripper = HTMLStripper()
    stripper.feed(str(html_text))
    text = stripper.get_text()
    
    # Clean up extra whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text


def truncate_text(text, max_length=200):
    """Truncate text to max_length characters"""
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length] + "..."


def get_time_ago(timestamp):
    """Convert timestamp to relative time (e.g., '2 hours ago')"""
    if not timestamp:
        return "Unknown"
    
    try:
        # Parse various timestamp formats
        if isinstance(timestamp, str):
            # Try ISO format first
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                # Try other common formats
                for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S']:
                    try:
                        dt = datetime.strptime(timestamp, fmt)
                        break
                    except:
                        continue
                else:
                    return timestamp  # Return original if can't parse
        else:
            dt = timestamp
        
        # Ensure timezone awareness
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        
        now = datetime.now(timezone.utc)
        diff = now - dt
        
        seconds = diff.total_seconds()
        
        if seconds < 0:
            return "Just now"
        elif seconds < 60:
            return "Just now"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif seconds < 604800:
            days = int(seconds / 86400)
            return f"{days} day{'s' if days != 1 else ''} ago"
        elif seconds < 2592000:
            weeks = int(seconds / 604800)
            return f"{weeks} week{'s' if weeks != 1 else ''} ago"
        else:
            months = int(seconds / 2592000)
            return f"{months} month{'s' if months != 1 else ''} ago"
            
    except Exception as e:
        print(f"Error parsing timestamp: {e}")
        return str(timestamp)


def is_job_relevant(job, search_keywords):
    """Check if job is relevant to search keywords - RELAXED to show jobs with ServiceNow mentioned"""
    if not search_keywords:
        return True
    
    keywords = [k.lower().strip() for k in search_keywords.split()]
    if not keywords:
        return True
    
    # Get the main keyword (usually the technology/platform name like "ServiceNow")
    main_keyword = max(keywords, key=len) if keywords else keywords[0]
    
    # Combine title and description for searching
    title = str(job.get('title', '') or '').lower()
    description = strip_html(str(job.get('description', '') or '')).lower()
    company = str(job.get('company', '') or '').lower()
    tags = ' '.join([str(tag).lower() for tag in job.get('tags', [])])
    
    searchable_text = f"{title} {description} {company} {tags}"
    
    # RELAXED: Main keyword MUST be present ANYWHERE (title OR description)
    # This ensures "ServiceNow" jobs are shown even if title is "Senior Developer"
    if main_keyword in searchable_text:
        return True
    
    return False  # Only filter if main keyword completely missing


def calculate_relevance_score(job, search_keywords):
    """Calculate relevance score (0-100) based on keyword matches - RELAXED scoring"""
    if not search_keywords:
        return 50  # Default score
    
    keywords = [k.lower().strip() for k in search_keywords.split()]
    if not keywords:
        return 50
    
    score = 0
    title = str(job.get('title', '') or '').lower()
    description = strip_html(str(job.get('description', '') or '')).lower()
    
    # Get main keyword
    main_keyword = max(keywords, key=len) if keywords else keywords[0]
    
    # If main keyword in title, high score
    if main_keyword in title:
        score += 50
    # If main keyword only in description, still good score
    elif main_keyword in description:
        score += 30
    
    # Bonus for other keywords
    for keyword in keywords:
        if keyword != main_keyword:
            if keyword in title:
                score += 15
            elif keyword in description:
                score += 5
    
    return min(score, 100)


def detect_work_type(location, description, is_remote):
    """Detect if job is Remote, Hybrid, or On-site with comprehensive pattern matching"""
    location_lower = (location or '').lower()
    desc_lower = (description or '').lower()
    combined = f"{location_lower} {desc_lower}"

    # Hybrid patterns - check BEFORE remote since hybrid jobs often mention "remote" too
    hybrid_patterns = [
        'hybrid', 'mix of remote', 'mix of in-office', 'mix of onsite',
        'days in office', 'days on-site', 'days on site', 'days onsite',
        'partially remote', 'part remote', 'flexible work arrangement',
        'in-office and remote', 'onsite and remote', 'remote and onsite',
        'onsite/remote', 'remote/onsite', 'on-site/remote', 'remote/on-site',
        'combination of remote', 'blend of remote', 'work model hybrid',
        'work model: hybrid', 'flexible work model', 'flexible location',
        'some days in office', 'office and home', 'home and office',
        '2 days', '3 days', '4 days',  # "2 days in office" etc.
    ]
    for pattern in hybrid_patterns:
        if pattern in combined:
            return 'Hybrid'

    # Remote patterns
    remote_patterns = [
        'remote', 'work from home', 'wfh', 'work anywhere',
        'fully remote', '100% remote', 'distributed', 'telecommute',
        'telework', 'virtual position', 'work from anywhere',
    ]
    if is_remote:
        return 'Remote'
    for pattern in remote_patterns:
        if pattern in combined:
            return 'Remote'

    # Default to on-site
    return 'On-site'
