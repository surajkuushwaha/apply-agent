"""
Abstract base class for job portal handlers.

All portal implementations must inherit from BasePortal and implement
the required abstract methods.
"""

from abc import ABC, abstractmethod
from typing import Optional

from ..config import (
    CANDIDATE_PROFILE,
    REQUIRED_KEYWORDS,
    BONUS_KEYWORDS,
    BLACKLIST_COMPANIES,
    MIN_JOB_SCORE,
    RESUME_PATH,
)
from ..tracking import get_applied_job_identifiers


class BasePortal(ABC):
    """
    Abstract base class for job portal handlers.

    Each portal (LinkedIn, WorkAtAStartup, etc.) should implement this interface.
    """

    # Portal identification
    name: str = "Base Portal"
    key: str = "base"

    # URLs
    base_url: str = ""
    login_url: str = ""

    # Authentication
    needs_login: bool = True
    username: str = ""
    password: str = ""

    # Rate limits
    rate_limit_type: str = "daily"  # "daily" or "weekly"
    rate_limit: int = 25

    @abstractmethod
    def build_search_url(self, keywords: str, **kwargs) -> str:
        """
        Build portal-specific search URL with filters.

        Args:
            keywords: Search keywords
            **kwargs: Portal-specific parameters (e.g., freshness for LinkedIn)

        Returns:
            str: Full URL for job search
        """
        pass

    @abstractmethod
    def build_search_task(self, require_salary_range: bool = False) -> str:
        """
        Build the prompt for searching jobs on this portal.

        Args:
            require_salary_range: Whether to only show jobs with salary info

        Returns:
            str: Full task prompt for the browser agent
        """
        pass

    @abstractmethod
    def build_apply_task(
        self,
        job_number: int,
        total_jobs: int,
        require_salary_range: bool = False
    ) -> str:
        """
        Build the prompt for applying to jobs on this portal.

        Args:
            job_number: Current job number (1-indexed)
            total_jobs: Total jobs to apply to
            require_salary_range: Whether to only apply to jobs with salary info

        Returns:
            str: Full task prompt for the browser agent
        """
        pass

    @abstractmethod
    def parse_job_result(self, result: str) -> dict:
        """
        Parse portal-specific job result format.

        Args:
            result: Raw result string from the browser agent

        Returns:
            dict: Parsed job information
        """
        pass

    def get_login_instructions(self) -> str:
        """Get login instructions for the portal."""
        if not self.needs_login or not self.username:
            return ""

        return f"""
   - Click "Log in" or "Sign in"
   - Enter Email/Username: {self.username}
   - Enter Password: {self.password}
   - Submit and wait for dashboard"""

    def get_applied_jobs_str(self, limit: int = 30) -> str:
        """Get formatted string of already applied jobs."""
        applied = get_applied_job_identifiers()[-limit:]
        if not applied:
            return "  None yet"
        return "\n".join(f"  - {job}" for job in applied)

    def get_blacklist_str(self) -> str:
        """Get formatted string of blacklisted companies."""
        if not BLACKLIST_COMPANIES:
            return "None"
        return ", ".join(BLACKLIST_COMPANIES)

    def get_salary_filter_note(self, require_salary_range: bool) -> str:
        """Get salary range filter note if enabled."""
        if not require_salary_range:
            return ""

        return """
SALARY RANGE FILTER (REQUIRED):
- ONLY consider jobs that have a visible salary range
- Skip any jobs where salary information is "Not specified" or not visible
- This is a mandatory filter - do not list jobs without salary information"""

    def get_scoring_criteria_str(self) -> str:
        """Get formatted string of scoring criteria."""
        return f"""
JOB SCORING CRITERIA:
- Required keywords (+8 each): {", ".join(REQUIRED_KEYWORDS)}
- Bonus keywords (+4 each): {", ".join(BONUS_KEYWORDS)}
- Experience match: +10 for 2-4 years, mid-level, senior
- Remote: +5 bonus
- Minimum score to apply: {MIN_JOB_SCORE}"""

    def get_search_result_format(self) -> str:
        """Get the expected format for search results."""
        return f"""
4. Return this EXACT format for each job found:
   ---JOB_FOUND---
   Portal: {self.key}
   Company: [company name]
   Title: [job title]
   URL: [job url]
   Score: [calculated score]
   TechStack: [comma-separated tech mentioned]
   SalaryRange: [if visible, else "Not specified"]
   Remote: [yes/no/not specified]
   Experience: [required experience level]
   ---END---"""

    def get_apply_result_format(self) -> str:
        """Get the expected format for application results."""
        return f"""
5. Return this EXACT format after applying:
   ---JOB_APPLIED---
   Portal: {self.key}
   Company: [company name]
   Title: [job title]
   URL: [job url]
   Score: [calculated score]
   Status: [success/failed]
   CoverLetterUsed: [true/false]
   ResumeUploaded: [true/false]
   TechStack: [comma-separated tech mentioned]
   SalaryRange: [if visible, else "Not specified"]
   Notes: [any relevant notes]
   ---END---"""

    def parse_result_common(self, result: str, marker: str = "---JOB_APPLIED---") -> dict:
        """
        Parse common result format used by all portals.

        Args:
            result: Raw result string
            marker: Start marker (---JOB_APPLIED--- or ---JOB_FOUND---)

        Returns:
            dict: Parsed job information
        """
        job_info = {}

        if not result:
            return job_info

        result_str = str(result)
        field_mappings = {
            "Portal:": "portal",
            "Company:": "company",
            "Title:": "title",
            "URL:": "url",
            "Score:": "score",
            "Status:": "status",
            "CoverLetterUsed:": "cover_letter_used",
            "ResumeUploaded:": "resume_uploaded",
            "TechStack:": "tech_stack",
            "SalaryRange:": "salary_range",
            "Remote:": "remote",
            "Experience:": "experience",
            "Notes:": "notes",
        }

        for line in result_str.split("\n"):
            line = line.strip()
            for prefix, key in field_mappings.items():
                if line.startswith(prefix):
                    value = line.replace(prefix, "").strip()
                    if key == "score":
                        try:
                            job_info[key] = int(value.split("/")[0])
                        except (ValueError, IndexError):
                            job_info[key] = 0
                    elif key in ["cover_letter_used", "resume_uploaded"]:
                        job_info[key] = value.lower() == "true"
                    elif key == "tech_stack":
                        job_info[key] = [t.strip() for t in value.split(",")]
                    else:
                        job_info[key] = value

        return job_info
