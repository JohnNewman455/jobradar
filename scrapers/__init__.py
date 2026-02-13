# Scrapers package
try:
    from .base_scraper import BaseScraper
except ImportError:
    BaseScraper = None

# Working scrapers
try:
    from .remoteok_scraper import RemoteOKScraper
except ImportError:
    RemoteOKScraper = None

try:
    from .weworkremotely_scraper import WeWorkRemotelyScraper
except ImportError:
    WeWorkRemotelyScraper = None

try:
    from .servicenow_careers_scraper import ServiceNowCareersScraper
except ImportError:
    ServiceNowCareersScraper = None

# JobSpy scrapers (replacements for Indeed, LinkedIn, etc.)
try:
    from .jobspy_scraper import (
        JobSpyIndeedScraper,
        JobSpyLinkedInScraper,
        JobSpyZipRecruiterScraper,
        JobSpyGlassdoorScraper,
        JobSpyAllScraper
    )
except ImportError:
    JobSpyIndeedScraper = None
    JobSpyLinkedInScraper = None
    JobSpyZipRecruiterScraper = None
    JobSpyGlassdoorScraper = None
    JobSpyAllScraper = None

# Optional scrapers (may need curl_cffi or other deps)
try:
    from .indeed_scraper import IndeedScraper
except ImportError:
    IndeedScraper = None

try:
    from .glassdoor_scraper import GlassdoorScraper
except ImportError:
    GlassdoorScraper = None

try:
    from .google_jobs_scraper import GoogleJobsScraper
except ImportError:
    GoogleJobsScraper = None

try:
    from .dice_scraper import DiceScraper
except ImportError:
    DiceScraper = None

try:
    from .talent_com_scraper import TalentComScraper
except ImportError:
    TalentComScraper = None

try:
    from .jooble_scraper import JoobleScraper
except ImportError:
    JoobleScraper = None

try:
    from .wellfound_scraper import WellfoundScraper
except ImportError:
    WellfoundScraper = None

try:
    from .simplyhired_ca_scraper import SimplyHiredCAScraper
except ImportError:
    SimplyHiredCAScraper = None

__all__ = [
    'BaseScraper',
    'IndeedScraper',
    'RemoteOKScraper',
    'WeWorkRemotelyScraper',
    'GlassdoorScraper',
    'GoogleJobsScraper',
    'DiceScraper',
    'TalentComScraper',
    'JoobleScraper',
    'ServiceNowCareersScraper',
    'WellfoundScraper',
    'SimplyHiredCAScraper'
]
