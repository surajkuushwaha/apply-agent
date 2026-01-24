"""
Job tracking and rate limit management.

Handles:
- Applied jobs JSON file management
- Rate limit tracking per portal
- Statistics and analytics
"""

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from .config import (
    APPLIED_JOBS_FILE,
    VIEWED_JOBS_FILE,
    SELECTED_JOBS_FILE,
    REJECTED_JOBS_FILE,
    RATE_LIMITS,
)


def load_applied_jobs() -> dict:
    """
    Load previously applied jobs from JSON file.

    Migrates old schema if needed and ensures rate_limits structure exists.
    """
    default_data = {
        "jobs": [],
        "stats": {
            "total_applied": 0,
            "by_portal": {},
            "by_status": {"success": 0, "failed": 0},
            "avg_score": 0
        },
        "rate_limits": {}
    }

    if not APPLIED_JOBS_FILE.exists():
        return default_data

    with open(APPLIED_JOBS_FILE, "r") as f:
        data = json.load(f)

    # Migrate old schema (has total_applied at root, no stats)
    if "stats" not in data:
        data["stats"] = {
            "total_applied": data.get("total_applied", len(data.get("jobs", []))),
            "by_portal": {},
            "by_status": {"success": 0, "failed": 0},
            "avg_score": 0
        }
        data.pop("total_applied", None)

    # Ensure rate_limits exists
    if "rate_limits" not in data:
        data["rate_limits"] = {}

    return data


def save_applied_jobs(data: dict):
    """Save the full applied jobs data to file."""
    with open(APPLIED_JOBS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def save_applied_job(job_info: dict):
    """
    Save newly applied job to tracking file with enhanced schema.

    Updates stats and rate limits automatically.
    """
    data = load_applied_jobs()

    # Add metadata
    job_info["id"] = str(uuid.uuid4())
    job_info["applied_at"] = datetime.now().isoformat()

    data["jobs"].append(job_info)

    # Update stats
    data["stats"]["total_applied"] = len(data["jobs"])

    portal = job_info.get("portal", "unknown")
    data["stats"]["by_portal"][portal] = data["stats"]["by_portal"].get(portal, 0) + 1

    status = job_info.get("status", "unknown")
    if status in ["success", "failed"]:
        data["stats"]["by_status"][status] = data["stats"]["by_status"].get(status, 0) + 1

    # Calculate average score
    scores = [j.get("score", 0) for j in data["jobs"] if j.get("score")]
    data["stats"]["avg_score"] = round(sum(scores) / len(scores), 1) if scores else 0

    # Update rate limits
    if status == "success":
        update_rate_limit(data, portal)

    save_applied_jobs(data)


def update_rate_limit(data: dict, portal: str):
    """Update rate limit counter for a portal after successful application."""
    today = datetime.now().date().isoformat()
    week_start = (datetime.now().date() - timedelta(days=datetime.now().weekday())).isoformat()

    if portal not in data["rate_limits"]:
        data["rate_limits"][portal] = {}

    portal_limits = data["rate_limits"][portal]
    rate_config = RATE_LIMITS.get(portal, {"type": "daily", "limit": 25})

    if rate_config["type"] == "daily":
        # Reset if new day
        if portal_limits.get("last_date") != today:
            portal_limits["daily_used"] = 0
            portal_limits["last_date"] = today
        portal_limits["daily_used"] = portal_limits.get("daily_used", 0) + 1

    elif rate_config["type"] == "weekly":
        # Reset if new week
        if portal_limits.get("week_start") != week_start:
            portal_limits["weekly_used"] = 0
            portal_limits["week_start"] = week_start
        portal_limits["weekly_used"] = portal_limits.get("weekly_used", 0) + 1


def get_rate_limit_status(portal: str) -> dict:
    """
    Get current rate limit status for a portal.

    Returns:
        dict: {used: int, limit: int, remaining: int, can_apply: bool, reset_info: str}
    """
    data = load_applied_jobs()
    rate_config = RATE_LIMITS.get(portal, {"type": "daily", "limit": 25})

    today = datetime.now().date().isoformat()
    week_start = (datetime.now().date() - timedelta(days=datetime.now().weekday())).isoformat()

    portal_limits = data.get("rate_limits", {}).get(portal, {})

    if rate_config["type"] == "daily":
        # Check if we need to reset (new day)
        if portal_limits.get("last_date") != today:
            used = 0
        else:
            used = portal_limits.get("daily_used", 0)
        limit = rate_config["limit"]
        reset_info = "Resets at midnight"

    elif rate_config["type"] == "weekly":
        # Check if we need to reset (new week)
        if portal_limits.get("week_start") != week_start:
            used = 0
        else:
            used = portal_limits.get("weekly_used", 0)
        limit = rate_config["limit"]
        days_until_reset = 7 - datetime.now().weekday()
        reset_info = f"Resets in {days_until_reset} day(s)"

    else:
        used = 0
        limit = 999
        reset_info = "No limit"

    remaining = max(0, limit - used)
    can_apply = remaining > 0

    return {
        "used": used,
        "limit": limit,
        "remaining": remaining,
        "can_apply": can_apply,
        "reset_info": reset_info,
        "type": rate_config["type"],
    }


def get_applied_job_identifiers() -> list:
    """Get list of already applied job identifiers (company - title - portal)."""
    data = load_applied_jobs()
    return [
        f"{j.get('company', '')} - {j.get('title', '')} ({j.get('portal', '')})"
        for j in data["jobs"]
    ]


def is_already_applied(company: str, title: str, portal: str) -> bool:
    """Check if we already applied to a specific job."""
    identifier = f"{company} - {title} ({portal})"
    return identifier in get_applied_job_identifiers()


def get_stats_summary() -> str:
    """Get a formatted summary of application statistics."""
    data = load_applied_jobs()
    stats = data["stats"]

    lines = [
        f"Total Applied: {stats['total_applied']}",
        f"Success Rate: {stats['by_status'].get('success', 0)}/{stats['total_applied']}",
        f"Average Score: {stats['avg_score']}",
        "",
        "By Portal:",
    ]

    for portal, count in stats.get("by_portal", {}).items():
        rate_status = get_rate_limit_status(portal)
        lines.append(
            f"  - {portal}: {count} total, "
            f"{rate_status['remaining']}/{rate_status['limit']} remaining "
            f"({rate_status['reset_info']})"
        )

    return "\n".join(lines)


# =============================================================================
# VIEWED JOBS TRACKING
# =============================================================================

def load_viewed_jobs() -> dict:
    """Load viewed jobs from JSON file."""
    default_data = {
        "jobs": [],
        "stats": {
            "total_viewed": 0,
            "by_portal": {},
        }
    }

    if not VIEWED_JOBS_FILE.exists():
        return default_data

    with open(VIEWED_JOBS_FILE, "r") as f:
        data = json.load(f)

    # Ensure stats structure exists
    if "stats" not in data:
        data["stats"] = {
            "total_viewed": len(data.get("jobs", [])),
            "by_portal": {},
        }

    return data


def save_viewed_jobs(data: dict):
    """Save the full viewed jobs data to file."""
    with open(VIEWED_JOBS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_viewed_job_identifiers() -> list:
    """Get list of already viewed job identifiers (company - title - portal)."""
    data = load_viewed_jobs()
    return [
        f"{j.get('company', '')} - {j.get('title', '')} ({j.get('portal', '')})"
        for j in data["jobs"]
    ]


def is_already_viewed(company: str, title: str, portal: str) -> bool:
    """Check if a job was already viewed."""
    identifier = f"{company} - {title} ({portal})"
    return identifier in get_viewed_job_identifiers()


def save_viewed_job(job_info: dict):
    """
    Save a viewed job to tracking file.

    Includes: portal, company, title, url, score, tech_stack, salary_range, remote, experience
    """
    # Check for duplicates
    company = job_info.get("company", "")
    title = job_info.get("title", "")
    portal = job_info.get("portal", "unknown")

    if is_already_viewed(company, title, portal):
        return  # Skip duplicates

    data = load_viewed_jobs()

    # Add metadata
    job_info["id"] = str(uuid.uuid4())
    job_info["viewed_at"] = datetime.now().isoformat()

    data["jobs"].append(job_info)

    # Update stats
    data["stats"]["total_viewed"] = len(data["jobs"])
    data["stats"]["by_portal"][portal] = data["stats"]["by_portal"].get(portal, 0) + 1

    save_viewed_jobs(data)


# =============================================================================
# SELECTED JOBS TRACKING
# =============================================================================

def load_selected_jobs() -> dict:
    """Load selected jobs from JSON file."""
    default_data = {
        "jobs": [],
        "stats": {
            "total_selected": 0,
            "by_portal": {},
        }
    }

    if not SELECTED_JOBS_FILE.exists():
        return default_data

    with open(SELECTED_JOBS_FILE, "r") as f:
        data = json.load(f)

    # Ensure stats structure exists
    if "stats" not in data:
        data["stats"] = {
            "total_selected": len(data.get("jobs", [])),
            "by_portal": {},
        }

    return data


def save_selected_jobs(data: dict):
    """Save the full selected jobs data to file."""
    with open(SELECTED_JOBS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_selected_job_identifiers() -> list:
    """Get list of already selected job identifiers (company - title - portal)."""
    data = load_selected_jobs()
    return [
        f"{j.get('company', '')} - {j.get('title', '')} ({j.get('portal', '')})"
        for j in data["jobs"]
    ]


def is_already_selected(company: str, title: str, portal: str) -> bool:
    """Check if a job was already selected."""
    identifier = f"{company} - {title} ({portal})"
    return identifier in get_selected_job_identifiers()


def save_selected_job(job_info: dict):
    """
    Save a selected job (score >= MIN_JOB_SCORE) to tracking file.

    Includes same fields as viewed jobs plus selected_at timestamp.
    """
    # Check for duplicates
    company = job_info.get("company", "")
    title = job_info.get("title", "")
    portal = job_info.get("portal", "unknown")

    if is_already_selected(company, title, portal):
        return  # Skip duplicates

    data = load_selected_jobs()

    # Add metadata (remove viewed_at if present, add selected_at)
    job_info = job_info.copy()  # Don't modify original
    job_info.pop("viewed_at", None)
    job_info["id"] = str(uuid.uuid4())
    job_info["selected_at"] = datetime.now().isoformat()

    data["jobs"].append(job_info)

    # Update stats
    data["stats"]["total_selected"] = len(data["jobs"])
    data["stats"]["by_portal"][portal] = data["stats"]["by_portal"].get(portal, 0) + 1

    save_selected_jobs(data)


# =============================================================================
# REJECTED JOBS TRACKING
# =============================================================================

def load_rejected_jobs() -> dict:
    """Load rejected jobs from JSON file."""
    default_data = {
        "jobs": [],
        "stats": {
            "total_rejected": 0,
            "by_reason": {},
            "by_portal": {},
        }
    }

    if not REJECTED_JOBS_FILE.exists():
        return default_data

    with open(REJECTED_JOBS_FILE, "r") as f:
        data = json.load(f)

    # Ensure stats structure exists
    if "stats" not in data:
        data["stats"] = {
            "total_rejected": len(data.get("jobs", [])),
            "by_reason": {},
            "by_portal": {},
        }

    return data


def save_rejected_jobs(data: dict):
    """Save the full rejected jobs data to file."""
    with open(REJECTED_JOBS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_rejected_job_identifiers() -> list:
    """Get list of already rejected job identifiers (company - title - portal)."""
    data = load_rejected_jobs()
    return [
        f"{j.get('company', '')} - {j.get('title', '')} ({j.get('portal', '')})"
        for j in data["jobs"]
    ]


def is_already_rejected(company: str, title: str, portal: str) -> bool:
    """Check if a job was already rejected."""
    identifier = f"{company} - {title} ({portal})"
    return identifier in get_rejected_job_identifiers()


def save_rejected_job(job_info: dict, rejection_reason: str, analysis: dict):
    """
    Save a rejected job with detailed rejection information.

    Args:
        job_info: Job information dict
        rejection_reason: Reason for rejection (e.g., "score_too_low", "negative_keywords")
        analysis: Analysis dict from analyze_job() containing matched keywords
    """
    # Check for duplicates
    company = job_info.get("company", "")
    title = job_info.get("title", "")
    portal = job_info.get("portal", "unknown")

    if is_already_rejected(company, title, portal):
        return  # Skip duplicates

    data = load_rejected_jobs()

    # Build rejected job entry
    rejected_job = job_info.copy()  # Don't modify original
    rejected_job.pop("viewed_at", None)
    rejected_job.pop("selected_at", None)
    rejected_job["id"] = str(uuid.uuid4())
    rejected_job["rejection_reason"] = rejection_reason
    rejected_job["rejected_at"] = datetime.now().isoformat()

    # Add matched keywords from analysis
    rejected_job["matched_required"] = analysis.get("matched_required", [])
    rejected_job["matched_bonus"] = analysis.get("matched_bonus", [])
    rejected_job["matched_negative"] = analysis.get("matched_negative", [])

    data["jobs"].append(rejected_job)

    # Update stats
    data["stats"]["total_rejected"] = len(data["jobs"])
    data["stats"]["by_reason"][rejection_reason] = data["stats"]["by_reason"].get(rejection_reason, 0) + 1
    data["stats"]["by_portal"][portal] = data["stats"]["by_portal"].get(portal, 0) + 1

    save_rejected_jobs(data)
