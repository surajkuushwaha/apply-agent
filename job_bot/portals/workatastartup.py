"""
Work at a Startup (Y Combinator) job portal handler.

Handles WorkAtAStartup-specific:
- YC startup ecosystem
- Weekly application limits
- Simpler application flow
"""

from .base import BasePortal
from ..config import (
    WORKATASTARTUP_USER,
    WORKATASTARTUP_PASS,
    CANDIDATE_PROFILE,
    MIN_JOB_SCORE,
    RESUME_PATH,
)
from ..tracking import get_rate_limit_status


class WorkAtAStartupPortal(BasePortal):
    """Work at a Startup (YC) job portal handler."""

    name = "Work at a Startup"
    key = "workatastartup"
    base_url = "https://www.workatastartup.com/"
    login_url = "https://www.workatastartup.com/users/sign_in"

    needs_login = True
    username = WORKATASTARTUP_USER
    password = WORKATASTARTUP_PASS

    rate_limit_type = "weekly"
    rate_limit = 5

    # Search filters for UI-based filtering
    search_filters = "Backend Engineer, Software Engineer, Platform Engineer, AI Developer, AI Engineer, LLM Engineer"

    def build_search_url(self, keywords: str = None, **kwargs) -> str:
        """
        Build WorkAtAStartup search URL.

        Note: WaaS uses UI-based filtering, so we just return the base URL.
        Filters are applied through the UI by the agent.
        """
        # WaaS doesn't support URL-based filtering
        return self.base_url

    def get_rate_limit_warning(self) -> str:
        """Get a warning about weekly application limits."""
        status = get_rate_limit_status(self.key)
        if status["remaining"] <= 2:
            return f"""
⚠️ WEEKLY LIMIT WARNING:
- Used: {status['used']}/{status['limit']} applications
- Remaining: {status['remaining']}
- {status['reset_info']}
- Apply carefully - you have limited applications left!"""
        return ""

    def build_search_task(self, require_salary_range: bool = False) -> str:
        """Build the task prompt for searching jobs on Work at a Startup."""
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

1. Navigate to {self.base_url}
{self.get_login_instructions()}

2. Apply filters using the UI:
   - Click on filter options
   - Select "Remote only" if available
   - Filter by company stage: Seed, Series A, Series B
   - Filter by roles: {self.search_filters}
   - PRIORITIZE roles mentioning: LangChain, agentic workflows, automated workflows with LLMs

3. For each job found (up to 20 jobs):
   - Click to view full details
   {"   - CHECK: Verify salary range is visible before proceeding" if require_salary_range else ""}
   - Use calculate_match_score tool to check job score
   - Extract job information

{self.get_search_result_format()}

WORKATASTARTUP-SPECIFIC NOTES:
- All companies are YC-backed startups
- Look for batch information (e.g., W23, S22) - indicates YC cohort
- Check for funding stage (Seed, Series A, B)
- Note if company is actively hiring vs. just listing
- Some jobs show "Quick Apply" - prefer these
{self.get_rate_limit_warning()}

IMPORTANT:
- Use calculate_match_score for each job
- Only list jobs scoring >= {MIN_JOB_SCORE}
{"- ONLY list jobs that have a visible salary range" if require_salary_range else ""}
- List up to 20 matching jobs
- Skip jobs already in the applied list
"""

    def build_apply_task(
        self,
        job_number: int,
        total_jobs: int,
        require_salary_range: bool = False
    ) -> str:
        """Build the task prompt for applying to jobs on Work at a Startup."""
        rate_status = get_rate_limit_status(self.key)

        # Check if we can even apply
        if not rate_status["can_apply"]:
            return f"""
TASK ABORTED: Weekly application limit reached on {self.name}

You have used all {rate_status['limit']} applications for this week.
{rate_status['reset_info']}

Please try again after the limit resets.
"""

        return f"""
TASK: Apply to job {job_number} of {total_jobs} on {self.name}

{CANDIDATE_PROFILE}

ALREADY APPLIED (DO NOT APPLY TO THESE AGAIN):
{self.get_applied_jobs_str()}

BLACKLISTED COMPANIES (SKIP THESE):
{self.get_blacklist_str()}
{self.get_salary_filter_note(require_salary_range)}

{self.get_scoring_criteria_str()}
{self.get_rate_limit_warning()}

STEPS:

1. Navigate to {self.base_url}
{self.get_login_instructions()}

2. Apply filters using the UI:
   - Click on filter options
   - Select "Remote only" if available
   - Filter by company stage: Seed, Series A, Series B
   - Filter by roles: {self.search_filters}

3. Find and evaluate a job:
   - Use calculate_match_score tool to check job score
   - Only apply if score >= {MIN_JOB_SCORE}
   {"   - ONLY apply to jobs with visible salary range" if require_salary_range else ""}
   - Skip blacklisted companies
   - Skip already-applied jobs

4. Apply to the selected job:
   - Click on the job to view details
   - Click "Apply" or "Quick Apply" button
   - Use generate_cover_letter tool if cover letter is needed
   - Upload resume if file upload is available (path: {RESUME_PATH})
   - Fill all required fields using candidate profile
   - Submit application

{self.get_apply_result_format()}

WORKATASTARTUP-SPECIFIC NOTES:
- Weekly limit: {rate_status['remaining']}/{rate_status['limit']} applications remaining
- {rate_status['reset_info']}
- All companies are YC-backed startups
- Application process is usually simpler than LinkedIn
- Cover letter is often required - use generate_cover_letter
- Some companies may have custom questions
- Be aware of the weekly limit - apply to best matches first!

IMPORTANT:
- Use calculate_match_score before applying
- Use generate_cover_letter when a cover letter field exists
- If application fails, try the next matching job
{"- ONLY apply to jobs with visible salary range" if require_salary_range else ""}
- If you see "Application limit reached", report it immediately
"""

    def parse_job_result(self, result: str) -> dict:
        """Parse WorkAtAStartup-specific job result format."""
        job_info = self.parse_result_common(result)
        job_info["portal"] = self.key

        # Extract YC batch if present
        if result:
            import re
            batch_match = re.search(r'\(([WS]\d{2})\)', result)
            if batch_match:
                job_info["yc_batch"] = batch_match.group(1)

        return job_info
