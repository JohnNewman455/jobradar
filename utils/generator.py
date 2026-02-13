"""
AI Asset Generator — cover letters, cold messages, bullet rewrites.

Uses a `call_llm()` placeholder that returns rule-based output now.
Drop in your OpenAI / Anthropic API key later to upgrade to real AI.
"""

import re
import os
import json


# ═══════════════════════════════════════════════════════════════════════════════
#  RESUME / JD PARSING HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _extract_name(resume: str) -> str:
    """Try to extract candidate name from top of resume."""
    if not resume:
        return ''
    lines = [l.strip() for l in resume.strip().split('\n') if l.strip()]
    if not lines:
        return ''
    # First non-empty line is usually the name
    first = lines[0]
    # Skip if it looks like a section header
    skip = ['summary', 'objective', 'experience', 'education', 'skills', 'resume', 'curriculum', 'profile']
    if first.lower().rstrip(':') in skip:
        return ''
    # Skip if too long (probably a sentence, not a name)
    if len(first) > 50:
        return ''
    # Skip if it has too many words (a name is usually 2-4 words)
    words = first.split()
    if 1 <= len(words) <= 5:
        # Clean common prefixes
        clean = re.sub(r'^(name|full name)\s*[:|-]\s*', '', first, flags=re.IGNORECASE).strip()
        return clean
    return ''


def _extract_email(resume: str) -> str:
    m = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', resume)
    return m.group(0) if m else ''


def _extract_phone(resume: str) -> str:
    m = re.search(r'[\+]?[\d\s\-\(\)]{10,15}', resume)
    return m.group(0).strip() if m else ''


def _extract_linkedin(resume: str) -> str:
    m = re.search(r'linkedin\.com/in/[\w-]+', resume, re.IGNORECASE)
    return m.group(0) if m else ''


def _extract_skills(text: str) -> list:
    """Extract skills/technologies from text."""
    # Common ServiceNow and IT skills to look for
    skill_patterns = [
        'ServiceNow', 'ITSM', 'ITOM', 'ITBM', 'CSM', 'HRSD', 'GRC', 'IRM', 'SecOps',
        'Flow Designer', 'IntegrationHub', 'Service Portal', 'Service Catalog',
        'Business Rules', 'Client Scripts', 'Script Includes', 'UI Actions', 'UI Policies',
        'REST API', 'SOAP', 'OAuth', 'MID Server', 'CMDB', 'Discovery',
        'JavaScript', 'HTML', 'CSS', 'AngularJS', 'Angular', 'React', 'Python', 'Java',
        'SQL', 'PowerShell', 'Jelly', 'Glide', 'ATF',
        'Agile', 'Scrum', 'ITIL', 'DevOps', 'CI/CD', 'Git',
        'SAM', 'HAM', 'APM', 'Event Management', 'Performance Analytics',
        'Virtual Agent', 'Predictive Intelligence', 'Machine Learning',
        'AWS', 'Azure', 'GCP', 'Jira', 'Confluence', 'Slack',
        'CAD', 'Now Mobile', 'Workspace', 'Agent Workspace',
        'Certified System Administrator', 'CSA', 'CIS', 'CAD',
        'Certified Implementation Specialist', 'Certified Application Developer',
    ]
    found = []
    text_lower = text.lower()
    for skill in skill_patterns:
        if skill.lower() in text_lower:
            found.append(skill)
    return found


def _extract_years(resume: str) -> str:
    """Extract years of experience from resume."""
    patterns = [
        r'(\d+)\+?\s*years?\s+(?:of\s+)?experience',
        r'(\d+)\+?\s*years?\s+(?:of\s+)?(?:ServiceNow|IT|software|development)',
        r'experience\s*:?\s*(\d+)\+?\s*years?',
    ]
    for p in patterns:
        m = re.search(p, resume, re.IGNORECASE)
        if m:
            return m.group(1)
    return ''


def _extract_certifications(resume: str) -> list:
    """Extract certifications from resume."""
    certs = []
    cert_patterns = [
        (r'ServiceNow\s+Certified\s+System\s+Administrator', 'ServiceNow CSA'),
        (r'CSA\b', 'CSA'),
        (r'CIS[\s-](?:ITSM|CSM|ITOM|HR|SAM|APM)', 'CIS'),
        (r'Certified\s+Implementation\s+Specialist', 'CIS'),
        (r'CAD\b', 'CAD'),
        (r'Certified\s+Application\s+Developer', 'CAD'),
        (r'ITIL\s*(?:v[34])?\s*(?:Foundation|Certified)?', 'ITIL'),
        (r'PMP\b', 'PMP'),
        (r'AWS\s+(?:Solutions?\s+Architect|Certified)', 'AWS Certified'),
        (r'Azure\s+(?:Certified|Administrator|Developer)', 'Azure Certified'),
        (r'Scrum\s+Master', 'Scrum Master'),
    ]
    resume_lower = resume.lower()
    for pattern, label in cert_patterns:
        if re.search(pattern, resume, re.IGNORECASE):
            if label not in certs:
                certs.append(label)
    return certs


def _extract_company_role_from_jd(jd: str) -> tuple:
    """Try to extract company name and role from job description."""
    company = ''
    role = ''
    # Common patterns
    m = re.search(r'(?:at|@|for|join)\s+([A-Z][\w\s&,.-]{1,40}?)(?:\s+is\s|\s+are\s|\s*[,.])', jd)
    if m:
        company = m.group(1).strip()
    m = re.search(r'(?:seeking|hiring|looking for)\s+(?:a|an)\s+(.{5,60}?)(?:\s+to\s|\s+who\s|\s*[.])', jd, re.IGNORECASE)
    if m:
        role = m.group(1).strip()
    return company, role


def _extract_key_requirements(jd: str) -> list:
    """Extract key requirements/responsibilities from JD."""
    reqs = []
    # Look for bullet points or numbered items
    for line in jd.split('\n'):
        line = line.strip()
        if line and (line.startswith(('•', '-', '●', '▪', '*', '◦')) or re.match(r'^\d+[.)]\s', line)):
            clean = re.sub(r'^[•\-●▪*◦\d.)]+\s*', '', line).strip()
            if 10 < len(clean) < 200:
                reqs.append(clean)
    return reqs[:8]


# ═══════════════════════════════════════════════════════════════════════════════
#  LLM ABSTRACTION — swap this out for a real API later
# ═══════════════════════════════════════════════════════════════════════════════

def call_llm(prompt: str, max_tokens: int = 800) -> str:
    """
    Placeholder LLM call. Returns rule-based output.
    To enable real AI, set env var OPENAI_API_KEY and uncomment below.
    """
    api_key = os.environ.get('OPENAI_API_KEY', '')
    if api_key:
        try:
            import openai
            client = openai.OpenAI(api_key=api_key)
            resp = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[{'role': 'user', 'content': prompt}],
                max_tokens=max_tokens,
                temperature=0.7,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            print(f"⚠️ OpenAI call failed, falling back to rules: {e}")
            pass

    # ── Rule-based fallback ──
    return _rule_based_response(prompt)


def _rule_based_response(prompt: str) -> str:
    """Simple rule-based generation when no LLM is available."""
    prompt_lower = prompt.lower()
    if 'cover letter' in prompt_lower:
        return _generate_cover_letter_rules(prompt)
    elif 'cold message' in prompt_lower or 'linkedin' in prompt_lower or 'recruiter' in prompt_lower:
        return _generate_cold_message_rules(prompt)
    elif 'rewrite' in prompt_lower or 'bullet' in prompt_lower:
        return _rewrite_bullet_rules(prompt)
    elif 'thank you' in prompt_lower or 'follow' in prompt_lower:
        return _generate_followup_rules(prompt)
    return "I'd be happy to help. Please provide more context about what you'd like me to generate."


# ═══════════════════════════════════════════════════════════════════════════════
#  PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

def generate_cover_letter(resume_text: str, job_description: str, company: str = '', job_title: str = '', tone: str = 'professional') -> dict:
    """Generate a tailored cover letter."""
    prompt = f"""Write a {tone} cover letter for a {job_title or 'position'} at {company or 'the company'}.

Job Description:
{job_description[:1500]}

Candidate Resume:
{resume_text[:1500]}

Requirements:
- 3-4 paragraphs
- Opening: mention the specific role and company
- Middle: connect 3-4 resume achievements to job requirements
- Closing: express enthusiasm and call to action
- Keep it under 350 words
- Use specific details from both the resume and JD
"""
    content = call_llm(prompt, max_tokens=600)
    word_count = len(content.split())

    return {
        'cover_letter': content,
        'word_count': word_count,
        'tone': tone,
        'ai_powered': bool(os.environ.get('OPENAI_API_KEY')),
        'tips': [
            'Replace any [brackets] with your actual details.',
            'Proofread for company name and role accuracy.',
            'Keep it to 1 page (250-400 words).',
        ],
    }


def generate_cold_message(resume_text: str, recruiter_name: str = '', job_title: str = '', company: str = '', platform: str = 'linkedin') -> dict:
    """Generate a cold outreach message for LinkedIn or email."""
    prompt = f"""Write a short {platform} cold message to {recruiter_name or 'a recruiter'} about a {job_title or 'ServiceNow'} role at {company or 'their company'}.

Candidate Background:
{resume_text[:800]}

Requirements:
- {platform.title()} style: concise, 3-5 sentences max
- Mention 1-2 specific skills from the candidate's background
- Express genuine interest and ask a question
- Professional but personable tone
- Under 100 words
"""
    content = call_llm(prompt, max_tokens=200)

    return {
        'message': content,
        'platform': platform,
        'word_count': len(content.split()),
        'ai_powered': bool(os.environ.get('OPENAI_API_KEY')),
        'variants': _generate_message_variants(resume_text, recruiter_name, job_title, company),
    }


def rewrite_bullet(original_bullet: str, target_skill: str = '', job_context: str = '') -> dict:
    """Rewrite a resume bullet point to be stronger / incorporate a skill."""
    prompt = f"""Rewrite this resume bullet point to be more impactful:

Original: {original_bullet}
{"Target skill to incorporate: " + target_skill if target_skill else ""}
{"Job context: " + job_context[:500] if job_context else ""}

Requirements:
- Start with a strong ACTION VERB
- Add quantified metrics (use [X] placeholders if unknown)
- Incorporate the target skill naturally
- Keep it to 1-2 lines
- Provide 3 different versions
"""
    content = call_llm(prompt, max_tokens=400)

    # Parse versions from response
    versions = _parse_versions(content, original_bullet, target_skill)

    return {
        'original': original_bullet,
        'rewrites': versions,
        'target_skill': target_skill,
        'ai_powered': bool(os.environ.get('OPENAI_API_KEY')),
        'tips': [
            'Choose the version that best matches your actual experience.',
            'Replace [X] with your real numbers.',
            'Feel free to mix elements from different versions.',
        ],
    }


def generate_thank_you(interviewer_name: str = '', job_title: str = '', company: str = '', discussion_points: str = '') -> dict:
    """Generate a post-interview thank-you email."""
    prompt = f"""Write a thank-you email after an interview for a {job_title or 'position'} at {company or 'the company'} with {interviewer_name or 'the interviewer'}.

Discussion topics: {discussion_points or 'ServiceNow implementation, team collaboration'}

Requirements:
- Short and genuine (150-200 words)
- Reference a specific discussion point
- Reiterate interest in the role
- Professional but warm
"""
    content = call_llm(prompt, max_tokens=300)

    return {
        'email': content,
        'word_count': len(content.split()),
        'ai_powered': bool(os.environ.get('OPENAI_API_KEY')),
        'send_within': '24 hours of interview',
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  RULE-BASED FALLBACKS (when no LLM key is set)
# ═══════════════════════════════════════════════════════════════════════════════

def _generate_cover_letter_rules(prompt: str) -> str:
    """Rule-based cover letter generation using actual resume/JD data embedded in prompt."""
    # Extract the resume and JD sections from the prompt
    resume = ''
    jd = ''
    m = re.search(r'Candidate Resume:\s*\n(.*?)(?:\nRequirements:|\Z)', prompt, re.DOTALL)
    if m:
        resume = m.group(1).strip()
    m = re.search(r'Job Description:\s*\n(.*?)(?:\nCandidate Resume:|\Z)', prompt, re.DOTALL)
    if m:
        jd = m.group(1).strip()

    # Extract company and role from the prompt header
    company = _extract_between(prompt, 'at ', '.')
    role = _extract_between(prompt, 'for a ', ' at')
    
    # If not found in header, try JD
    if not company:
        c, r = _extract_company_role_from_jd(jd)
        company = c or 'your company'
        if not role:
            role = r

    # Extract real details from resume
    name = _extract_name(resume)
    email = _extract_email(resume)
    phone = _extract_phone(resume)
    linkedin = _extract_linkedin(resume)
    years = _extract_years(resume)
    certs = _extract_certifications(resume)
    resume_skills = _extract_skills(resume)
    jd_skills = _extract_skills(jd)
    
    # Find matching skills between resume and JD
    matching_skills = [s for s in resume_skills if s in jd_skills]
    if not matching_skills:
        matching_skills = resume_skills[:6]
    
    # Build skill phrase
    if len(matching_skills) >= 3:
        skill_phrase = f"{', '.join(matching_skills[:3])}, and {matching_skills[3]}" if len(matching_skills) > 3 else f"{', '.join(matching_skills[:-1])}, and {matching_skills[-1]}"
    elif matching_skills:
        skill_phrase = ' and '.join(matching_skills)
    else:
        skill_phrase = 'ServiceNow development and ITSM'

    # Build years phrase
    years_phrase = f"{years}+ years of" if years else "extensive"

    # Certifications phrase
    cert_phrase = ''
    if certs:
        cert_phrase = f"My {', '.join(certs[:3])} certification{'s' if len(certs) > 1 else ''}, combined with"
    else:
        cert_phrase = "My hands-on platform expertise, combined with"

    # Extract key JD requirements for middle paragraph
    jd_reqs = _extract_key_requirements(jd)
    
    # Build achievement bullets from JD requirements
    achievement_lines = []
    if jd_reqs:
        for req in jd_reqs[:3]:
            achievement_lines.append(f"demonstrated capability in {req.lower().rstrip('.')}")
    else:
        achievement_lines = [
            f"developed and maintained ServiceNow applications and workflows",
            f"implemented {matching_skills[0] if matching_skills else 'ITSM'} solutions improving operational efficiency",
            f"created custom integrations connecting ServiceNow with enterprise systems",
        ]

    achievements_text = '; '.join(achievement_lines)

    # Contact line
    contact_parts = []
    if phone:
        contact_parts.append(phone)
    if email:
        contact_parts.append(email)
    if linkedin:
        contact_parts.append(linkedin)
    contact_line = ' | '.join(contact_parts) if contact_parts else '[Your Phone] | [Your Email]'

    return f"""Dear Hiring Manager,

I am writing to express my strong interest in the {role or 'ServiceNow Developer'} position at {company}. With {years_phrase} experience in {skill_phrase}, I am confident I can make a meaningful contribution to your team.

In my career, I have {achievements_text}. My experience with {skill_phrase} aligns closely with what you are looking for in this role.

{cert_phrase} {years_phrase} hands-on platform experience, positions me to contribute immediately while continuing to grow with your team. I am particularly excited about this opportunity to bring my expertise in {matching_skills[0] if matching_skills else 'ServiceNow'} to {company}.

I would welcome the opportunity to discuss how my skills and experience align with your needs. Thank you for considering my application.

Best regards,
{name or '[Your Name]'}
{contact_line}"""


def _generate_cold_message_rules(prompt: str) -> str:
    """Rule-based cold message using actual resume data."""
    recruiter = _extract_between(prompt, 'to ', ' about') or 'there'
    role = _extract_between(prompt, 'about a ', ' role') or 'ServiceNow'
    
    # Extract resume from prompt
    resume = ''
    m = re.search(r'Candidate Background:\s*\n(.*?)(?:\nRequirements:|\Z)', prompt, re.DOTALL)
    if m:
        resume = m.group(1).strip()
    
    name = _extract_name(resume)
    years = _extract_years(resume)
    certs = _extract_certifications(resume)
    skills = _extract_skills(resume)
    
    years_phrase = f"{years}+ years" if years else "several years"
    cert_phrase = f" ({', '.join(certs[:2])} certified)" if certs else ""
    top_skills = ', '.join(skills[:3]) if skills else "ITSM, Service Catalog, and Flow Designer"
    sign_off = name if name else '[Your Name]'

    return f"""Hi {recruiter},

I came across the {role} opportunity and was immediately interested. With {years_phrase} of hands-on ServiceNow experience{cert_phrase} including {top_skills}, I believe I'd be a strong fit for your team.

I'd love to learn more about the role and how I could contribute. Would you be open to a brief chat this week?

Best,
{sign_off}"""


def _rewrite_bullet_rules(prompt: str) -> str:
    """Rule-based bullet rewrite."""
    return """Version 1 (Impact-focused):
• Developed and deployed [X]+ custom ServiceNow solutions, automating critical business processes and reducing manual effort by [X]%

Version 2 (Metrics-heavy):
• Configured ServiceNow workflows processing [X]+ requests monthly, improving SLA compliance from [X]% to [X]% and reducing resolution time by [X] hours

Version 3 (Technical depth):
• Designed and implemented ServiceNow applications leveraging Business Rules, Client Scripts, and REST API integrations, serving [X]+ end users across [X] departments"""


def _generate_followup_rules(prompt: str) -> str:
    """Rule-based follow-up/thank-you email using available context."""
    interviewer = _extract_between(prompt, 'with ', '.') or 'the interviewer'
    role = _extract_between(prompt, 'for a ', ' at') or 'the position'
    company = _extract_between(prompt, 'at ', ' with') or 'your company'
    topics = _extract_between(prompt, 'Discussion topics: ', '\n') or ''

    # Use discussion points if provided
    if topics and topics != 'ServiceNow implementation, team collaboration':
        topic_ref = f"I especially enjoyed discussing {topics.split(',')[0].strip()}"
    else:
        topic_ref = "I especially enjoyed learning about your team's approach and current projects"

    return f"""Subject: Thank You — {role} Interview

Dear {interviewer},

Thank you for taking the time to speak with me about the {role} role at {company}. {topic_ref}, and it reinforced my enthusiasm for this opportunity.

My experience aligns well with what you described, and I'm confident I can contribute meaningfully to your team from day one. I'm very excited about the possibility of joining {company}.

Please don't hesitate to reach out if you need any additional information. I look forward to hearing from you.

Best regards,
[Your Name]"""


# ═══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _generate_message_variants(resume_text, recruiter, title, company):
    """Generate 2 alternative message versions using actual resume data."""
    r = recruiter or 'there'
    t = title or 'ServiceNow'
    c = company or 'your company'
    
    years = _extract_years(resume_text) if resume_text else ''
    certs = _extract_certifications(resume_text) if resume_text else []
    skills = _extract_skills(resume_text) if resume_text else []
    
    years_txt = f"{years}+" if years else "several"
    cert_txt = f" and a {certs[0]} certification" if certs else ""
    skills_txt = ', '.join(skills[:3]) if skills else "ITSM, Flow Designer, and custom app development"

    return [
        {
            'label': 'Direct & Confident',
            'text': f"Hi {r}, I noticed the {t} opening at {c}. With {years_txt} years of ServiceNow experience{cert_txt}, I'd love to explore if I could be a fit. Happy to share my resume if interested!",
        },
        {
            'label': 'Question-Led',
            'text': f"Hi {r}, I'm a ServiceNow developer with experience in {skills_txt}. I'm curious about the {t} role at {c} — is the team focused more on implementations or platform optimization? Would love to connect!",
        },
    ]


def _parse_versions(llm_output, original, target_skill):
    """Parse multiple versions from LLM output."""
    versions = []
    # Try to find numbered versions
    parts = re.split(r'(?:Version|Option|\d+[.)]\s)', llm_output)
    for part in parts:
        cleaned = part.strip().lstrip(':').strip()
        if cleaned and len(cleaned) > 20:
            # Ensure it starts with a bullet
            if not cleaned.startswith(('•', '-')):
                cleaned = f"• {cleaned}"
            versions.append(cleaned)

    # If parsing failed, generate rule-based versions
    if len(versions) < 2:
        clean = original.lstrip('•-●▪* ').strip()
        skill_text = f", leveraging {target_skill}" if target_skill else ""
        versions = [
            f"• {clean}{skill_text}, resulting in [X]% improvement in operational efficiency",
            f"• Led initiative to {clean.lower()}{skill_text}, reducing processing time by [X]% and serving [X]+ users",
            f"• Designed and implemented solution to {clean.lower()}{skill_text}, achieving [X]% adoption rate within [X] months",
        ]

    return versions[:3]


def _extract_between(text, start, end):
    """Extract text between two markers."""
    try:
        s = text.index(start) + len(start)
        e = text.index(end, s)
        return text[s:e].strip()
    except (ValueError, IndexError):
        return ''
