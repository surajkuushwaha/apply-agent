"""
Job Application Bot - Main Entry Point

CLI interface for job searching and application automation.
Supports:
- Multiple job portals (LinkedIn, WorkAtAStartup)
- Dry-run mode for testing
- Configurable freshness filters
- Rate limit awareness

Usage:
    python -m job_bot           # Recommended
    python -m job_bot.main      # Alternative
    python job_bot/main.py      # Direct execution (also works)
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Handle direct execution (python job_bot/main.py)
if __name__ == "__main__" and __package__ is None:
    # Add parent directory to path so relative imports work
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    __package__ = "job_bot"

from browser_use import Agent, Browser, ChatGoogle

from .config import (
    JOBS_TO_APPLY,
    MIN_JOB_SCORE,
    PORTAL_ALLOCATION,
    BROWSER_AGENT_MODEL,
    RESUME_PATH,
    SESSION_STORAGE_DIR,
    LINKEDIN_FRESHNESS,
    DEFAULT_LINKEDIN_FRESHNESS,
    RATE_LIMITS,
    CANDIDATE_PROFILE,
)
from .tools import tools
from .tracking import (
    load_applied_jobs,
    save_applied_job,
    get_stats_summary,
    get_rate_limit_status,
    save_viewed_job,
    save_selected_job,
    save_rejected_job,
)
from .scoring import analyze_job
from .portals import get_portal, PORTAL_REGISTRY


# =============================================================================
# BROWSER SESSION MANAGEMENT
# =============================================================================

def get_browser_for_portal(portal_key: str) -> Browser:
    """Get or create a persistent browser instance for a portal."""
    session_dir = SESSION_STORAGE_DIR / portal_key
    session_dir.mkdir(parents=True, exist_ok=True)

    return Browser(
        user_data_dir=str(session_dir),
        headless=False,
    )


# =============================================================================
# SEARCH FUNCTIONS
# =============================================================================

async def search_jobs_on_portal(
    portal_key: str,
    require_salary_range: bool = False,
    freshness: str = None,
    dry_run: bool = False
) -> list:
    """Search for jobs on a specific portal without applying."""
    portal = get_portal(portal_key)

    # Build task with portal-specific options
    if portal_key == "linkedin" and freshness:
        task = portal.build_search_task(require_salary_range=require_salary_range, freshness=freshness)
    else:
        task = portal.build_search_task(require_salary_range=require_salary_range)

    if dry_run:
        print(f"\n[DRY RUN] Would search {portal.name}")
        print(f"[DRY RUN] Task preview:\n{task[:500]}...")
        return []

    browser = get_browser_for_portal(portal_key)
    llm = ChatGoogle(model=BROWSER_AGENT_MODEL)
    agent = Agent(
        task=task,
        llm=llm,
        tools=tools,
        browser=browser,
        available_file_paths=[str(RESUME_PATH)],
    )

    print(f"\n{'='*60}")
    print(f"[{portal.name}] Searching for jobs...")
    print(f"{'='*60}")

    try:
        history = await agent.run(max_steps=60)
        result = history.final_result() if history else "No result"

        # Parse results
        jobs_found = []
        if result:
            result_str = str(result)
            current_job = {}

            for line in result_str.split("\n"):
                line = line.strip()
                if line.startswith("---JOB_FOUND---"):
                    current_job = {}
                elif line.startswith("---END---"):
                    if current_job:
                        # Ensure portal is set
                        current_job["portal"] = portal_key
                        jobs_found.append(current_job)
                        current_job = {}
                else:
                    parsed = portal.parse_result_common(line, "---JOB_FOUND---")
                    current_job.update(parsed)

        # Save and categorize all browsed jobs
        for job in jobs_found:
            # Ensure portal is set
            job["portal"] = job.get("portal", portal_key)
            
            # Build a description from available fields for analysis
            # (since search results might not have full description)
            title = job.get("title", "")
            company = job.get("company", "")
            tech_stack = job.get("tech_stack", [])
            experience = job.get("experience", "")
            remote = job.get("remote", "")
            
            # Construct description from available info
            description_parts = []
            if isinstance(tech_stack, list):
                description_parts.extend(tech_stack)
            elif isinstance(tech_stack, str):
                description_parts.append(tech_stack)
            if experience:
                description_parts.append(experience)
            if remote:
                description_parts.append(remote)
            
            description = " ".join(description_parts) if description_parts else title
            
            # Analyze job to get rejection reason and matched keywords
            analysis = analyze_job(title, company, description)
            
            # Use score from analysis (or from parsed result if analysis score is 0 and parsed has score)
            score = analysis.get("score", 0)
            if score == 0 and job.get("score"):
                try:
                    score = int(job.get("score", 0))
                except (ValueError, TypeError):
                    score = 0
            
            # Update job with score
            job["score"] = score
            
            # Save as viewed
            save_viewed_job(job)
            
            # Categorize based on score and rejection reason
            rejection_reason = analysis.get("rejection_reason", "score_too_low")
            
            if rejection_reason == "passed" or score >= MIN_JOB_SCORE:
                # Save as selected
                save_selected_job(job)
            else:
                # Save as rejected with reason and analysis
                save_rejected_job(job, rejection_reason, analysis)

        print(f"✓ [{portal.name}] Found {len(jobs_found)} jobs")
        return jobs_found

    except Exception as e:
        print(f"✗ [{portal.name}] Error during search: {e}")
        return []


async def search_jobs_multi_portal(
    require_salary_range: bool = False,
    freshness: str = None,
    dry_run: bool = False
):
    """Search for jobs across multiple job portals."""
    print_header("JOB SEARCH", require_salary_range, dry_run=dry_run)

    enabled_portals = list(PORTAL_ALLOCATION.keys())
    print("Portals to search:")
    for portal_key in enabled_portals:
        portal = get_portal(portal_key)
        print(f"  - {portal.name}")

    data = load_applied_jobs()
    print(f"\nPreviously applied: {data['stats']['total_applied']} jobs")

    if freshness and "linkedin" in enabled_portals:
        print(f"LinkedIn freshness: {freshness} ({LINKEDIN_FRESHNESS.get(freshness, 'default')})")

    print(f"\nStarting job search...\n")

    all_jobs = []

    for portal_key in enabled_portals:
        portal = get_portal(portal_key)
        print(f"\n{'─'*60}")
        print(f"Searching {portal.name}")
        print(f"{'─'*60}")

        jobs = await search_jobs_on_portal(
            portal_key,
            require_salary_range=require_salary_range,
            freshness=freshness,
            dry_run=dry_run
        )
        all_jobs.extend(jobs)

        if portal_key != enabled_portals[-1]:
            if not dry_run:
                print("Waiting 5 seconds before next portal...")
                await asyncio.sleep(5)

    print_search_summary(all_jobs, require_salary_range)
    return all_jobs


# =============================================================================
# APPLICATION FUNCTIONS
# =============================================================================

async def apply_to_job_on_portal(
    portal_key: str,
    job_number: int,
    total_jobs: int,
    require_salary_range: bool = False,
    freshness: str = None,
    dry_run: bool = False
) -> dict:
    """Apply to a single job on a specific portal."""
    portal = get_portal(portal_key)

    # Check rate limits
    rate_status = get_rate_limit_status(portal_key)
    if not rate_status["can_apply"]:
        print(f"⚠️ [{portal.name}] Rate limit reached: {rate_status['used']}/{rate_status['limit']}")
        print(f"   {rate_status['reset_info']}")
        return {
            "portal": portal_key,
            "status": "skipped",
            "reason": "rate_limit_reached",
        }

    # Build task
    if portal_key == "linkedin" and freshness:
        task = portal.build_apply_task(
            job_number, total_jobs,
            require_salary_range=require_salary_range,
            freshness=freshness
        )
    else:
        task = portal.build_apply_task(
            job_number, total_jobs,
            require_salary_range=require_salary_range
        )

    if dry_run:
        print(f"\n[DRY RUN] Would apply to job {job_number}/{total_jobs} on {portal.name}")
        print(f"[DRY RUN] Rate limit: {rate_status['remaining']}/{rate_status['limit']} remaining")
        return {
            "portal": portal_key,
            "job_number": job_number,
            "status": "dry_run",
            "date": datetime.now().strftime("%Y-%m-%d"),
        }

    browser = get_browser_for_portal(portal_key)
    llm = ChatGoogle(model=BROWSER_AGENT_MODEL)
    agent = Agent(
        task=task,
        llm=llm,
        tools=tools,
        browser=browser,
        available_file_paths=[str(RESUME_PATH)],
    )

    print(f"\n{'='*60}")
    print(f"[{portal.name}] Applying to job {job_number}/{total_jobs}")
    print(f"Rate limit: {rate_status['remaining']}/{rate_status['limit']} remaining")
    print(f"{'='*60}")

    try:
        history = await agent.run(max_steps=60)
        result = history.final_result() if history else "No result"

        job_info = portal.parse_job_result(result) if result else {}
        job_info.update({
            "portal": portal_key,
            "job_number": job_number,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "raw_result": str(result)[:1000] if result else ""
        })

        save_applied_job(job_info)
        status = job_info.get("status", "unknown")
        company = job_info.get("company", "Unknown")
        print(f"✓ [{portal.name}] Applied to {company} - Status: {status}")
        return job_info

    except Exception as e:
        error_info = {
            "portal": portal_key,
            "job_number": job_number,
            "status": "failed",
            "error": str(e),
            "date": datetime.now().strftime("%Y-%m-%d")
        }
        save_applied_job(error_info)
        print(f"✗ [{portal.name}] Error: {e}")
        return error_info


async def apply_multi_portal(
    require_salary_range: bool = False,
    freshness: str = None,
    dry_run: bool = False
):
    """Apply to jobs across multiple portals."""
    total_jobs = sum(PORTAL_ALLOCATION.values())
    print_header("JOB APPLICATION", require_salary_range, total_jobs, dry_run=dry_run)

    print("Portal Allocation:")
    for portal_key, count in PORTAL_ALLOCATION.items():
        portal = get_portal(portal_key)
        rate_status = get_rate_limit_status(portal_key)
        print(f"  - {portal.name}: {count} jobs (limit: {rate_status['remaining']}/{rate_status['limit']} remaining)")

    data = load_applied_jobs()
    print(f"\nPreviously applied: {data['stats']['total_applied']} jobs")
    print(f"Average score: {data['stats']['avg_score']}")

    if freshness and "linkedin" in PORTAL_ALLOCATION:
        print(f"LinkedIn freshness: {freshness}")

    print(f"\nStarting applications...\n")

    results = []
    job_counter = 0

    for portal_key, job_count in PORTAL_ALLOCATION.items():
        if job_count == 0:
            continue

        portal = get_portal(portal_key)
        print(f"\n{'─'*60}")
        print(f"Starting {portal.name} ({job_count} jobs)")
        print(f"{'─'*60}")

        for i in range(1, job_count + 1):
            job_counter += 1
            result = await apply_to_job_on_portal(
                portal_key, i, job_count,
                require_salary_range=require_salary_range,
                freshness=freshness,
                dry_run=dry_run
            )
            results.append(result)

            if job_counter < total_jobs and not dry_run:
                delay = RATE_LIMITS.get(portal_key, {}).get("delay_seconds", 10)
                print(f"Waiting {delay} seconds before next application...")
                await asyncio.sleep(delay)

    print_application_summary(results)
    return results


# =============================================================================
# SINGLE PORTAL MODE
# =============================================================================

async def apply_single_portal(
    portal_key: str = "linkedin",
    count: int = 1,
    require_salary_range: bool = False,
    freshness: str = None,
    dry_run: bool = False
):
    """Apply to jobs on a single portal."""
    portal = get_portal(portal_key)
    print(f"Single portal mode: {portal.name}, {count} job(s)")

    if dry_run:
        print("[DRY RUN MODE ENABLED]")

    results = []
    for i in range(1, count + 1):
        result = await apply_to_job_on_portal(
            portal_key, i, count,
            require_salary_range=require_salary_range,
            freshness=freshness,
            dry_run=dry_run
        )
        results.append(result)

        if i < count and not dry_run:
            delay = RATE_LIMITS.get(portal_key, {}).get("delay_seconds", 5)
            await asyncio.sleep(delay)

    return results


# =============================================================================
# APPLY TO SPECIFIC JOB URL
# =============================================================================

async def apply_to_specific_job_url(job_url: str, dry_run: bool = False) -> dict:
    """
    Apply to a specific job URL.
    
    Args:
        job_url: The full URL of the job posting
        dry_run: If True, simulate without actually applying
    
    Returns:
        dict: Application result information
    """
    # Determine portal from URL
    if "workatastartup.com" in job_url:
        portal_key = "workatastartup"
    elif "linkedin.com" in job_url:
        portal_key = "linkedin"
    else:
        print(f"⚠️  Unknown portal for URL: {job_url}")
        print("Supported portals: Work at a Startup, LinkedIn")
        return {
            "status": "failed",
            "error": "Unknown portal",
            "url": job_url,
        }
    
    portal = get_portal(portal_key)
    
    # Check rate limits
    rate_status = get_rate_limit_status(portal_key)
    if not rate_status["can_apply"]:
        print(f"⚠️  Rate limit reached for {portal.name}")
        print(f"   Used: {rate_status['used']}/{rate_status['limit']}")
        print(f"   {rate_status['reset_info']}")
        return {
            "portal": portal_key,
            "status": "skipped",
            "reason": "rate_limit_reached",
            "url": job_url,
        }
    
    print(f"\n{'='*60}")
    print(f"Applying to job on {portal.name}")
    print(f"URL: {job_url}")
    print(f"Rate limit: {rate_status['remaining']}/{rate_status['limit']} remaining")
    print(f"{'='*60}\n")
    
    if dry_run:
        print("[DRY RUN] Would apply to job URL")
        print(f"[DRY RUN] Rate limit: {rate_status['remaining']}/{rate_status['limit']} remaining")
        return {
            "portal": portal_key,
            "url": job_url,
            "status": "dry_run",
            "date": datetime.now().strftime("%Y-%m-%d"),
        }
    
    # Build task prompt
    task = f"""
TASK: Apply to a specific job posting on {portal.name}

{CANDIDATE_PROFILE}

JOB URL: {job_url}

CRITICAL: DO NOT use analyze_job_action or calculate_match_score tools. The user has explicitly provided this URL and wants to apply directly. Skip all analysis and scoring - proceed directly to applying.

STEPS:

1. Navigate directly to the job URL: {job_url}
   - The browser should already have your login context, so you should be logged in
   - If you see a login page, use the login credentials:
     Email/Username: {portal.username}
     Password: {portal.password}

2. Read the job posting to extract basic information:
   - Extract the job title and company name (you can use the extract tool if needed)
   - DO NOT use analyze_job_action tool
   - DO NOT use calculate_match_score tool
   - Just read the page to understand what you're applying to

3. Apply to the job:
   - Click the "Apply" or "Quick Apply" button
   - If a cover letter field is present, use generate_cover_letter_action tool to create a tailored cover letter
   - Upload your resume from: {RESUME_PATH}
   - Fill in all required fields using information from the candidate profile:
     * Name: Suraj Kushwaha
     * Email: jobs@surajkuushwaha.com
     * Phone: +91 91067 64917
     * GitHub: github.com/surajkuushwaha
     * LinkedIn: linkedin.com/in/surajkuushwaha
     * Experience: 4+ years as Senior Backend Engineer
   - Review all information before submitting
   - Submit the application

4. After applying, return this EXACT format:
   ---JOB_APPLIED---
   Portal: {portal_key}
   Company: [company name]
   Title: [job title]
   URL: {job_url}
   Score: N/A
   Status: [success/failed]
   CoverLetterUsed: [true/false]
   ResumeUploaded: [true/false]
   TechStack: [comma-separated tech mentioned if visible on page]
   SalaryRange: [if visible, else "Not specified"]
   Remote: [yes/no/not specified]
   Experience: [required experience level if visible]
   Notes: [any relevant notes about the application]
   ---END---

CRITICAL INSTRUCTIONS:
- DO NOT call analyze_job_action - skip it entirely
- DO NOT call calculate_match_score - skip it entirely
- Proceed directly to applying to the job
- Use generate_cover_letter_action if a cover letter field exists
- Upload the resume file from {RESUME_PATH}
- Fill all required fields accurately
- Complete the application process fully
- If the application fails, note the reason in the Notes field
"""
    
    browser = get_browser_for_portal(portal_key)
    llm = ChatGoogle(model=BROWSER_AGENT_MODEL)
    agent = Agent(
        task=task,
        llm=llm,
        tools=tools,
        browser=browser,
        available_file_paths=[str(RESUME_PATH)],
    )
    
    try:
        print("Starting browser automation...")
        history = await agent.run(max_steps=60)
        result = history.final_result() if history else "No result"
        
        # Parse result
        job_info = portal.parse_job_result(result) if result else {}
        job_info.update({
            "portal": portal_key,
            "url": job_url,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "raw_result": str(result)[:1000] if result else ""
        })
        
        # Save application
        save_applied_job(job_info)
        
        # Print summary
        print(f"\n{'='*60}")
        print("APPLICATION RESULT")
        print(f"{'='*60}")
        print(f"Company: {job_info.get('company', 'Unknown')}")
        print(f"Title: {job_info.get('title', 'Unknown')}")
        print(f"Status: {job_info.get('status', 'unknown')}")
        print(f"Score: {job_info.get('score', 'N/A')}")
        print(f"Cover Letter Used: {job_info.get('cover_letter_used', False)}")
        print(f"Resume Uploaded: {job_info.get('resume_uploaded', False)}")
        if job_info.get('notes'):
            print(f"Notes: {job_info['notes']}")
        print(f"{'='*60}\n")
        
        return job_info
        
    except Exception as e:
        error_info = {
            "portal": portal_key,
            "url": job_url,
            "status": "failed",
            "error": str(e),
            "date": datetime.now().strftime("%Y-%m-%d")
        }
        save_applied_job(error_info)
        print(f"\n✗ Error during application: {e}")
        return error_info


# =============================================================================
# OUTPUT HELPERS
# =============================================================================

def print_header(mode: str, require_salary_range: bool, total_jobs: int = None, dry_run: bool = False):
    """Print a formatted header."""
    salary_status = "ENABLED" if require_salary_range else "DISABLED"
    dry_run_status = " [DRY RUN]" if dry_run else ""

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║              {mode} BOT v2.0{dry_run_status:>20}  ║
╠══════════════════════════════════════════════════════════════╣
║  Date: {datetime.now().strftime("%Y-%m-%d %H:%M"):45} ║
║  Min Score: {MIN_JOB_SCORE:<47} ║
║  Salary Range Filter: {salary_status:<37} ║
{"║  Target: " + str(total_jobs) + " jobs" + " "*48 + "║" if total_jobs else ""}
╚══════════════════════════════════════════════════════════════╝
    """)


def print_search_summary(all_jobs: list, require_salary_range: bool):
    """Print search results summary."""
    print(f"\n{'═'*60}")
    print("SEARCH SUMMARY")
    print(f"{'═'*60}")

    if require_salary_range:
        jobs_with_salary = [j for j in all_jobs if j.get("salary_range", "").lower() not in ["not specified", "n/a", ""]]
        print(f"⚠️ Filtered to jobs with salary range: {len(jobs_with_salary)} jobs")
        all_jobs = jobs_with_salary

    print(f"Total jobs found: {len(all_jobs)}")

    high_score_jobs = [j for j in all_jobs if j.get("score", 0) >= MIN_JOB_SCORE]
    print(f"Jobs with score >= {MIN_JOB_SCORE}: {len(high_score_jobs)}")

    if all_jobs:
        sorted_jobs = sorted(all_jobs, key=lambda x: x.get("score", 0), reverse=True)
        print(f"\nTop 10 jobs by score:")
        for i, job in enumerate(sorted_jobs[:10], 1):
            company = job.get("company", "Unknown")
            title = job.get("title", "Unknown")
            score = job.get("score", 0)
            salary = job.get("salary_range", "Not specified")
            print(f"  {i}. {company} - {title} (Score: {score}, Salary: {salary})")


def print_application_summary(results: list):
    """Print application results summary."""
    print(f"\n{'═'*60}")
    print("APPLICATION SUMMARY")
    print(f"{'═'*60}")

    successful = sum(1 for r in results if r.get("status") == "success")
    failed = sum(1 for r in results if r.get("status") == "failed" or "error" in r)
    skipped = sum(1 for r in results if r.get("status") in ["skipped", "dry_run"])

    print(f"Total attempted: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Skipped: {skipped}")

    print("\nBy Portal:")
    for portal_key in PORTAL_ALLOCATION.keys():
        portal_results = [r for r in results if r.get("portal") == portal_key]
        portal_success = sum(1 for r in portal_results if r.get("status") == "success")
        portal = get_portal(portal_key)
        print(f"  - {portal.name}: {portal_success}/{len(portal_results)}")

    print("\n" + get_stats_summary())


# =============================================================================
# CLI MENU
# =============================================================================

def get_user_choice() -> dict:
    """Interactive CLI menu for the job bot."""
    print("\n" + "="*60)
    print("JOB SEARCH & APPLICATION BOT v2.0")
    print("="*60)

    # Mode selection
    print("\nWhat would you like to do?")
    print("  1. Search for jobs (browse and list matching jobs)")
    print("  2. Apply to jobs (automatically apply to matching jobs)")
    print("  3. View stats (see application history and rate limits)")
    print("  4. Apply to specific job URL (apply to a job by providing its URL)")

    while True:
        choice = input("\nEnter your choice (1, 2, 3, or 4): ").strip()
        if choice in ["1", "2", "3", "4"]:
            break
        print("Invalid choice. Please enter 1, 2, 3, or 4.")

    if choice == "3":
        return {"mode": "stats"}
    
    if choice == "4":
        # Get job URL
        print("\nEnter the job URL:")
        print("  Example: https://www.workatastartup.com/jobs/78968")
        while True:
            job_url = input("\nJob URL: ").strip()
            if job_url.startswith("http://") or job_url.startswith("https://"):
                break
            print("Invalid URL. Please provide a full URL starting with http:// or https://")
        
        # Dry run option
        print("\nDry run mode?")
        print("  This will simulate the process without actually applying.")
        while True:
            dry_run_choice = input("\nEnable dry run? (y/n, default n): ").strip().lower() or "n"
            if dry_run_choice in ["y", "yes", "n", "no"]:
                break
            print("Invalid choice.")
        
        return {
            "mode": "apply_url",
            "job_url": job_url,
            "dry_run": dry_run_choice in ["y", "yes"],
        }

    mode = "search" if choice == "1" else "apply"

    # Portal selection
    print("\nSelect portal(s):")
    print("  1. LinkedIn")
    print("  2. Work at a Startup")
    print("  3. Both (use default allocation)")

    while True:
        portal_choice = input("\nEnter your choice (1, 2, or 3): ").strip()
        if portal_choice in ["1", "2", "3"]:
            break
        print("Invalid choice.")

    portals = {
        "1": ["linkedin"],
        "2": ["workatastartup"],
        "3": list(PORTAL_ALLOCATION.keys()),
    }[portal_choice]

    # LinkedIn freshness (if LinkedIn selected)
    freshness = None
    if "linkedin" in portals:
        print("\nLinkedIn job freshness filter:")
        print("  1. Past hour (first-mover advantage)")
        print("  2. Past 24 hours (recommended)")
        print("  3. Past week")
        print("  4. Past month")

        while True:
            fresh_choice = input("\nEnter your choice (1-4, default 2): ").strip() or "2"
            if fresh_choice in ["1", "2", "3", "4"]:
                break
            print("Invalid choice.")

        freshness = {"1": "1h", "2": "24h", "3": "7d", "4": "30d"}[fresh_choice]

    # Salary filter
    print("\nRequire salary range?")
    print("  This will only consider jobs with visible salary information.")

    while True:
        salary_choice = input("\nRequire salary range? (y/n, default n): ").strip().lower() or "n"
        if salary_choice in ["y", "yes", "n", "no"]:
            break
        print("Invalid choice.")

    require_salary = salary_choice in ["y", "yes"]

    # Dry run
    print("\nDry run mode?")
    print("  This will simulate the process without actually applying.")

    while True:
        dry_run_choice = input("\nEnable dry run? (y/n, default n): ").strip().lower() or "n"
        if dry_run_choice in ["y", "yes", "n", "no"]:
            break
        print("Invalid choice.")

    dry_run = dry_run_choice in ["y", "yes"]

    return {
        "mode": mode,
        "portals": portals,
        "freshness": freshness,
        "require_salary": require_salary,
        "dry_run": dry_run,
    }


async def main():
    """Main entry point."""
    options = get_user_choice()

    if options["mode"] == "stats":
        print("\n" + get_stats_summary())
        return
    
    if options["mode"] == "apply_url":
        await apply_to_specific_job_url(
            job_url=options["job_url"],
            dry_run=options["dry_run"],
        )
        return

    # Temporarily update PORTAL_ALLOCATION if specific portals selected
    if len(options["portals"]) == 1:
        portal_key = options["portals"][0]
        original_allocation = PORTAL_ALLOCATION.copy()
        for key in list(PORTAL_ALLOCATION.keys()):
            if key != portal_key:
                PORTAL_ALLOCATION[key] = 0

    if options["mode"] == "search":
        await search_jobs_multi_portal(
            require_salary_range=options["require_salary"],
            freshness=options.get("freshness"),
            dry_run=options["dry_run"],
        )
    else:
        await apply_multi_portal(
            require_salary_range=options["require_salary"],
            freshness=options.get("freshness"),
            dry_run=options["dry_run"],
        )


if __name__ == "__main__":
    asyncio.run(main())
