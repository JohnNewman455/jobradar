"""
Resume Matcher - Intelligent Scoring System v3
Bidirectional matching: checks resume skills IN job AND job keywords IN resume.
Properly handles ServiceNow ecosystem (ITSM, SAM, ITOM, ITAM, CSM, GRC, etc.)
"""

import re
from difflib import SequenceMatcher


# ============================================================
# SKILL TAXONOMY - ServiceNow & IT ecosystem
# ============================================================
# Each skill has: weight, category, aliases
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
    'cmdb':            {'w': 5, 'cat': 'itsm', 'aliases': ['configuration management']},
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
    
    # === Methodology ===
    'agile':           {'w': 1, 'cat': 'meth', 'aliases': ['agile methodology']},
    'scrum':           {'w': 1, 'cat': 'meth', 'aliases': ['scrum master']},
    'jira':            {'w': 1, 'cat': 'meth', 'aliases': []},
    'git':             {'w': 1, 'cat': 'meth', 'aliases': ['github', 'source control']},
    'sdlc':            {'w': 1, 'cat': 'meth', 'aliases': ['software development lifecycle']},
}

# Title keywords: strong positive signals
TITLE_BOOST = [
    'servicenow', 'service now', 'snow',
    'itsm', 'itom', 'itam', 'sam',
    'platform developer', 'platform admin',
    'system administrator', 'application developer',
]

# Title keywords: negative signals (wrong role)
TITLE_PENALTY = [
    'director', 'vp ', 'vice president', 'chief',
    'sales', 'marketing', 'recruiter',
]


def _text_has_skill(text, skill, aliases):
    """Check if any form of the skill appears in text, using word-boundary aware matching."""
    candidates = [skill] + aliases
    for term in candidates:
        # For very short terms (2-3 chars) like 'csa', 'cad', 'sam', 'spm',
        # use word-boundary regex to avoid false positives
        if len(term) <= 4 and term.isalpha():
            pattern = r'\b' + re.escape(term) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                return True
        else:
            if term in text:
                return True
    return False


def calculate_match_score(job_description, job_title='', resume_text=None):
    """
    Calculate match score (0-100) between resume and job.
    Uses BIDIRECTIONAL matching:
      - Resume skills found in job description (demand match)
      - Job requirements found in resume (supply match)
    
    Returns int 0-100
    """
    if not job_description and not job_title:
        return 0
    
    # Use provided resume or empty string (no default resume to avoid fake scores)
    resume = (resume_text or '').lower()
    desc = (job_description or '').lower()
    title = (job_title or '').lower()
    job_text = f"{title} {desc}"
    
    score = 0.0
    
    # =============================================
    # 1. SKILL OVERLAP (max 65 points)
    # =============================================
    # Bidirectional: skill must be in BOTH resume AND job
    overlap_score = 0.0
    max_possible = 0.0
    matched_skills = []
    
    for skill, info in SKILL_CATALOG.items():
        w = info['w']
        aliases = info['aliases']
        
        in_job = _text_has_skill(job_text, skill, aliases)
        in_resume = _text_has_skill(resume, skill, aliases)
        
        if in_job and in_resume:
            # Both sides match: full weight
            overlap_score += w
            matched_skills.append(skill)
        elif in_job:
            # Job asks for it, resume doesn't have it: count toward max only
            pass
        
        if in_job:
            max_possible += w
    
    # Normalize: what % of the job's required skills does the resume cover?
    # Also factor in absolute breadth — a job with only 2 generic skills
    # shouldn't score 90+ just because you match both.
    if max_possible > 0:
        skill_pct = overlap_score / max_possible
        
        # Breadth factor: how many SN-specific skills were matched?
        sn_categories = {'platform', 'itsm', 'sam', 'itom', 'module', 'dev', 'cert'}
        sn_matched = [s for s in matched_skills if SKILL_CATALOG.get(s, {}).get('cat') in sn_categories]
        
        if len(sn_matched) >= 6:
            breadth_mult = 1.0      # full score
        elif len(sn_matched) >= 3:
            breadth_mult = 0.85     # decent SN overlap
        elif len(sn_matched) >= 1:
            breadth_mult = 0.6      # some SN overlap
        else:
            breadth_mult = 0.35     # only generic skills match
        
        score += skill_pct * breadth_mult * 70  # max 70 pts
    elif resume:
        score += 5
    
    # =============================================
    # 2. TITLE ALIGNMENT (max 15 points)
    # =============================================
    title_score = 0.0
    for kw in TITLE_BOOST:
        if kw in title:
            title_score += 5
    for kw in TITLE_PENALTY:
        if kw in title:
            title_score -= 10
    score += min(max(title_score, 0), 15)
    
    # =============================================
    # 3. CATEGORY DEPTH BONUS (max 15 points)
    # =============================================
    # ServiceNow-specific categories get higher bonus
    matched_cats = set(SKILL_CATALOG[s]['cat'] for s in matched_skills if s in SKILL_CATALOG)
    sn_cats = {'platform', 'itsm', 'sam', 'itom', 'module', 'dev', 'cert'}
    sn_matched = matched_cats & sn_cats
    generic_matched = matched_cats - sn_cats
    cat_bonus = min(len(sn_matched) * 3 + len(generic_matched) * 1, 15)
    score += cat_bonus
    
    # =============================================
    # 4. EXPERIENCE LEVEL (max 5 points)
    # =============================================
    exp_keywords = ['3+ years', '5+ years', '2+ years', 'mid-level', 'senior', 'intermediate']
    for kw in exp_keywords:
        if kw in job_text:
            score += 2.5
            break
    if 'remote' in job_text:
        score += 2.5
    
    return max(0, min(int(round(score)), 100))


def get_match_details(job_description, job_title='', resume_text=None):
    """Get detailed match breakdown."""
    resume = (resume_text or '').lower()
    desc = (job_description or '').lower()
    title = (job_title or '').lower()
    job_text = f"{title} {desc}"
    
    matched = []
    missing_in_resume = []
    
    for skill, info in SKILL_CATALOG.items():
        aliases = info['aliases']
        in_job = _text_has_skill(job_text, skill, aliases)
        in_resume = _text_has_skill(resume, skill, aliases)
        
        if in_job and in_resume:
            matched.append(skill)
        elif in_job and not in_resume:
            missing_in_resume.append(skill)
    
    score = calculate_match_score(job_description, job_title, resume_text)
    
    if score >= 80:
        rec = "Excellent match — Apply immediately!"
    elif score >= 60:
        rec = "Strong match — Worth applying"
    elif score >= 40:
        rec = "Decent match — Review carefully"
    elif score >= 20:
        rec = "Partial match — Some overlap"
    else:
        rec = "Low match — May not be relevant"
    
    return {
        'score': score,
        'matched_skills': matched,
        'missing_skills': missing_in_resume,
        'recommendation': rec
    }
