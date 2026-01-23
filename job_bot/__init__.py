"""
Job Application Bot - A modular job application automation system.

This package provides:
- Multi-portal job search and application
- LinkedIn and WorkAtAStartup support (extensible for more)
- Job scoring and filtering
- Cover letter generation with templates
- Rate limit tracking
- Dry-run mode for testing
"""

from .config import JOBS_TO_APPLY, MIN_JOB_SCORE, CANDIDATE_PROFILE
from .scoring import calculate_job_score
from .tracking import load_applied_jobs, save_applied_job
from .portals import LinkedInPortal, WorkAtAStartupPortal

__version__ = "2.0.0"
__all__ = [
    "JOBS_TO_APPLY",
    "MIN_JOB_SCORE",
    "CANDIDATE_PROFILE",
    "calculate_job_score",
    "load_applied_jobs",
    "save_applied_job",
    "LinkedInPortal",
    "WorkAtAStartupPortal",
]
