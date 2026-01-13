"""
Configuration file for Daily Job Application Bot

Edit this file to customize:
- Job portals and credentials
- Keyword scoring weights
- Company blacklist/whitelist
- Portal allocation
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# PATHS
# =============================================================================

RESUME_PATH = Path("/Users/suraj/Personal/projects/browser-use/Suraj_Kushwaha_v1.pdf")
APPLIED_JOBS_FILE = Path("applied_jobs.json")

# =============================================================================
# APPLICATION SETTINGS
# =============================================================================

JOBS_TO_APPLY = 5
MIN_JOB_SCORE = 30  # Minimum score (0-100) to apply to a job

# =============================================================================
# COMPANY FILTERS
# =============================================================================

# Companies to never apply to
BLACKLIST_COMPANIES = [
    # "Company Name",
]

# Companies to prioritize (future feature)
WHITELIST_COMPANIES = [
    # "Dream Company",
]

# =============================================================================
# KEYWORD SCORING
# =============================================================================

# Keywords that MUST appear for high score (+8 points each)
REQUIRED_KEYWORDS = [
    "backend",
    "node",
    "nodejs",
    "typescript",
    "aws",
    "golang",
    "go",
    "graphql",
    "devops",
    "platform",
    "api",
]

# Nice-to-have keywords (+4 points each)
BONUS_KEYWORDS = [
    "remote",
    "microservices",
    "saas",
    "startup",
    "series a",
    "series b",
    "mongodb",
    "postgresql",
    "redis",
    "docker",
    "kubernetes",
    "lambda",
    "event-driven",
    "distributed",
]

# Experience level keywords (+10 points if any match)
EXPERIENCE_KEYWORDS = [
    "2-4 years",
    "2+ years",
    "3+ years",
    "4+ years",
    "mid-level",
    "senior",
]

# =============================================================================
# PORTAL CREDENTIALS
# =============================================================================

CREDENTIALS = {
    "workatastartup": {
        "username": os.getenv("WORKATASTARTUP_USER", "surajkuushwaha"),
        "password": os.getenv("WORKATASTARTUP_PASS", "Suraj@9106"),
    },
    "linkedin": {
        "username": os.getenv("LINKEDIN_USER", ""),
        "password": os.getenv("LINKEDIN_PASS", ""),
    },
    "wellfound": {
        "username": os.getenv("WELLFOUND_USER", ""),
        "password": os.getenv("WELLFOUND_PASS", ""),
    },
    "indeed": {
        "username": os.getenv("INDEED_USER", ""),
        "password": os.getenv("INDEED_PASS", ""),
    },
}

# =============================================================================
# PORTAL CONFIGURATION
# =============================================================================

JOB_PORTALS = {
    "workatastartup": {
        "name": "Work at a Startup",
        "url": "https://www.workatastartup.com/",
        "login_url": "https://www.workatastartup.com/users/sign_in",
        "search_filters": "Backend Engineer, Software Engineer, Platform Engineer",
        "needs_login": True,
        "enabled": True,
    },
    "linkedin": {
        "name": "LinkedIn",
        "url": "https://www.linkedin.com/jobs/",
        "login_url": "https://www.linkedin.com/login",
        "search_filters": "Backend Engineer Node.js TypeScript Remote",
        "needs_login": True,
        "enabled": True,
    },
    "wellfound": {
        "name": "Wellfound (AngelList)",
        "url": "https://wellfound.com/jobs",
        "login_url": "https://wellfound.com/login",
        "search_filters": "Backend Engineer, 2-5 years experience",
        "needs_login": True,
        "enabled": False,  # Enable when credentials are added
    },
    "indeed": {
        "name": "Indeed",
        "url": "https://www.indeed.com/",
        "login_url": None,
        "search_filters": "Backend Engineer Node.js Remote",
        "needs_login": False,
        "enabled": False,  # Enable for testing
    },
}

# =============================================================================
# PORTAL ALLOCATION
# How many jobs to apply to on each portal (total = JOBS_TO_APPLY)
# =============================================================================

PORTAL_ALLOCATION = {
    "workatastartup": 3,
    "linkedin": 2,
    "wellfound": 0,
    "indeed": 0,
}

# =============================================================================
# CANDIDATE PROFILE
# =============================================================================

CANDIDATE_NAME = "Suraj Kushwaha"
CANDIDATE_EMAIL = "jobs@surajkuushwaha.com"
CANDIDATE_PHONE = "+91 91067 64917"
CANDIDATE_GITHUB = "github.com/surajkuushwaha"
CANDIDATE_LINKEDIN = "linkedin.com/in/surajkuushwaha"

CANDIDATE_TITLE = "Senior Backend Engineer | Product & Extensibility Platforms"
CANDIDATE_EXPERIENCE = "4+ years"
CANDIDATE_CURRENT_COMPANY = "CultureX Entertainment"

CANDIDATE_SKILLS = {
    "languages": ["Node.js", "TypeScript", "GraphQL", "JavaScript (ES6+)", "Golang"],
    "backend": ["Express.js", "Hono", "MongoDB", "PostgreSQL", "MySQL", "Redis", "Microservices"],
    "cloud": ["AWS Lambda", "SQS", "SNS", "EventBridge", "S3", "EC2", "Docker", "CI/CD"],
    "tools": ["Git", "Linux", "Tmux", "GitHub Actions"],
}

CANDIDATE_ACHIEVEMENTS = [
    "Owned public-facing API microservice (internal tool → high-availability product)",
    "Led zero-downtime migration to unified SaaS for 30+ global brands",
    "Architected event-driven systems handling 10M+ monthly requests",
    "Scaled backend infrastructure, reducing debugging effort by 40%",
    "Developed 10+ MVPs for influencer marketing platform",
]

TARGET_ROLES = [
    "Senior Backend Engineer",
    "Backend Engineer",
    "Platform Engineer",
    "API/Extensibility Engineer",
    "DevOps Engineer",
]

# =============================================================================
# TIMING SETTINGS
# =============================================================================

DELAY_BETWEEN_APPLICATIONS = 5  # seconds
DELAY_LINKEDIN = 10  # LinkedIn needs longer delays
MAX_STEPS_PER_APPLICATION = 60
