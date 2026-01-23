"""
Custom browser_use tools for the Job Application Bot.

Provides tools that the browser automation agent can use during job applications.
"""

from browser_use import Tools, ActionResult

from .config import MIN_JOB_SCORE
from .scoring import calculate_job_score, get_score_recommendation, analyze_job
from .cover_letter import generate_cover_letter


def create_tools() -> Tools:
    """
    Create and return configured Tools instance for browser_use.

    Returns a Tools object with all custom actions registered.
    """
    tools = Tools()

    @tools.action('Generate a tailored cover letter for the job application')
    def generate_cover_letter_action(job_title: str, company: str, job_description: str) -> str:
        """Generate a personalized cover letter using the candidate profile."""
        cover_letter, method = generate_cover_letter(job_title, company, job_description)
        return f"[Generated via {method}]\n\n{cover_letter}"

    @tools.action('Calculate job match score based on requirements')
    def calculate_match_score(job_title: str, job_description: str, company: str) -> ActionResult:
        """Calculate how well a job matches the candidate profile."""
        score = calculate_job_score(job_title, company, job_description)

        if score == -1:
            return ActionResult(
                extracted_content=f"SKIP: {company} is in the blacklist",
                is_done=False
            )

        if score < 0:
            return ActionResult(
                extracted_content=f"SKIP: Score {score} (contains negative keywords)",
                is_done=False
            )

        recommendation = "APPLY" if score >= MIN_JOB_SCORE else "SKIP"

        return ActionResult(
            extracted_content=f"Score: {score}/100 - {recommendation}",
            long_term_memory=f"Job at {company} scored {score}/100"
        )

    @tools.action('Analyze a job posting in detail')
    def analyze_job_action(job_title: str, job_description: str, company: str) -> ActionResult:
        """Perform detailed analysis of a job posting."""
        analysis = analyze_job(job_title, company, job_description)

        result_lines = [
            f"Score: {analysis['score']}/100",
            f"Recommendation: {analysis['recommendation']}",
            f"Should Apply: {'Yes' if analysis['should_apply'] else 'No'}",
            "",
            f"Matched Required Keywords: {', '.join(analysis['matched_required']) or 'None'}",
            f"Matched Bonus Keywords: {', '.join(analysis['matched_bonus']) or 'None'}",
        ]

        if analysis['matched_negative']:
            result_lines.append(
                f"WARNING - Negative Keywords Found: {', '.join(analysis['matched_negative'])}"
            )

        if analysis['is_blacklisted']:
            result_lines.append("WARNING: Company is blacklisted!")

        return ActionResult(
            extracted_content="\n".join(result_lines),
            long_term_memory=f"Analyzed {company}: {analysis['recommendation']}"
        )

    return tools


# Singleton instance for convenience
tools = create_tools()
