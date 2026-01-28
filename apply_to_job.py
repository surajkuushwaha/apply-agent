"""
Simple helper script to apply to a specific job URL.

Usage:
    python apply_to_job.py <job_url>

Example:
    python apply_to_job.py https://www.workatastartup.com/jobs/78968
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from browser_use import Agent, Browser, ChatGoogle
from job_bot.config import (
    BROWSER_AGENT_MODEL,
    RESUME_PATH,
    SESSION_STORAGE_DIR,
    CANDIDATE_PROFILE,
    MIN_JOB_SCORE,
)
from job_bot.tools import tools
from job_bot.portals import get_portal
from job_bot.tracking import save_applied_job, get_rate_limit_status
from job_bot.scoring import analyze_job


async def apply_to_specific_job(job_url: str):
    """
    Apply to a specific job URL.
    
    Args:
        job_url: The full URL of the job posting
    """
    # Determine portal from URL
    if "workatastartup.com" in job_url:
        portal_key = "workatastartup"
    elif "linkedin.com" in job_url:
        portal_key = "linkedin"
    else:
        print(f"⚠️  Unknown portal for URL: {job_url}")
        print("Supported portals: Work at a Startup, LinkedIn")
        return
    
    portal = get_portal(portal_key)
    
    # Check rate limits
    rate_status = get_rate_limit_status(portal_key)
    if not rate_status["can_apply"]:
        print(f"⚠️  Rate limit reached for {portal.name}")
        print(f"   Used: {rate_status['used']}/{rate_status['limit']}")
        print(f"   {rate_status['reset_info']}")
        return
    
    print(f"\n{'='*60}")
    print(f"Applying to job on {portal.name}")
    print(f"URL: {job_url}")
    print(f"Rate limit: {rate_status['remaining']}/{rate_status['limit']} remaining")
    print(f"{'='*60}\n")
    
    # Build task prompt
    task = f"""
TASK: Apply to a specific job posting on {portal.name}

{CANDIDATE_PROFILE}

JOB URL: {job_url}

STEPS:

1. Navigate directly to the job URL: {job_url}
   - The browser should already have your login context, so you should be logged in
   - If you see a login page, use the login credentials:
     Email/Username: {portal.username}
     Password: {portal.password}

2. Read and analyze the job posting:
   - Extract the job title, company name, and full job description
   - Use the analyze_job_action tool to get a detailed analysis
   - Use calculate_match_score tool to check if the job matches your profile
   - Only proceed if the score is >= {MIN_JOB_SCORE}

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
   Score: [calculated score]
   Status: [success/failed]
   CoverLetterUsed: [true/false]
   ResumeUploaded: [true/false]
   TechStack: [comma-separated tech mentioned]
   SalaryRange: [if visible, else "Not specified"]
   Remote: [yes/no/not specified]
   Experience: [required experience level]
   Notes: [any relevant notes about the application]
   ---END---

IMPORTANT:
- Use calculate_match_score before applying to verify the job is a good match
- Use generate_cover_letter_action if a cover letter field exists
- Upload the resume file from {RESUME_PATH}
- Fill all required fields accurately
- If the application fails, note the reason in the Notes field
"""
    
    # Get or create browser instance
    session_dir = SESSION_STORAGE_DIR / portal_key
    session_dir.mkdir(parents=True, exist_ok=True)
    
    browser = Browser(
        user_data_dir=str(session_dir),
        headless=False,
    )
    
    # Create agent
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


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python apply_to_job.py <job_url>")
        print("\nExample:")
        print("  python apply_to_job.py https://www.workatastartup.com/jobs/78968")
        sys.exit(1)
    
    job_url = sys.argv[1]
    
    if not job_url.startswith("http"):
        print(f"Error: Invalid URL: {job_url}")
        print("Please provide a full URL starting with http:// or https://")
        sys.exit(1)
    
    asyncio.run(apply_to_specific_job(job_url))


if __name__ == "__main__":
    main()
