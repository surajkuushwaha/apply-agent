"""
Job scoring logic for matching candidates to job postings.

Calculates a score based on keyword matches, experience level, and other factors.
Uses negative keywords to filter out irrelevant jobs.
"""

from .config import (
    BLACKLIST_COMPANIES,
    REQUIRED_KEYWORDS,
    BONUS_KEYWORDS,
    NEGATIVE_KEYWORDS,
    REQUIRED_KEYWORD_SCORE,
    BONUS_KEYWORD_SCORE,
    EXPERIENCE_MATCH_SCORE,
    REMOTE_BONUS_SCORE,
    NEGATIVE_KEYWORD_PENALTY,
    MIN_JOB_SCORE,
)


def calculate_job_score(job_title: str, company: str, description: str) -> int:
    """
    Score job based on match with candidate profile (0-100).

    Returns:
        int: Score from 0-100, or -1 for blacklisted companies,
             or negative score for jobs with negative keywords.
    """
    # Check blacklist
    if company.lower() in [c.lower() for c in BLACKLIST_COMPANIES]:
        return -1

    score = 0
    text = f"{job_title} {description}".lower()

    # Check for negative keywords first (auto-skip)
    for keyword in NEGATIVE_KEYWORDS:
        if keyword.lower() in text:
            score += NEGATIVE_KEYWORD_PENALTY
            # Don't return immediately - accumulate penalties
            # This helps identify jobs that match multiple negative criteria

    # Required skills match (+8 each, max ~88)
    for keyword in REQUIRED_KEYWORDS:
        if keyword.lower() in text:
            score += REQUIRED_KEYWORD_SCORE

    # Bonus keywords (+4 each)
    for keyword in BONUS_KEYWORDS:
        if keyword.lower() in text:
            score += BONUS_KEYWORD_SCORE

    # Experience level match
    experience_patterns = [
        "2-4 years", "2+ years", "3+ years", "4+ years",
        "mid-level", "mid level", "senior", "staff"
    ]
    if any(pattern in text for pattern in experience_patterns):
        score += EXPERIENCE_MATCH_SCORE

    # Remote preference
    if "remote" in text:
        score += REMOTE_BONUS_SCORE

    return min(max(score, -100), 100)


def should_apply(score: int) -> bool:
    """Determine if we should apply based on score."""
    return score >= MIN_JOB_SCORE


def get_score_recommendation(score: int) -> str:
    """Get a human-readable recommendation based on score."""
    if score == -1:
        return "SKIP (blacklisted company)"
    elif score < 0:
        return f"SKIP (negative keywords, score: {score})"
    elif score < MIN_JOB_SCORE:
        return f"SKIP (score {score} < min {MIN_JOB_SCORE})"
    elif score < 50:
        return f"MAYBE (score: {score})"
    elif score < 70:
        return f"GOOD MATCH (score: {score})"
    else:
        return f"EXCELLENT MATCH (score: {score})"


def analyze_job(job_title: str, company: str, description: str) -> dict:
    """
    Perform detailed analysis of a job posting.

    Returns a dict with score, recommendation, matched keywords, and rejection_reason.
    """
    text = f"{job_title} {description}".lower()

    matched_required = [kw for kw in REQUIRED_KEYWORDS if kw.lower() in text]
    matched_bonus = [kw for kw in BONUS_KEYWORDS if kw.lower() in text]
    matched_negative = [kw for kw in NEGATIVE_KEYWORDS if kw.lower() in text]

    score = calculate_job_score(job_title, company, description)
    is_blacklisted = company.lower() in [c.lower() for c in BLACKLIST_COMPANIES]

    # Determine rejection reason
    if is_blacklisted or score == -1:
        rejection_reason = "blacklisted_company"
    elif score < 0:
        rejection_reason = "negative_keywords"
    elif score < MIN_JOB_SCORE:
        rejection_reason = "score_too_low"
    else:
        rejection_reason = "passed"

    return {
        "score": score,
        "recommendation": get_score_recommendation(score),
        "should_apply": should_apply(score),
        "matched_required": matched_required,
        "matched_bonus": matched_bonus,
        "matched_negative": matched_negative,
        "is_blacklisted": is_blacklisted,
        "rejection_reason": rejection_reason,
    }
