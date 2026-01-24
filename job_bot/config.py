"""
Centralized configuration for the Job Application Bot.

All settings, keywords, rate limits, and candidate profile are defined here.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# PATHS
# =============================================================================

APPLIED_JOBS_FILE = Path("applied_jobs_v2.json")
VIEWED_JOBS_FILE = Path("viewed_jobs.json")
SELECTED_JOBS_FILE = Path("selected_jobs.json")
REJECTED_JOBS_FILE = Path("rejected_jobs.json")
RESUME_PATH = Path("/Users/suraj/Personal/projects/browser-use/Suraj_Kushwaha_Resumes-1.pdf")
SESSION_STORAGE_DIR = Path("browser_sessions")

# =============================================================================
# APPLICATION SETTINGS
# =============================================================================

JOBS_TO_APPLY = 5
MIN_JOB_SCORE = 30
REQUIRE_SALARY_RANGE = False

# =============================================================================
# MODEL CONFIGURATION
# =============================================================================

COVER_LETTER_MODEL = "gemini-2.5-flash"
BROWSER_AGENT_MODEL = "gemini-2.5-flash"

# =============================================================================
# LINKEDIN FRESHNESS OPTIONS
# =============================================================================

LINKEDIN_FRESHNESS = {
    "1h": "r3600",      # Past hour
    "24h": "r86400",    # Past 24 hours (default)
    "7d": "r604800",    # Past week
    "30d": "r2592000",  # Past month
}

DEFAULT_LINKEDIN_FRESHNESS = "24h"

# =============================================================================
# RATE LIMITS PER PORTAL
# =============================================================================

RATE_LIMITS = {
    "linkedin": {
        "type": "daily",
        "limit": 1,
        "delay_seconds": 10,  # Delay between applications
    },
    "workatastartup": {
        "type": "weekly",
        "limit": 1,
        "delay_seconds": 5,
    },
}

# =============================================================================
# PORTAL ALLOCATION (total should equal JOBS_TO_APPLY)
# =============================================================================

PORTAL_ALLOCATION = {
    "linkedin": 3,
    "workatastartup": 2,
}

# =============================================================================
# JOB SCORING CONFIGURATION
# =============================================================================

BLACKLIST_COMPANIES = [
    # Add companies you want to skip
]

REQUIRED_KEYWORDS = [
    "backend", "node", "nodejs", "typescript", "aws", "golang", "go",
    "graphql", "devops", "platform", "api",
    # AI/LLM Developer keywords
    "langchain", "agentic", "llm", "llms", "ai developer", "ai engineer",
    "automated workflows", "agent workflows", "workflow automation"
]

BONUS_KEYWORDS = [
    "remote", "microservices", "saas", "startup", "series a", "series b",
    "mongodb", "postgresql", "redis", "docker", "kubernetes", "lambda",
    # AI/LLM Bonus keywords
    "openai", "anthropic", "claude", "gpt", "gemini", "langgraph",
    "autonomous agents", "multi-agent", "rag", "vector database",
    "prompt engineering", "fine-tuning", "model deployment"
]

# Negative keywords - jobs containing these will be auto-skipped
NEGATIVE_KEYWORDS = [
    "frontend", "react developer", "vue developer", "angular developer",
    "ios", "ios developer", "android", "android developer",
    "qa engineer", "quality assurance", "test engineer",
    "designer", "ui designer", "ux designer", "graphic designer",
    "intern", "internship",
    "manager", "engineering manager", "product manager",
    "sales", "marketing", "recruiter", "hr",
    "data analyst", "business analyst",
]

# Scoring weights
REQUIRED_KEYWORD_SCORE = 8
BONUS_KEYWORD_SCORE = 4
EXPERIENCE_MATCH_SCORE = 10
REMOTE_BONUS_SCORE = 5
NEGATIVE_KEYWORD_PENALTY = -50  # Heavy penalty to skip irrelevant jobs

# =============================================================================
# CREDENTIALS (from .env)
# =============================================================================

LINKEDIN_USER = os.getenv("LINKEDIN_USER", "")
LINKEDIN_PASS = os.getenv("LINKEDIN_PASS", "")
WORKATASTARTUP_USER = os.getenv("WORKATASTARTUP_USER", "")
WORKATASTARTUP_PASS = os.getenv("WORKATASTARTUP_PASS", "")

# =============================================================================
# CANDIDATE PROFILE
# =============================================================================

CANDIDATE_PROFILE = """
CANDIDATE PROFILE:
- Name: Suraj Kushwaha
- Title: Senior Backend Engineer | Product & Extensibility Platforms
- Experience: 4+ years at CultureX Entertainment (B2B SaaS, Influencer Marketing)
- Contact: jobs@surajkuushwaha.com | +91 91067 64917
- GitHub: github.com/surajkuushwaha
- LinkedIn: linkedin.com/in/surajkuushwaha

CORE STACK:
- Languages: Node.js, TypeScript, GraphQL, JavaScript (ES6+), Golang, Python
- Backend: Express.js, Hono, MongoDB, PostgreSQL, MySQL, Redis, RESTful APIs, Microservices
- Cloud: AWS (Lambda, SQS, SNS, EventBridge, S3, EC2), Docker, GitHub Actions, CI/CD
- AI/LLM: LangChain, LangGraph, Agentic Workflows, LLM Integration, Automated Workflows
- AI/Tooling: LLMs for debugging/documentation, Linux, Git, Tmux

AI/LLM EXPERIENCE:
- Built fully automated workflows with LLMs using LangChain agentic patterns
- Designed and implemented agentic workflows for complex multi-step processes
- Experience with autonomous agents, multi-agent systems, and workflow automation
- Integrated LLMs (OpenAI, Anthropic Claude, Google Gemini) into production systems
- Developed RAG (Retrieval Augmented Generation) pipelines and vector database integrations
- Created prompt engineering strategies for reliable agent behavior
- Deployed and scaled LLM-powered applications in production environments

KEY ACHIEVEMENTS:
- Owned public-facing API microservice (transformed internal tool into high-availability product)
- Led zero-downtime migration to unified SaaS architecture for 50+ global brands
- Architected event-driven systems (EventBridge, SQS, Lambda) handling 100M+ monthly requests
- Scaled backend infrastructure, reducing manual debugging effort by 40%
- Developed 40+ MVPs for influencer marketing platform, securing first client
- Built production-ready agentic workflows automating complex business processes

PROFESSIONAL STRENGTHS:
- Remote/Async Native: Fluent in written communication, generous context in PRs
- Pragmatic Performance: Experienced in measuring bottlenecks in high-traffic B2B environments
- AI/LLM Expertise: Strong background in building reliable, production-grade LLM applications

TARGET ROLES:
- Senior Backend Engineer
- Backend Engineer
- Platform Engineer
- API/Extensibility Engineer
- DevOps Engineer
- AI Developer / AI Engineer
- LLM Engineer
- Agentic Workflow Engineer
- Automation Engineer (LLM-powered)
"""

# Compact profile for cover letters
CANDIDATE_PROFILE_COMPACT = """
Candidate: Suraj Kushwaha, Senior Backend Engineer
- 4+ years at CultureX Entertainment (B2B SaaS, Influencer Marketing)
- Core Stack: Node.js, TypeScript, GraphQL, Golang, JavaScript
- Backend: Express.js, Hono, MongoDB, PostgreSQL, MySQL, Redis, Microservices
- Cloud: AWS (Lambda, SQS, SNS, EventBridge, S3, EC2), Docker, CI/CD
- AI/LLM: LangChain, LangGraph, Agentic Workflows, RAG, Vector Databases
- Led zero-downtime migration for 50+ global brands
- Architected event-driven systems handling 100M+ monthly requests
- Built 40+ MVPs, owns public-facing API products
- Remote/Async native, strong written communication
"""
