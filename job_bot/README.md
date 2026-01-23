# Job Application Bot v2.0

Automated job application bot with multi-portal support, built on [browser-use](https://github.com/browser-use/browser-use).

## Features

- **Multi-Portal Support**: LinkedIn and Work at a Startup (Y Combinator), extensible for more
- **Smart Job Scoring**: Automatic scoring based on keywords, experience level, and preferences
- **Negative Keywords**: Auto-skip irrelevant jobs (frontend, QA, manager roles, etc.)
- **LinkedIn Freshness Filter**: Target jobs posted in the last hour for first-mover advantage
- **Rate Limit Tracking**: Respects portal limits (LinkedIn daily, WaaS weekly)
- **Cover Letter Generation**: AI-powered (Gemini) with template fallbacks
- **Dry-Run Mode**: Test the flow without actually applying
- **Persistent Browser Sessions**: Stay logged in across runs

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your credentials
```

## Usage

### Run the CLI

```bash
# Recommended (as module)
python -m job_bot

# Or direct execution
python job_bot/main.py
```

This launches an interactive menu where you can:
1. **Search for jobs** - Browse and list matching jobs without applying
2. **Apply to jobs** - Automatically apply to matching jobs
3. **View stats** - See application history and rate limits

### Command Line Options

The CLI will prompt you for:
- **Portal selection**: LinkedIn, Work at a Startup, or both
- **LinkedIn freshness**: 1 hour, 24 hours (default), 7 days, or 30 days
- **Salary filter**: Only show jobs with visible salary range
- **Dry-run mode**: Simulate without actually applying

### Programmatic Usage

```python
import asyncio
from job_bot.main import search_jobs_multi_portal, apply_multi_portal

# Search for jobs
jobs = asyncio.run(search_jobs_multi_portal(
    require_salary_range=False,
    freshness="24h",
    dry_run=True
))

# Apply to jobs
results = asyncio.run(apply_multi_portal(
    require_salary_range=False,
    freshness="1h",  # First-mover advantage
    dry_run=False
))
```

## Configuration

Edit `job_bot/config.py` to customize:

### Keywords

```python
# Jobs must match these (+8 points each)
REQUIRED_KEYWORDS = ["backend", "node", "typescript", "aws", ...]

# Nice to have (+4 points each)
BONUS_KEYWORDS = ["remote", "startup", "microservices", ...]

# Auto-skip jobs containing these (-50 points)
NEGATIVE_KEYWORDS = ["frontend", "ios", "qa engineer", "manager", ...]
```

### Rate Limits

```python
RATE_LIMITS = {
    "linkedin": {"type": "daily", "limit": 25},
    "workatastartup": {"type": "weekly", "limit": 5},
}
```

### Portal Allocation

```python
# How many jobs to apply to per portal
PORTAL_ALLOCATION = {
    "linkedin": 3,
    "workatastartup": 2,
}
```

### LinkedIn Freshness

```python
LINKEDIN_FRESHNESS = {
    "1h": "r3600",      # Past hour (first-mover advantage)
    "24h": "r86400",    # Past 24 hours (default)
    "7d": "r604800",    # Past week
    "30d": "r2592000",  # Past month
}
```

## Project Structure

```
job_bot/
├── __init__.py           # Package exports
├── __main__.py           # python -m job_bot entry point
├── main.py               # CLI menu and main functions
├── config.py             # All configuration settings
├── scoring.py            # Job scoring with negative keywords
├── tracking.py           # applied_jobs_v2.json + rate limits
├── cover_letter.py       # AI generation + template fallbacks
├── tools.py              # browser_use custom tools
│
└── portals/
    ├── __init__.py       # Portal registry
    ├── base.py           # Abstract base class
    ├── linkedin.py       # LinkedIn handler
    └── workatastartup.py # WaaS handler
```

## Adding a New Portal

1. Create `job_bot/portals/yourportal.py`:

```python
from .base import BasePortal

class YourPortal(BasePortal):
    name = "Your Portal"
    key = "yourportal"
    base_url = "https://yourportal.com/jobs"

    def build_search_url(self, keywords, **kwargs):
        # Build portal-specific search URL
        pass

    def build_search_task(self, require_salary_range=False):
        # Build search prompt for browser agent
        pass

    def build_apply_task(self, job_number, total_jobs, require_salary_range=False):
        # Build apply prompt for browser agent
        pass

    def parse_job_result(self, result):
        # Parse portal-specific result format
        pass
```

2. Register in `job_bot/portals/__init__.py`:

```python
from .yourportal import YourPortal

PORTAL_REGISTRY = {
    "linkedin": LinkedInPortal,
    "workatastartup": WorkAtAStartupPortal,
    "yourportal": YourPortal,  # Add here
}
```

3. Add rate limits in `job_bot/config.py`:

```python
RATE_LIMITS = {
    # ...
    "yourportal": {"type": "daily", "limit": 10, "delay_seconds": 5},
}
```

## Tracking Data

Applications are tracked in `applied_jobs_v2.json`:

```json
{
  "jobs": [...],
  "stats": {
    "total_applied": 42,
    "by_portal": {"linkedin": 30, "workatastartup": 12},
    "by_status": {"success": 38, "failed": 4},
    "avg_score": 67.5
  },
  "rate_limits": {
    "linkedin": {"daily_used": 5, "last_date": "2026-01-24"},
    "workatastartup": {"weekly_used": 3, "week_start": "2026-01-20"}
  }
}
```

## Cover Letter Templates

When Gemini AI fails, the bot falls back to role-specific templates:

- `backend` - Backend/Node.js/TypeScript focused
- `ai_engineer` - AI/LLM/LangChain focused
- `platform` - Platform/API/Infrastructure focused
- `devops` - DevOps/SRE/Cloud focused
- `default` - General software engineering

Templates are in `job_bot/cover_letter.py`.

## Environment Variables

Create a `.env` file:

```bash
# Required for browser agent
GOOGLE_API_KEY=your_gemini_api_key

# LinkedIn credentials
LINKEDIN_USER=your_email
LINKEDIN_PASS=your_password

# Work at a Startup credentials
WORKATASTARTUP_USER=your_email
WORKATASTARTUP_PASS=your_password
```

## Tips

1. **Use freshness filters**: Set LinkedIn to "1h" to be among the first applicants
2. **Enable dry-run first**: Test your configuration before real applications
3. **Monitor rate limits**: The bot tracks and respects portal limits
4. **Customize negative keywords**: Add roles you want to skip
5. **Check tracking file**: Review `applied_jobs_v2.json` for your history
