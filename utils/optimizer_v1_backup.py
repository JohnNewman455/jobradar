"""
Resume Optimizer — ATS-style keyword gap analysis & improvement suggestions.
Rule-based: extracts skills from resume & JD, finds gaps, generates suggestions.
"""

import re
from utils.scorer import SKILL_CATALOG, _text_has_skill, _extract_skills, calculate_match_score


# Additional important keywords beyond SKILL_CATALOG
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


def _extract_extra_keywords(text):
    """Extract important non-catalog keywords from text."""
    text_lower = text.lower()
    found = set()
    for kw in EXTRA_KEYWORDS:
        if kw in text_lower:
            found.add(kw)
    return found


def _generate_summary_options(matched_skills, missing_skills, job_text):
    """Generate 2-3 professional summary options."""
    job_lower = job_text.lower()
    options = []

    # Extract role hint from job
    role_hints = []
    for hint in ['developer', 'administrator', 'analyst', 'architect',
                 'consultant', 'engineer', 'manager', 'specialist']:
        if hint in job_lower:
            role_hints.append(hint.title())
    role = role_hints[0] if role_hints else 'Professional'

    # Determine platform
    platform = 'ServiceNow' if 'servicenow' in matched_skills or 'servicenow' in [s for s in missing_skills] else 'IT'

    top_matched = [s.replace('_', ' ').title() for s in sorted(matched_skills, key=lambda s: SKILL_CATALOG.get(s, {}).get('w', 0), reverse=True)[:6]]
    top_missing = [s.replace('_', ' ').title() for s in sorted(missing_skills, key=lambda s: SKILL_CATALOG.get(s, {}).get('w', 0), reverse=True)[:4]]

    matched_str = ', '.join(top_matched) if top_matched else 'various IT skills'
    gap_str = ', '.join(top_missing[:3]) if top_missing else ''

    # Option 1: Conservative (focus on what you already have)
    options.append({
        'label': 'Option 1: Conservative',
        'text': f"Experienced {platform} {role} with proven expertise in {matched_str}. Skilled in delivering enterprise-grade solutions that drive operational efficiency and digital transformation.",
        'recommended': False
    })

    # Option 2: Comprehensive (weave in missing keywords naturally)
    if gap_str:
        all_skills_str = ', '.join(top_matched[:4] + top_missing[:2])
        options.append({
            'label': 'Option 2: Comprehensive (Recommended)',
            'text': f"Results-driven {platform} {role} with deep expertise spanning {all_skills_str}. Passionate about leveraging platform capabilities to streamline processes, improve service delivery, and support business objectives.",
            'recommended': True
        })
    else:
        options.append({
            'label': 'Option 2: Impact-Focused (Recommended)',
            'text': f"Results-driven {platform} {role} with extensive hands-on experience in {matched_str}. Track record of delivering scalable solutions, optimizing workflows, and ensuring alignment with organizational goals.",
            'recommended': True
        })

    # Option 3: Metrics-focused
    options.append({
        'label': 'Option 3: Metrics-Focused',
        'text': f"Detail-oriented {platform} {role} with [X]+ years of experience in {matched_str}. Known for reducing incident resolution times by [X]%, improving process automation coverage, and maintaining [X]% platform uptime.",
        'recommended': False
    })

    return options


def _generate_highlights(matched_skills, missing_skills):
    """Generate key highlights to add to resume."""
    highlights = []

    # Skills to reinforce (already in resume but should be highlighted)
    high_value_matched = [
        s for s in matched_skills
        if SKILL_CATALOG.get(s, {}).get('w', 0) >= 6
    ]
    if high_value_matched:
        highlights.append({
            'type': 'reinforce',
            'title': 'Emphasize These Existing Skills',
            'items': [f"Make sure '{s.replace('_', ' ').title()}' appears prominently in your experience bullets" for s in high_value_matched[:5]]
        })

    # Skills to add (missing from resume but in job)
    if missing_skills:
        critical = [s for s in missing_skills if SKILL_CATALOG.get(s, {}).get('w', 0) >= 6]
        nice_to_have = [s for s in missing_skills if SKILL_CATALOG.get(s, {}).get('w', 0) < 6]

        if critical:
            highlights.append({
                'type': 'critical_gap',
                'title': 'Critical Skills to Add',
                'items': [f"Add '{s.replace('_', ' ').title()}' — high-weight keyword the ATS will look for" for s in critical[:6]]
            })

        if nice_to_have:
            highlights.append({
                'type': 'nice_to_have',
                'title': 'Nice-to-Have Keywords',
                'items': [f"Consider adding '{s.replace('_', ' ').title()}'" for s in nice_to_have[:5]]
            })

    return highlights


def _generate_skills_section(matched_skills, missing_skills, extra_skills):
    """Generate technical skills section suggestions."""
    suggestions = {
        'keep': [],
        'add': [],
        'organize_by': {}
    }

    # Group by category
    cat_names = {
        'platform': 'Platform',
        'itsm': 'ITSM',
        'sam': 'SAM / ITAM',
        'itom': 'ITOM',
        'module': 'Modules',
        'dev': 'Development',
        'cert': 'Certifications',
        'lang': 'Languages & APIs',
        'meth': 'Methodology'
    }

    for skill in matched_skills:
        cat = SKILL_CATALOG.get(skill, {}).get('cat', 'other')
        cat_label = cat_names.get(cat, 'Other')
        suggestions['organize_by'].setdefault(cat_label, []).append({
            'skill': skill.replace('_', ' ').title(),
            'status': 'matched',
        })

    for skill in missing_skills:
        cat = SKILL_CATALOG.get(skill, {}).get('cat', 'other')
        cat_label = cat_names.get(cat, 'Other')
        w = SKILL_CATALOG.get(skill, {}).get('w', 0)
        suggestions['organize_by'].setdefault(cat_label, []).append({
            'skill': skill.replace('_', ' ').title(),
            'status': 'missing',
            'priority': 'high' if w >= 6 else 'medium'
        })

    suggestions['keep'] = [s.replace('_', ' ').title() for s in matched_skills]
    suggestions['add'] = [s.replace('_', ' ').title() for s in missing_skills]

    return suggestions


def _generate_experience_tips(missing_skills, missing_keywords, job_text):
    """Generate work experience improvement tips."""
    tips = []

    # High-priority missing skills → suggest experience bullets
    critical_missing = [s for s in missing_skills if SKILL_CATALOG.get(s, {}).get('w', 0) >= 5]

    bullet_templates = {
        'itsm': "Managed {skill} processes within ServiceNow, handling [X]+ tickets monthly and maintaining [X]% SLA compliance",
        'sam': "Administered {skill} module, tracking [X]+ software assets and identifying $[X]K in license savings",
        'itom': "Configured {skill} capabilities to monitor [X]+ CIs across hybrid infrastructure",
        'dev': "Developed custom {skill} to automate [describe process], reducing manual effort by [X]%",
        'module': "Implemented {skill} for [use case], improving [metric] by [X]%",
        'cert': "Earned {skill} certification demonstrating expertise in ServiceNow platform",
        'lang': "Utilized {skill} for [integration/development purpose]",
    }

    for skill in critical_missing[:8]:
        cat = SKILL_CATALOG.get(skill, {}).get('cat', 'dev')
        template = bullet_templates.get(cat, "Leveraged {skill} for [describe accomplishment]")
        tips.append({
            'skill': skill.replace('_', ' ').title(),
            'bullet': template.format(skill=skill.replace('_', ' ').title()),
            'priority': 'high' if SKILL_CATALOG.get(skill, {}).get('w', 0) >= 7 else 'medium'
        })

    # Extra keyword suggestions
    if missing_keywords:
        tips.append({
            'skill': 'General Keywords',
            'bullet': f"Try to naturally include these keywords: {', '.join(list(missing_keywords)[:6])}",
            'priority': 'low'
        })

    return tips


def optimize_resume(resume_text, job_description):
    """
    Full resume optimization analysis.

    Returns:
        dict with ats_score, gap analysis, and section-by-section suggestions
    """
    if not resume_text or not job_description:
        return {'error': 'Both resume and job description are required'}

    resume_lower = resume_text.lower()
    job_lower = job_description.lower()

    # 1. Extract skills
    resume_skills = _extract_skills(resume_lower)
    job_skills = _extract_skills(job_lower)

    matched = set(resume_skills.keys()) & set(job_skills.keys())
    missing = set(job_skills.keys()) - set(resume_skills.keys())
    extra = set(resume_skills.keys()) - set(job_skills.keys())

    # 2. Extra keyword analysis
    resume_kw = _extract_extra_keywords(resume_text)
    job_kw = _extract_extra_keywords(job_description)
    missing_keywords = job_kw - resume_kw

    # 3. ATS score (keyword coverage %)
    total_job_items = len(job_skills) + len(job_kw)
    matched_items = len(matched) + len(resume_kw & job_kw)
    ats_score = int((matched_items / max(total_job_items, 1)) * 100)

    # 4. Match score
    match_score = calculate_match_score(job_description, '', resume_text)

    # 5. Generate suggestions
    matched_list = sorted(matched)
    missing_list = sorted(missing, key=lambda s: SKILL_CATALOG.get(s, {}).get('w', 0), reverse=True)
    extra_list = sorted(extra)

    suggestions = {
        'professional_summary': _generate_summary_options(matched_list, missing_list, job_description),
        'key_highlights': _generate_highlights(matched_list, missing_list),
        'technical_skills': _generate_skills_section(matched_list, missing_list, extra_list),
        'work_experience': _generate_experience_tips(missing_list, missing_keywords, job_description),
    }

    return {
        'ats_score': min(ats_score, 100),
        'match_score': match_score,
        'matched_skills': [s.replace('_', ' ').title() for s in matched_list],
        'missing_skills': [s.replace('_', ' ').title() for s in missing_list],
        'extra_skills': [s.replace('_', ' ').title() for s in extra_list],
        'missing_keywords': sorted(missing_keywords),
        'total_job_keywords': total_job_items,
        'total_matched': matched_items,
        'suggestions': suggestions,
    }
