"""
LinkedIn job portal handler.

Handles LinkedIn-specific:
- URL building with freshness filters
- Easy Apply detection
- Application flow
"""

from urllib.parse import urlencode

from .base import BasePortal
from ..config import (
    LINKEDIN_USER,
    LINKEDIN_PASS,
    LINKEDIN_FRESHNESS,
    DEFAULT_LINKEDIN_FRESHNESS,
    CANDIDATE_PROFILE,
    MIN_JOB_SCORE,
    RESUME_PATH,
)


class LinkedInPortal(BasePortal):
    """LinkedIn job portal handler."""

    name = "LinkedIn"
    key = "linkedin"
    base_url = "https://www.linkedin.com/jobs/search/"
    login_url = "https://www.linkedin.com/login"

    needs_login = True
    username = LINKEDIN_USER
    password = LINKEDIN_PASS

    rate_limit_type = "daily"
    rate_limit = 25

    # LinkedIn search filters
    search_keywords = "Backend Engineer Node.js TypeScript Remote AI Developer LangChain Agentic Workflows"

    def build_search_url(
        self,
        keywords: str = None,
        freshness: str = None,
        remote_only: bool = True,
        experience_level: str = "3,4",  # Mid-Senior level
        sort_by: str = "DD",  # Date Descending
    ) -> str:
        """
        Build LinkedIn search URL with filters.

        Args:
            keywords: Search keywords (defaults to self.search_keywords)
            freshness: Time filter key ("1h", "24h", "7d", "30d")
            remote_only: Filter for remote jobs only
            experience_level: Experience level filter (1=Entry, 2=Associate, 3=Mid, 4=Senior, 5=Director, 6=Executive)
            sort_by: Sort order ("DD"=Date, "R"=Relevance)

        Returns:
            str: Full LinkedIn search URL
        """
        if keywords is None:
            keywords = self.search_keywords

        if freshness is None:
            freshness = DEFAULT_LINKEDIN_FRESHNESS

        params = {
            "keywords": keywords,
            "f_TPR": LINKEDIN_FRESHNESS.get(freshness, "r86400"),
            "sortBy": sort_by,
        }

        if remote_only:
            params["f_WT"] = "2"  # Remote

        if experience_level:
            params["f_E"] = experience_level

        return f"{self.base_url}?{urlencode(params)}"

    def build_search_task(self, require_salary_range: bool = False, freshness: str = None) -> str:
        """Build the task prompt for searching jobs on LinkedIn."""
        search_url = self.build_search_url(freshness=freshness)

        return f"""
TASK: Search and list matching jobs on {self.name}

{CANDIDATE_PROFILE}

ALREADY APPLIED (DO NOT LIST THESE):
{self.get_applied_jobs_str()}

BLACKLISTED COMPANIES (SKIP THESE):
{self.get_blacklist_str()}
{self.get_salary_filter_note(require_salary_range)}

{self.get_scoring_criteria_str()}

STEPS:

1. Navigate to {search_url}
{self.get_login_instructions()}

2. The URL already includes these filters:
   - Time posted: Last 24 hours (configurable)
   - Remote only
   - Mid-Senior level experience
   - Sorted by date (newest first)

3. For each job found (up to 20 jobs):
   - Click to view full details
   {"   - CHECK: Verify salary range is visible before proceeding" if require_salary_range else ""}
   - Use calculate_match_score tool to check job score
   - Note if "Easy Apply" button is present (preferred)
   - Extract job information

{self.get_search_result_format()}

LINKEDIN-SPECIFIC NOTES:
- Prefer "Easy Apply" jobs (faster application process)
- Check if job requires external application
- Note any application questions visible
- Skip "Promoted" listings if possible (usually lower quality)
- Skip jobs already in the applied list

IMPORTANT:
- Use calculate_match_score for each job
- Only list jobs scoring >= {MIN_JOB_SCORE}
{"- ONLY list jobs that have a visible salary range" if require_salary_range else ""}
- List up to 20 matching jobs
"""

    def build_apply_task(
        self,
        job_number: int,
        total_jobs: int,
        require_salary_range: bool = False,
        freshness: str = None
    ) -> str:
        """Build the task prompt for applying to jobs on LinkedIn."""
        search_url = self.build_search_url(freshness=freshness)

        return f"""
TASK: Apply to job {job_number} of {total_jobs} on {self.name}

{CANDIDATE_PROFILE}

ALREADY APPLIED (DO NOT APPLY TO THESE AGAIN):
{self.get_applied_jobs_str()}

BLACKLISTED COMPANIES (SKIP THESE):
{self.get_blacklist_str()}
{self.get_salary_filter_note(require_salary_range)}

{self.get_scoring_criteria_str()}

STEPS:

1. Navigate to {search_url}
{self.get_login_instructions()}

2. The URL already includes filters. Find a matching job:
   - Look for "Easy Apply" jobs (preferred)
   - Use calculate_match_score tool to check job score
   - Only apply if score >= {MIN_JOB_SCORE}
   {"   - ONLY apply to jobs with visible salary range" if require_salary_range else ""}

3. Apply to the selected job:
   - Click "Easy Apply" if available
   - If external application, follow the link and complete there
   - Upload resume if prompted (path: {RESUME_PATH})
   - Use generate_cover_letter tool if cover letter is needed
   - Fill all required fields using candidate profile
   - Answer any screening questions appropriately
   - Submit application

{self.get_apply_result_format()}

LINKEDIN-SPECIFIC NOTES:
- "Easy Apply" is faster and preferred
- Some jobs redirect to company websites
- Watch for multi-step application forms
- Answer screening questions based on candidate profile:
  - Years of experience: 4+
  - Work authorization: Yes (for remote roles)
  - Willing to relocate: Depends on role (prefer remote)
- Skip jobs that require assessment tests

IMPORTANT:
- Use calculate_match_score before applying
- Use generate_cover_letter when a cover letter field exists
- If application fails, try the next matching job
{"- ONLY apply to jobs with visible salary range" if require_salary_range else ""}
"""

    def parse_job_result(self, result: str) -> dict:
        """Parse LinkedIn-specific job result format."""
        job_info = self.parse_result_common(result)
        job_info["portal"] = self.key

        # Add LinkedIn-specific fields if not present
        if "easy_apply" not in job_info:
            result_lower = result.lower() if result else ""
            job_info["easy_apply"] = "easy apply" in result_lower

        return job_info
