"""
Resume Optimizer v2 — Commercial-grade ATS analysis & improvement engine.
Produces section-by-section scores, copy-paste ready text, before/after bullet
rewrites, keyword-density comparison, and ATS formatting checks.
"""

import re, math
from utils.scorer import SKILL_CATALOG, _text_has_skill, _extract_skills, calculate_match_score

# ── soft / power keywords ────────────────────────────────────────────
POWER_KEYWORDS = [
    'leadership', 'collaboration', 'communication', 'problem solving',
    'analytical', 'strategic', 'mentoring', 'stakeholder management',
    'cross-functional', 'process improvement', 'project management',
    'team lead', 'change management', 'vendor management',
    'time management', 'critical thinking', 'negotiation',
    'continuous improvement', 'agile', 'customer focus',
    'adaptability', 'innovation', 'attention to detail',
    'documentation', 'training', 'knowledge transfer',
    'presentation', 'facilitation', 'conflict resolution',
    'decision making', 'accountability',
]

CAT_LABELS = {
    'platform': 'Platform & Core', 'itsm': 'ITSM', 'sam': 'SAM / ITAM',
    'itom': 'ITOM / Discovery', 'module': 'Modules', 'dev': 'Development',
    'cert': 'Certifications', 'lang': 'Languages & APIs', 'meth': 'Methodology',
}

EXTRA_KEYWORDS = [
    'leadership', 'team lead', 'mentoring', 'stakeholder',
    'communication', 'documentation', 'process improvement',
    'project management', 'pmp', 'prince2',
    'digital transformation', 'automation', 'optimization',
    'enterprise', 'scalable', 'mission-critical',
    'sla monitoring', 'root cause analysis', 'rca',
    'vendor management', 'third party',
    'compliance', 'audit', 'security',
    'cloud', 'azure', 'aws', 'gcp',
    'devops', 'ci/cd', 'pipeline',
    'cross-functional', 'collaboration',
    'training', 'onboarding', 'knowledge transfer',
    'upgrade', 'migration', 'implementation',
    'best practices', 'framework',
    'customer satisfaction', 'user experience',
]


# ── helpers ───────────────────────────────────────────────────────────

def _extract_extra_keywords(text):
    found = set()
    tl = text.lower()
    for kw in EXTRA_KEYWORDS:
        if kw in tl:
            found.add(kw)
    return found


def _count_occurrences(text, term):
    return len(re.findall(r'\b' + re.escape(term) + r'\b', text, re.I))


def _role_hint(job_text):
    jl = job_text.lower()
    for h in ['developer', 'administrator', 'analyst', 'architect',
              'consultant', 'engineer', 'manager', 'specialist']:
        if h in jl:
            return h.title()
    return 'Professional'


def _platform_hint(matched):
    return 'ServiceNow' if any('servicenow' in s for s in matched) else 'IT'


# ── section scores ────────────────────────────────────────────────────

def _compute_section_scores(resume, job, matched, missing, resume_kw, job_kw):
    total_hard = len(matched) + len(missing)
    hard = int((len(matched) / max(total_hard, 1)) * 100)

    # soft skills
    r_soft = {k for k in POWER_KEYWORDS if k in resume.lower()}
    j_soft = {k for k in POWER_KEYWORDS if k in job.lower()}
    soft = int((len(r_soft & j_soft) / max(len(j_soft), 1)) * 100) if j_soft else 70

    # experience heuristic: bullet density
    bullets = len(re.findall(r'(?m)^[\s]*[-•*]', resume))
    exp = min(100, 40 + bullets * 5)  # more bullets = higher

    # formatting checks
    fmt_score = 60
    if re.search(r'\b[A-Z][a-z]+@', resume): fmt_score += 10  # email
    if re.search(r'linkedin', resume, re.I): fmt_score += 10
    if len(resume.split()) >= 300: fmt_score += 10
    if bullets >= 6: fmt_score += 10
    fmt_score = min(fmt_score, 100)

    # summary check
    has_summary = bool(re.search(r'(?i)(summary|objective|profile|about)', resume[:500]))
    summary = 70 if has_summary else 30

    return {
        'hard_skills': hard,
        'soft_skills': soft,
        'experience': exp,
        'formatting': fmt_score,
        'summary': summary,
    }


# ── professional summary ─────────────────────────────────────────────

def _summary_suggestions(matched, missing, job_text, resume_text):
    role = _role_hint(job_text)
    plat = _platform_hint(matched)
    top_m = [s.replace('_', ' ').title() for s in sorted(matched, key=lambda s: SKILL_CATALOG.get(s, {}).get('w', 0), reverse=True)[:6]]
    top_miss = [s.replace('_', ' ').title() for s in sorted(missing, key=lambda s: SKILL_CATALOG.get(s, {}).get('w', 0), reverse=True)[:4]]
    m_str = ', '.join(top_m) if top_m else 'various IT skills'
    gap_str = ', '.join(top_miss[:3])

    # current assessment
    assessment = []
    first_500 = resume_text[:500].lower()
    if not re.search(r'(summary|profile|objective|about)', first_500):
        assessment.append('No professional summary detected at the top of your resume.')
    elif len(first_500.split('.')[0].split()) < 15:
        assessment.append('Summary appears too short — aim for 3-4 lines.')
    else:
        assessment.append('Summary detected — review keyword coverage below.')

    if not any(s.replace('_', ' ') in first_500 for s in matched[:3]):
        assessment.append('Top skills are missing from your summary. ATS scans summary first.')

    options = []
    # Option 1: Conservative
    options.append({
        'label': 'Option 1: Conservative',
        'text': f"Experienced {plat} {role} with proven expertise in {m_str}. Skilled in delivering enterprise-grade solutions that drive operational efficiency and digital transformation.",
        'tips': ['Best if you already have most required skills.', 'Safe for direct applications.'],
        'recommended': False,
    })
    # Option 2: ATS-Optimised (weave missing)
    if gap_str:
        all_str = ', '.join(top_m[:4] + top_miss[:2])
        options.append({
            'label': 'Option 2: ATS-Optimised (Recommended)',
            'text': f"Results-driven {plat} {role} with deep expertise spanning {all_str}. Passionate about leveraging platform capabilities to streamline processes, improve service delivery, and support business objectives.",
            'tips': ['Weaves missing keywords into summary to boost ATS match.', 'Best for roles where you meet 60%+ of requirements.'],
            'recommended': True,
        })
    else:
        options.append({
            'label': 'Option 2: Impact-Focused (Recommended)',
            'text': f"Results-driven {plat} {role} with extensive hands-on experience in {m_str}. Track record of delivering scalable solutions, optimizing workflows, and ensuring alignment with organizational goals.",
            'tips': ['Strong self-sufficient summary.', 'Highlights impact over listing.'],
            'recommended': True,
        })
    # Option 3: Metrics-heavy
    options.append({
        'label': 'Option 3: Metrics-Heavy',
        'text': f"Detail-oriented {plat} {role} with [X]+ years of experience in {m_str}. Known for reducing incident resolution times by [X]%, improving process automation coverage, and maintaining [X]% platform uptime.",
        'tips': ['Replace [X] with real numbers.', 'Best if you have quantifiable achievements.'],
        'recommended': False,
    })

    return {'current_assessment': assessment, 'options': options}


# ── hard skills ───────────────────────────────────────────────────────

def _hard_skills_suggestions(matched, missing, extra):
    categories = {}
    for skill in list(matched) + list(missing):
        cat = SKILL_CATALOG.get(skill, {}).get('cat', 'other')
        label = CAT_LABELS.get(cat, 'Other')
        w = SKILL_CATALOG.get(skill, {}).get('w', 0)
        categories.setdefault(label, []).append({
            'skill': skill.replace('_', ' ').title(),
            'status': 'matched' if skill in matched else 'missing',
            'priority': 'high' if w >= 6 else 'medium' if w >= 4 else 'low',
            'action': 'Keep visible' if skill in matched else f"Add — ATS weight {w}/10",
        })

    # Build copy-paste text
    lines = ['Technical Skills']
    for cat_label, items in sorted(categories.items()):
        skills_str = ' | '.join(i['skill'] for i in items)
        lines.append(f"  {cat_label}: {skills_str}")
    copy_paste = '\n'.join(lines)

    return {
        'categories': categories,
        'copy_paste_section': copy_paste,
        'matched_count': len(matched),
        'missing_count': len(missing),
    }


# ── work experience ──────────────────────────────────────────────────

def _experience_suggestions(missing, job_text):
    bullet_templates = {
        'itsm': ("Managed incident queue with 50+ tickets weekly",
                 "Managed {skill} processes within ServiceNow, handling [X]+ tickets monthly and maintaining [X]% SLA compliance"),
        'sam': ("Tracked software licenses",
                "Administered {skill} module, tracking [X]+ software assets and identifying $[X]K in license optimisation savings"),
        'itom': ("Monitored infrastructure",
                 "Configured {skill} capabilities to monitor [X]+ CIs across hybrid cloud/on-prem infrastructure with [X]% uptime"),
        'dev': ("Wrote scripts for ServiceNow",
                "Developed custom {skill} solutions automating [process], reducing manual effort by [X]% and saving [X] hours/week"),
        'module': ("Used ServiceNow modules",
                   "Implemented {skill} for [use case], improving [metric] by [X]% and supporting [X]+ end users"),
        'cert': ("Have ServiceNow certification",
                 "Earned {skill} certification demonstrating advanced expertise in ServiceNow platform capabilities"),
        'lang': ("Used APIs",
                 "Utilised {skill} for enterprise integrations connecting ServiceNow with [system], processing [X]+ transactions daily"),
    }

    rewrites = []
    keyword_bullets = []
    critical_missing = [s for s in missing if SKILL_CATALOG.get(s, {}).get('w', 0) >= 5]

    for skill in critical_missing[:6]:
        cat = SKILL_CATALOG.get(skill, {}).get('cat', 'dev')
        before, after = bullet_templates.get(cat, ("Worked on {skill}", "Leveraged {skill} for [accomplishment], achieving [metric]"))
        nice = skill.replace('_', ' ').title()
        rewrites.append({
            'before': before.format(skill=nice),
            'after': after.format(skill=nice),
        })
        keyword_bullets.append(after.format(skill=nice))

    metrics_coaching = [
        "Replace 'managed' with 'reduced resolution time by X%'",
        "Replace 'responsible for' with 'delivered/implemented/automated'",
        "Add dollar amounts: 'saved $X annually in licensing costs'",
        "Add user counts: 'supporting X+ end users across Y departments'",
        "Add time savings: 'cutting processing time from X hours to Y minutes'",
    ]

    return {
        'rewrites': rewrites,
        'keyword_bullets': keyword_bullets,
        'metrics_coaching': metrics_coaching,
    }


# ── soft skills ───────────────────────────────────────────────────────

def _soft_skills_suggestions(resume, job):
    rl = resume.lower()
    jl = job.lower()
    j_soft = [k for k in POWER_KEYWORDS if k in jl]
    r_soft = {k for k in POWER_KEYWORDS if k in rl}

    matched = [k for k in j_soft if k in r_soft]
    critical = [k for k in j_soft if k not in r_soft]
    nice = [k for k in POWER_KEYWORDS if k not in jl and k not in r_soft][:5]

    how_to = {
        'leadership': "Add: 'Led a team of X developers...'",
        'collaboration': "Add: 'Collaborated with cross-functional teams...'",
        'communication': "Add: 'Communicated technical solutions to non-technical stakeholders...'",
        'problem solving': "Add: 'Diagnosed and resolved complex platform issues...'",
        'project management': "Add: 'Managed end-to-end delivery of X projects...'",
        'mentoring': "Add: 'Mentored X junior developers on platform best practices...'",
        'stakeholder management': "Add: 'Partnered with business stakeholders to translate requirements...'",
        'process improvement': "Add: 'Streamlined X process, reducing turnaround by X%...'",
    }

    return {
        'matched': [{'keyword': k.title(), 'status': 'found'} for k in matched],
        'critical_missing': [{'keyword': k.title(), 'how_to_add': how_to.get(k, f"Naturally weave '{k}' into an experience bullet.")} for k in critical[:8]],
        'nice_to_have': [k.title() for k in nice],
    }


# ── keyword density ───────────────────────────────────────────────────

def _keyword_density(resume, job, matched, missing):
    rows = []
    for skill in sorted(matched):
        nice = skill.replace('_', ' ').title()
        jd_count = _count_occurrences(job, skill.replace('_', ' '))
        r_count = _count_occurrences(resume, skill.replace('_', ' '))
        rows.append({
            'keyword': nice, 'jd_count': jd_count, 'resume_count': r_count,
            'status': 'ok' if r_count >= 1 else 'missing',
            'recommendation': 'Good — keyword present' if r_count >= jd_count else f'Add {max(1, jd_count - r_count)} more mention(s)',
        })
    for skill in sorted(missing):
        nice = skill.replace('_', ' ').title()
        jd_count = _count_occurrences(job, skill.replace('_', ' '))
        rows.append({
            'keyword': nice, 'jd_count': jd_count, 'resume_count': 0,
            'status': 'missing',
            'recommendation': f'Add to resume — appears {jd_count}x in JD',
        })
    return rows


# ── formatting checks ─────────────────────────────────────────────────

def _formatting_suggestions(resume):
    tips = []

    # Section headers
    has_sections = bool(re.search(r'(?im)^(experience|education|skills|summary|certifications)', resume))
    tips.append({
        'check': 'Section headers (Experience, Skills, Education)',
        'passed': has_sections,
        'severity': 'high' if not has_sections else 'pass',
        'fix': 'Add clear section headers — ATS uses them to parse your resume.' if not has_sections else '',
    })

    # Bullet points
    bullets = len(re.findall(r'(?m)^[\s]*[-•*]', resume))
    tips.append({
        'check': f'Bullet points ({bullets} found)',
        'passed': bullets >= 6,
        'severity': 'high' if bullets < 3 else 'medium' if bullets < 6 else 'pass',
        'fix': f'Add more bullet points — aim for 15-20 across experience roles.' if bullets < 6 else '',
    })

    # Word count
    wc = len(resume.split())
    tips.append({
        'check': f'Word count ({wc} words)',
        'passed': 300 <= wc <= 800,
        'severity': 'medium' if wc < 300 or wc > 800 else 'pass',
        'fix': 'Aim for 400-700 words for a single-page resume.' if wc < 300 else ('Consider trimming — most ATS prefer concise resumes.' if wc > 800 else ''),
    })

    # Email
    has_email = bool(re.search(r'[\w.-]+@[\w.-]+\.\w+', resume))
    tips.append({
        'check': 'Email address',
        'passed': has_email,
        'severity': 'high' if not has_email else 'pass',
        'fix': 'Add your email in the header — required for ATS contact parsing.' if not has_email else '',
    })

    # LinkedIn
    has_linkedin = bool(re.search(r'linkedin', resume, re.I))
    tips.append({
        'check': 'LinkedIn profile',
        'passed': has_linkedin,
        'severity': 'medium' if not has_linkedin else 'pass',
        'fix': 'Add your LinkedIn URL — recruiters check it 87% of the time.' if not has_linkedin else '',
    })

    # Dates
    has_dates = bool(re.search(r'(20\d{2}|19\d{2})\s*[-–]\s*(20\d{2}|present|current)', resume, re.I))
    tips.append({
        'check': 'Date ranges in experience',
        'passed': has_dates,
        'severity': 'high' if not has_dates else 'pass',
        'fix': 'Add date ranges (e.g., "Jan 2021 – Present") — ATS needs them for experience parsing.' if not has_dates else '',
    })

    # Action verbs
    action_verbs = ['implemented', 'developed', 'managed', 'designed', 'created',
                    'configured', 'automated', 'optimized', 'led', 'delivered',
                    'built', 'reduced', 'improved', 'streamlined', 'deployed']
    found_verbs = sum(1 for v in action_verbs if v in resume.lower())
    tips.append({
        'check': f'Action verbs ({found_verbs}/{len(action_verbs)} found)',
        'passed': found_verbs >= 5,
        'severity': 'medium' if found_verbs < 5 else 'pass',
        'fix': f'Start more bullets with action verbs: {", ".join(v for v in action_verbs if v not in resume.lower())[:5]}' if found_verbs < 5 else '',
    })

    return tips


# ── main entry point ──────────────────────────────────────────────────

def optimize_resume(resume_text, job_description):
    """Full v2 resume optimization returning section scores, copy-paste text, and density analysis."""
    if not resume_text or not job_description:
        return {'error': 'Both resume and job description are required'}

    resume_lower = resume_text.lower()
    job_lower = job_description.lower()

    # Skills extraction
    resume_skills = _extract_skills(resume_lower)
    job_skills = _extract_skills(job_lower)
    matched = sorted(set(resume_skills.keys()) & set(job_skills.keys()))
    missing = sorted(set(job_skills.keys()) - set(resume_skills.keys()),
                     key=lambda s: SKILL_CATALOG.get(s, {}).get('w', 0), reverse=True)
    extra = sorted(set(resume_skills.keys()) - set(job_skills.keys()))

    # Extra keywords
    resume_kw = _extract_extra_keywords(resume_text)
    job_kw = _extract_extra_keywords(job_description)
    missing_keywords = job_kw - resume_kw

    # ATS score
    total_job = len(job_skills) + len(job_kw)
    matched_items = len(matched) + len(resume_kw & job_kw)
    ats_score = min(int((matched_items / max(total_job, 1)) * 100), 100)

    # Match score
    match_score = calculate_match_score(job_description, '', resume_text)

    # Section scores
    section_scores = _compute_section_scores(resume_text, job_description,
                                              matched, missing, resume_kw, job_kw)

    # Build suggestions (v2 structure)
    suggestions = {
        'section_scores': section_scores,
        'professional_summary': _summary_suggestions(matched, missing, job_description, resume_text),
        'hard_skills': _hard_skills_suggestions(set(matched), set(missing), set(extra)),
        'work_experience': _experience_suggestions(missing, job_description),
        'soft_skills': _soft_skills_suggestions(resume_text, job_description),
        'keyword_density': _keyword_density(resume_text, job_description, matched, missing),
        'formatting_tips': _formatting_suggestions(resume_text),
        # Keep legacy keys for backward compat
        'key_highlights': _legacy_highlights(matched, missing),
        'technical_skills': _hard_skills_suggestions(set(matched), set(missing), set(extra)),
    }

    return {
        'ats_score': ats_score,
        'match_score': match_score,
        'matched_skills': [s.replace('_', ' ').title() for s in matched],
        'missing_skills': [s.replace('_', ' ').title() for s in missing],
        'extra_skills': [s.replace('_', ' ').title() for s in extra],
        'missing_keywords': sorted(missing_keywords),
        'total_job_keywords': total_job,
        'total_matched': matched_items,
        'suggestions': suggestions,
    }


def _legacy_highlights(matched, missing):
    """Keep backward-compatible key_highlights for old JS."""
    highlights = []
    high_matched = [s for s in matched if SKILL_CATALOG.get(s, {}).get('w', 0) >= 6]
    if high_matched:
        highlights.append({
            'type': 'reinforce', 'title': 'Emphasize These Existing Skills',
            'items': [f"Make sure '{s.replace('_', ' ').title()}' appears prominently" for s in high_matched[:5]]
        })
    critical = [s for s in missing if SKILL_CATALOG.get(s, {}).get('w', 0) >= 6]
    if critical:
        highlights.append({
            'type': 'critical_gap', 'title': 'Critical Skills to Add',
            'items': [f"Add '{s.replace('_', ' ').title()}' — high-weight keyword" for s in critical[:6]]
        })
    return highlights
