"""
Resume Matcher - Intelligent Scoring System v4
Five-pillar approach: Platform Affinity + Demand Match + Supply Richness + Title + Experience
Handles ServiceNow ecosystem (ITSM, SAM, ITOM, ITAM, CSM, GRC, etc.)
"""

import re


# ============================================================
# SKILL TAXONOMY - ServiceNow & IT ecosystem
# ============================================================
SKILL_CATALOG = {
    # === ServiceNow Platform (core) ===
    'servicenow':      {'w': 12, 'cat': 'platform', 'aliases': ['service now', 'snow', 'service-now']},

    # === ITSM ===
    'itsm':            {'w': 10, 'cat': 'itsm', 'aliases': ['it service management']},
    'incident management': {'w': 6, 'cat': 'itsm', 'aliases': ['incident mgmt']},
    'problem management':  {'w': 6, 'cat': 'itsm', 'aliases': ['problem mgmt']},
    'change management':   {'w': 6, 'cat': 'itsm', 'aliases': ['change mgmt', 'change request']},
    'service catalog':     {'w': 6, 'cat': 'itsm', 'aliases': ['catalog item', 'catalog items', 'record producer']},
    'knowledge management': {'w': 4, 'cat': 'itsm', 'aliases': ['knowledge base', 'knowledge article']},
    'sla':             {'w': 5, 'cat': 'itsm', 'aliases': ['service level agreement', 'service level']},
    'cmdb':            {'w': 5, 'cat': 'itsm', 'aliases': ['configuration management database']},
    'request management': {'w': 4, 'cat': 'itsm', 'aliases': ['request fulfillment']},

    # === SAM / ITAM ===
    'sam':             {'w': 10, 'cat': 'sam', 'aliases': ['software asset management']},
    'sam pro':         {'w': 10, 'cat': 'sam', 'aliases': ['sam-pro', 'sampro']},
    'itam':            {'w': 9, 'cat': 'sam', 'aliases': ['it asset management', 'asset management']},
    'software asset':  {'w': 7, 'cat': 'sam', 'aliases': ['software model', 'software entitlement']},
    'license compliance': {'w': 6, 'cat': 'sam', 'aliases': ['license tracking', 'license management', 'entitlement']},
    'data normalization': {'w': 5, 'cat': 'sam', 'aliases': ['data reconciliation', 'normalization']},
    'reclamation':     {'w': 4, 'cat': 'sam', 'aliases': ['software reclamation']},

    # === ITOM ===
    'itom':            {'w': 8, 'cat': 'itom', 'aliases': ['it operations management']},
    'discovery':       {'w': 5, 'cat': 'itom', 'aliases': ['servicenow discovery']},
    'event management': {'w': 5, 'cat': 'itom', 'aliases': []},
    'orchestration':   {'w': 5, 'cat': 'itom', 'aliases': []},
    'service mapping':  {'w': 5, 'cat': 'itom', 'aliases': []},

    # === Other SN modules ===
    'csm':             {'w': 7, 'cat': 'module', 'aliases': ['customer service management']},
    'hr service delivery': {'w': 6, 'cat': 'module', 'aliases': ['hrsd']},
    'grc':             {'w': 6, 'cat': 'module', 'aliases': ['governance risk compliance']},
    'spm':             {'w': 5, 'cat': 'module', 'aliases': ['strategic portfolio management']},
    'secops':          {'w': 5, 'cat': 'module', 'aliases': ['security operations']},
    'service portal':  {'w': 5, 'cat': 'module', 'aliases': ['sp', 'employee center']},
    'performance analytics': {'w': 4, 'cat': 'module', 'aliases': ['pa']},
    'flow designer':   {'w': 6, 'cat': 'module', 'aliases': ['flow', 'subflow']},
    'integration hub':  {'w': 5, 'cat': 'module', 'aliases': ['integrathub']},
    'atf':             {'w': 3, 'cat': 'module', 'aliases': ['automated test framework']},

    # === SN Development ===
    'gliderecord':     {'w': 7, 'cat': 'dev', 'aliases': ['glide record', 'glide api', 'glidesystem', 'glide']},
    'script include':  {'w': 6, 'cat': 'dev', 'aliases': ['script includes', 'scriptinclude']},
    'business rule':   {'w': 6, 'cat': 'dev', 'aliases': ['business rules']},
    'client script':   {'w': 6, 'cat': 'dev', 'aliases': ['client scripts']},
    'ui policy':       {'w': 5, 'cat': 'dev', 'aliases': ['ui policies']},
    'ui action':       {'w': 5, 'cat': 'dev', 'aliases': ['ui actions']},
    'acl':             {'w': 5, 'cat': 'dev', 'aliases': ['access control', 'acls']},
    'update set':      {'w': 4, 'cat': 'dev', 'aliases': ['update sets']},
    'import set':      {'w': 4, 'cat': 'dev', 'aliases': ['import sets', 'transform map', 'transform maps']},
    'scheduled job':   {'w': 3, 'cat': 'dev', 'aliases': ['scheduled jobs']},
    'notification':    {'w': 3, 'cat': 'dev', 'aliases': ['email notification', 'email notifications']},
    'report':          {'w': 3, 'cat': 'dev', 'aliases': ['reports', 'dashboard', 'dashboards']},

    # === Certifications ===
    'csa':             {'w': 7, 'cat': 'cert', 'aliases': ['certified system administrator']},
    'cad':             {'w': 7, 'cat': 'cert', 'aliases': ['certified application developer']},
    'cis':             {'w': 6, 'cat': 'cert', 'aliases': ['certified implementation specialist']},
    'itil':            {'w': 5, 'cat': 'cert', 'aliases': ['itil v3', 'itil v4', 'itil foundation']},

    # === Programming ===
    'javascript':      {'w': 5, 'cat': 'lang', 'aliases': ['js', 'ecmascript']},
    'rest api':        {'w': 4, 'cat': 'lang', 'aliases': ['rest', 'restful', 'rest apis']},
    'soap':            {'w': 2, 'cat': 'lang', 'aliases': ['soap api']},
    'html':            {'w': 1, 'cat': 'lang', 'aliases': ['html5']},
    'css':             {'w': 1, 'cat': 'lang', 'aliases': ['css3']},
    'json':            {'w': 1, 'cat': 'lang', 'aliases': []},
    'xml':             {'w': 1, 'cat': 'lang', 'aliases': []},
    'sql':             {'w': 1, 'cat': 'lang', 'aliases': ['mysql', 'postgresql']},
    'angularjs':       {'w': 2, 'cat': 'lang', 'aliases': ['angular']},
    'python':          {'w': 2, 'cat': 'lang', 'aliases': []},
    'powershell':      {'w': 2, 'cat': 'lang', 'aliases': []},

    # === Methodology ===
    'agile':           {'w': 1, 'cat': 'meth', 'aliases': ['agile methodology']},
    'scrum':           {'w': 1, 'cat': 'meth', 'aliases': ['scrum master']},
    'jira':            {'w': 1, 'cat': 'meth', 'aliases': []},
    'git':             {'w': 1, 'cat': 'meth', 'aliases': ['github', 'source control']},
    'sdlc':            {'w': 1, 'cat': 'meth', 'aliases': ['software development lifecycle']},
}

TITLE_BOOST = [
    'servicenow', 'service now', 'snow',
    'itsm', 'itom', 'itam', 'sam',
    'platform developer', 'platform admin',
    'system administrator', 'application developer',
]

TITLE_PENALTY = [
    'director', 'vp ', 'vice president', 'chief',
    'sales', 'marketing', 'recruiter',
]

SN_CATEGORIES = {'platform', 'itsm', 'sam', 'itom', 'module', 'dev', 'cert'}


def _text_has_skill(text, skill, aliases):
    """Check if any form of the skill appears in text."""
    candidates = [skill] + aliases
    for term in candidates:
        if len(term) <= 4 and term.isalpha():
            pattern = r'\b' + re.escape(term) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                return True
        else:
            if term in text:
                return True
    return False


def _extract_skills(text):
    """Extract all catalog skills found in text. Returns dict of skill->info."""
    found = {}
    for skill, info in SKILL_CATALOG.items():
        if _text_has_skill(text, skill, info['aliases']):
            found[skill] = info
    return found


def calculate_match_score(job_description, job_title='', resume_text=None):
    """
    Calculate match score (0-100) between resume and job.

    Five pillars:
      1. Platform Affinity  (max 20) - Both mention ServiceNow? Same domain?
      2. Skill Demand Match  (max 35) - % of job-required skills in resume
      3. Resume Richness     (max 20) - How deep is resume's SN expertise?
      4. Title Alignment     (max 15) - Job title signals
      5. Experience Signal   (max 10) - Experience level + overlap count bonus

    Returns int 0-100
    """
    if not job_description and not job_title:
        return 0

    resume = (resume_text or '').lower()
    if not resume:
        return 0

    desc = (job_description or '').lower()
    title = (job_title or '').lower()
    job_text = f"{title} {desc}"

    resume_skills = _extract_skills(resume)
    job_skills = _extract_skills(job_text)
    overlap = set(resume_skills.keys()) & set(job_skills.keys())

    resume_cats = set(info['cat'] for info in resume_skills.values())
    job_cats = set(info['cat'] for info in job_skills.values())
    resume_sn_skills = [s for s, i in resume_skills.items() if i['cat'] in SN_CATEGORIES]

    # === 1. PLATFORM AFFINITY (max 20) ===
    sn_in_resume = 'servicenow' in resume_skills
    sn_in_job = 'servicenow' in job_skills

    platform_score = 0.0
    if sn_in_resume and sn_in_job:
        platform_score = 12
        sn_cat_overlap = (resume_cats & job_cats) & SN_CATEGORIES
        platform_score += min(len(sn_cat_overlap) * 2.5, 8)
    elif sn_in_resume or sn_in_job:
        platform_score = 5

    # === 2. SKILL DEMAND MATCH (max 35) ===
    demand_score = 0.0
    if job_skills:
        overlap_weight = sum(SKILL_CATALOG[s]['w'] for s in overlap)
        total_job_weight = sum(i['w'] for i in job_skills.values())
        if total_job_weight > 0:
            demand_score = (overlap_weight / total_job_weight) * 35

    # === 3. RESUME RICHNESS (max 20) ===
    richness_score = min(len(resume_sn_skills) * 2.5, 20)

    # === 4. TITLE ALIGNMENT (max 15) ===
    title_score = 0.0
    for kw in TITLE_BOOST:
        if kw in title:
            title_score += 5
    for kw in TITLE_PENALTY:
        if kw in title:
            title_score -= 10
    title_score = min(max(title_score, 0), 15)

    # === 5. EXPERIENCE SIGNAL (max 10) ===
    exp_score = 0.0
    for kw in ['3+ years', '5+ years', '2+ years', 'years experience',
               'mid-level', 'senior', 'intermediate']:
        if kw in job_text:
            exp_score += 2
            break
    if 'remote' in job_text:
        exp_score += 1
    if len(overlap) >= 8:
        exp_score += 7
    elif len(overlap) >= 5:
        exp_score += 5
    elif len(overlap) >= 3:
        exp_score += 3
    elif len(overlap) >= 1:
        exp_score += 1
    exp_score = min(exp_score, 10)

    total = platform_score + demand_score + richness_score + title_score + exp_score
    return max(0, min(int(round(total)), 100))


def get_match_details(job_description, job_title='', resume_text=None):
    """Get detailed match breakdown for the optimizer."""
    resume = (resume_text or '').lower()
    job_text = f"{(job_title or '').lower()} {(job_description or '').lower()}"

    resume_skills = _extract_skills(resume)
    job_skills = _extract_skills(job_text)

    matched = sorted(set(resume_skills.keys()) & set(job_skills.keys()))
    missing = sorted(set(job_skills.keys()) - set(resume_skills.keys()))
    extra = sorted(set(resume_skills.keys()) - set(job_skills.keys()))

    score = calculate_match_score(job_description, job_title, resume_text)

    if score >= 80:
        rec = "Excellent match - Apply immediately!"
    elif score >= 60:
        rec = "Strong match - Worth applying"
    elif score >= 40:
        rec = "Decent match - Review carefully"
    elif score >= 20:
        rec = "Partial match - Some overlap"
    else:
        rec = "Low match - May not be relevant"

    return {
        'score': score,
        'matched_skills': matched,
        'missing_skills': missing,
        'extra_skills': extra,
        'recommendation': rec,
    }
