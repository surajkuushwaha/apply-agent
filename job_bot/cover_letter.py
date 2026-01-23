"""
Cover letter generation with templates and Gemini AI fallback.

Provides:
- Multiple role-specific templates
- AI-powered generation via Gemini
- Automatic template selection based on job description
- Fallback to templates when AI fails
"""

import os
import google.generativeai as genai

from .config import COVER_LETTER_MODEL, CANDIDATE_PROFILE_COMPACT

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# =============================================================================
# COVER LETTER TEMPLATES
# =============================================================================

TEMPLATES = {
    "backend": """Dear Hiring Team,

I am writing to express my interest in the {job_title} position at {company}. With over 4 years of experience as a Senior Backend Engineer at CultureX Entertainment, I have developed deep expertise in building scalable, high-performance backend systems.

My core stack includes Node.js, TypeScript, GraphQL, and Golang, with extensive experience in cloud infrastructure (AWS Lambda, SQS, SNS, EventBridge). I've architected event-driven systems handling 100M+ monthly requests and led zero-downtime migrations for 50+ global brands. What excites me most about this role is the opportunity to apply my experience with microservices and distributed systems to {company}'s technical challenges.

I thrive in remote-first environments with strong async communication skills. I would welcome the opportunity to discuss how my backend expertise can contribute to your team's success.

Best regards,
Suraj Kushwaha
jobs@surajkuushwaha.com | github.com/surajkuushwaha""",

    "ai_engineer": """Dear Hiring Team,

I am excited to apply for the {job_title} position at {company}. As a Senior Backend Engineer with hands-on experience building production-grade LLM applications, I bring a unique combination of traditional backend expertise and cutting-edge AI development skills.

I have built fully automated workflows using LangChain and LangGraph, implementing agentic patterns for complex multi-step processes. My experience includes integrating LLMs (OpenAI, Claude, Gemini) into production systems, developing RAG pipelines with vector databases, and creating reliable prompt engineering strategies. Combined with my 4+ years of experience in scalable backend systems (Node.js, TypeScript, AWS), I can bridge the gap between AI capabilities and production-ready infrastructure.

I am passionate about building AI-powered solutions that deliver real business value. I would love to discuss how my blend of backend engineering and LLM expertise can contribute to {company}'s AI initiatives.

Best regards,
Suraj Kushwaha
jobs@surajkuushwaha.com | github.com/surajkuushwaha""",

    "platform": """Dear Hiring Team,

I am writing to apply for the {job_title} position at {company}. With my background in building extensibility platforms and API products, I am confident I can make a significant contribution to your team.

At CultureX Entertainment, I owned a public-facing API microservice, transforming an internal tool into a high-availability product used by enterprise clients. I have extensive experience with event-driven architectures (AWS EventBridge, SQS, Lambda), CI/CD pipelines, and infrastructure automation using Docker and GitHub Actions. I excel at designing systems that are both developer-friendly and operationally robust.

My experience with microservices, API design, and cloud infrastructure positions me well to help {company} scale its platform capabilities. I look forward to discussing how I can contribute to your platform engineering efforts.

Best regards,
Suraj Kushwaha
jobs@surajkuushwaha.com | github.com/surajkuushwaha""",

    "devops": """Dear Hiring Team,

I am applying for the {job_title} role at {company}. My experience building and maintaining cloud infrastructure at scale makes me a strong candidate for this position.

Over 4+ years at CultureX Entertainment, I've worked extensively with AWS services (Lambda, SQS, SNS, EventBridge, S3, EC2), Docker, and CI/CD pipelines using GitHub Actions. I've architected event-driven systems handling 100M+ monthly requests and reduced manual debugging effort by 40% through infrastructure improvements. I'm passionate about automation, reliability, and enabling development teams to ship faster.

I would be thrilled to bring my infrastructure and automation expertise to {company}. I look forward to learning more about your DevOps challenges and how I can help address them.

Best regards,
Suraj Kushwaha
jobs@surajkuushwaha.com | github.com/surajkuushwaha""",

    "default": """Dear Hiring Team,

I am writing to express my interest in the {job_title} position at {company}. With over 4 years of experience as a Senior Backend Engineer, I have developed strong expertise in building scalable software systems and delivering impactful products.

My technical background spans Node.js, TypeScript, GraphQL, and cloud infrastructure (AWS), with additional experience in AI/LLM integration using LangChain and LangGraph. I've led zero-downtime migrations, architected event-driven systems handling 100M+ requests monthly, and built 40+ MVPs from concept to production. I thrive in remote-first, startup environments where I can take ownership and make meaningful contributions.

I am excited about the opportunity to bring my skills to {company}. I would welcome the chance to discuss how my experience aligns with your team's needs.

Best regards,
Suraj Kushwaha
jobs@surajkuushwaha.com | github.com/surajkuushwaha"""
}


def match_template(job_title: str, job_description: str) -> str:
    """
    Match a job to the best template based on title and description.

    Returns the template key.
    """
    text = f"{job_title} {job_description}".lower()

    # AI/LLM roles
    ai_keywords = ["ai engineer", "ai developer", "llm", "langchain", "agentic",
                   "machine learning", "ml engineer", "nlp", "artificial intelligence"]
    if any(kw in text for kw in ai_keywords):
        return "ai_engineer"

    # Platform/API roles
    platform_keywords = ["platform engineer", "api engineer", "extensibility",
                         "infrastructure engineer", "developer experience"]
    if any(kw in text for kw in platform_keywords):
        return "platform"

    # DevOps roles
    devops_keywords = ["devops", "sre", "site reliability", "infrastructure",
                       "cloud engineer", "systems engineer"]
    if any(kw in text for kw in devops_keywords):
        return "devops"

    # Backend roles (most common)
    backend_keywords = ["backend", "back-end", "server-side", "node.js", "nodejs",
                        "golang", "typescript", "graphql", "microservices"]
    if any(kw in text for kw in backend_keywords):
        return "backend"

    return "default"


def generate_cover_letter_ai(job_title: str, company: str, job_description: str) -> str:
    """
    Generate a personalized cover letter using Gemini AI.

    Raises an exception if generation fails.
    """
    prompt = f"""
    Write a concise, professional cover letter (3 paragraphs, under 250 words) for:

    Position: {job_title} at {company}
    Job Description: {job_description}

    {CANDIDATE_PROFILE_COMPACT}

    Guidelines:
    - Be professional and enthusiastic
    - Highlight 2-3 most relevant experiences for this specific role
    - Show understanding of the company/role
    - Keep it concise and impactful
    - Do NOT use generic phrases like "I am excited to apply"
    - End with contact info: jobs@surajkuushwaha.com | github.com/surajkuushwaha
    """

    model = genai.GenerativeModel(COVER_LETTER_MODEL)
    response = model.generate_content(prompt)
    return response.text


def generate_cover_letter_template(job_title: str, company: str, job_description: str) -> str:
    """
    Generate a cover letter using templates.

    Used as fallback when AI generation fails.
    """
    template_key = match_template(job_title, job_description)
    template = TEMPLATES[template_key]
    return template.format(job_title=job_title, company=company)


def generate_cover_letter(job_title: str, company: str, job_description: str) -> tuple[str, str]:
    """
    Generate a cover letter, trying AI first then falling back to templates.

    Returns:
        tuple: (cover_letter_text, generation_method)
               generation_method is either "ai" or "template:{template_key}"
    """
    try:
        cover_letter = generate_cover_letter_ai(job_title, company, job_description)
        return cover_letter, "ai"
    except Exception as e:
        print(f"AI generation failed: {e}. Using template fallback.")
        template_key = match_template(job_title, job_description)
        cover_letter = generate_cover_letter_template(job_title, company, job_description)
        return cover_letter, f"template:{template_key}"
