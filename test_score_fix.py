"""Test scorer with Deloitte JD as resume AND user's actual resume"""
from utils.scorer import calculate_match_score

deloitte_jd = (
    "ITSM Process Product Architect ServiceNow Deloitte Global Technology "
    "architect cutting edge processes solutions modernizing IT Service Management "
    "ServiceNow Dynatrace Observability AI solutions Cloud Discovery "
    "Design architect innovate IT Service Management incorporating Agentic AI "
    "monitoring solutions automated workflows "
    "Service Strategy Transition Operations value stream ITSM "
    "technical roadmap platform capabilities governance "
    "AI technologies ServiceNow Business Architecture Service Excellence Observability "
    "Cloud Azure AWS Google orchestration technologies "
    "monitoring solutions common workflow engine ServiceNow automate remediation self-healing "
    "5-7 years designing developing IT Operations processes enterprise grade solutions "
    "minimum 3 years within ServiceNow platform "
    "data governance automation complex hybrid cloud on-premise solutions "
    "automating process customer interactions Predictive Agentic AI machine learning "
    "ITSM ITIL processes effective operations "
    "ServiceNow Master Technical Architect Certified Implementation Specialist ITIL certification "
)

user_resume = (
    "Pavan Kumar ServiceNow Developer CBC Radio Canada "
    "3+ years ServiceNow 6+ years IT experience "
    "SAM Pro ITSM ITAM Software Asset Management "
    "Service Catalog Flow Designer Business Rules Client Scripts "
    "UI Policies UI Actions Script Includes ACLs "
    "REST API SOAP API JavaScript GlideRecord "
    "CSA Certified System Administrator CAD in progress "
    "Incident Management Problem Management Change Management "
    "SLA Knowledge Management Update Sets Import Sets "
    "Platform Administration Configuration Management Database CMDB"
)

sn_dev_job = (
    "ServiceNow Developer needed. Must have experience with ITSM, Service Catalog, "
    "Flow Designer, Business Rules, Client Scripts, UI Policies, Script Includes, "
    "GlideRecord, JavaScript, REST API, ACLs. CSA certification preferred. "
    "3+ years ServiceNow experience required."
)

itsm_job = (
    "ITSM Analyst ServiceNow. Incident Management, Problem Management, Change Management, "
    "CMDB, SLA management, ITIL processes. ServiceNow platform administration. "
    "Knowledge Management, Request Management."
)

sam_job = (
    "ServiceNow SAM Pro Administrator. Software Asset Management, ITAM, "
    "License Compliance, Data Normalization, Reclamation. SAM Pro implementation "
    "and configuration. ServiceNow platform."
)

short_job = "ServiceNow developer Toronto remote"

print("=== Deloitte JD as Resume ===")
print(f"vs SN Dev job:   {calculate_match_score(sn_dev_job, 'ServiceNow Developer', deloitte_jd)}")
print(f"vs ITSM job:     {calculate_match_score(itsm_job, 'ITSM Analyst ServiceNow', deloitte_jd)}")
print(f"vs Short job:    {calculate_match_score(short_job, 'ServiceNow Developer', deloitte_jd)}")
print(f"vs No resume:    {calculate_match_score(sn_dev_job, 'ServiceNow Developer', None)}")

print()
print("=== User's Actual Resume ===")
print(f"vs SN Dev:       {calculate_match_score(sn_dev_job, 'ServiceNow Developer', user_resume)}")
print(f"vs ITSM:         {calculate_match_score(itsm_job, 'ITSM Analyst ServiceNow', user_resume)}")
print(f"vs SAM:          {calculate_match_score(sam_job, 'SAM Pro Administrator ServiceNow', user_resume)}")
print(f"vs Short:        {calculate_match_score(short_job, 'ServiceNow Developer', user_resume)}")
