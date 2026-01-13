from browser_use import Agent, ChatGoogle, Tools, ActionResult
from dotenv import load_dotenv
import asyncio
import os
import json
import uuid
from datetime import datetime
from pathlib import Path
import google.generativeai as genai

load_dotenv()

# Configure Google Generative AI
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# =============================================================================
# CONFIGURATION
# =============================================================================

JOBS_TO_APPLY = 5
APPLIED_JOBS_FILE = Path("applied_jobs_v2.json")
RESUME_PATH = Path("/Users/suraj/Personal/projects/browser-use/Suraj_Kushwaha_Resumes-1.pdf")

# Credentials (from .env)
WORKATASTARTUP_USER = os.getenv("WORKATASTARTUP_USER", "surajkuushwaha")
WORKATASTARTUP_PASS = os.getenv("WORKATASTARTUP_PASS", "Suraj@9106")

# =============================================================================
# JOB SCORING CONFIGURATION
# =============================================================================

BLACKLIST_COMPANIES = [
    # Add companies you want to skip
]

REQUIRED_KEYWORDS = [
    "backend", "node", "nodejs", "typescript", "aws", "golang", "go",
    "graphql", "devops", "platform", "api"
]

BONUS_KEYWORDS = [
    "remote", "microservices", "saas", "startup", "series a", "series b",
    "mongodb", "postgresql", "redis", "docker", "kubernetes", "lambda"
]

MIN_JOB_SCORE = 30  # Minimum score to apply

# =============================================================================
# MULTI-PORTAL CONFIGURATION
# =============================================================================

JOB_PORTALS = {
    "workatastartup": {
        "name": "Work at a Startup",
        "url": "https://www.workatastartup.com/",
        "login_url": "https://www.workatastartup.com/users/sign_in",
        "username": WORKATASTARTUP_USER,
        "password": WORKATASTARTUP_PASS,
        "search_filters": "Backend Engineer, Software Engineer, Platform Engineer",
        "needs_login": True,
    },
    # "linkedin": {
    #     "name": "LinkedIn",
    #     "url": "https://www.linkedin.com/jobs/",
    #     "login_url": "https://www.linkedin.com/login",
    #     "username": os.getenv("LINKEDIN_USER", ""),
    #     "password": os.getenv("LINKEDIN_PASS", ""),
    #     "search_filters": "Backend Engineer Node.js TypeScript Remote",
    #     "needs_login": True,
    # },
    # "wellfound": {
    #     "name": "Wellfound (AngelList)",
    #     "url": "https://wellfound.com/jobs",
    #     "login_url": "https://wellfound.com/login",
    #     "username": os.getenv("WELLFOUND_USER", ""),
    #     "password": os.getenv("WELLFOUND_PASS", ""),
    #     "search_filters": "Backend Engineer, 2-5 years experience",
    #     "needs_login": True,
    # },
    # "indeed": {
    #     "name": "Indeed",
    #     "url": "https://www.indeed.com/",
    #     "login_url": None,
    #     "username": None,
    #     "password": None,
    #     "search_filters": "Backend Engineer Node.js Remote",
    #     "needs_login": False,
    # },
}

# Default portal allocation (total should equal JOBS_TO_APPLY)
PORTAL_ALLOCATION = {
    "workatastartup": 5,
    # "linkedin": 2,
    # "wellfound": 0,
    # "indeed": 0,
}

# =============================================================================
# CANDIDATE PROFILE (from resume.tex)
# =============================================================================

CANDIDATE_PROFILE = """
CANDIDATE PROFILE:
- Name: Suraj Kushwaha
- Title: Senior Backend Engineer | Product & Extensibility Platforms
- Experience: 4+ years at CultureX Entertainment (B2B SaaS, Influencer Marketing)
- Contact: jobs@surajkuushwaha.com | +91 91067 64917
- GitHub: github.com/surajkuushwaha
- LinkedIn: linkedin.com/in/surajkuushwaha

CORE STACK:
- Languages: Node.js, TypeScript, GraphQL, JavaScript (ES6+), Golang
- Backend: Express.js, Hono, MongoDB, PostgreSQL, MySQL, Redis, RESTful APIs, Microservices
- Cloud: AWS (Lambda, SQS, SNS, EventBridge, S3, EC2), Docker, GitHub Actions, CI/CD
- AI/Tooling: LLMs for debugging/documentation, Linux, Git, Tmux

KEY ACHIEVEMENTS:
- Owned public-facing API microservice (transformed internal tool into high-availability product)
- Led zero-downtime migration to unified SaaS architecture for 50+ global brands
- Architected event-driven systems (EventBridge, SQS, Lambda) handling 100M+ monthly requests
- Scaled backend infrastructure, reducing manual debugging effort by 40%
- Developed 40+ MVPs for influencer marketing platform, securing first client

PROFESSIONAL STRENGTHS:
- Remote/Async Native: Fluent in written communication, generous context in PRs
- Pragmatic Performance: Experienced in measuring bottlenecks in high-traffic B2B environments

TARGET ROLES:
- Senior Backend Engineer
- Backend Engineer
- Platform Engineer
- API/Extensibility Engineer
- DevOps Engineer
"""

# =============================================================================
# CUSTOM TOOLS
# =============================================================================

tools = Tools()


@tools.action('Generate a tailored cover letter for the job application')
def generate_cover_letter(job_title: str, company: str, job_description: str) -> str:
    """Generate a personalized cover letter using the candidate profile."""
    prompt = f"""
    Write a concise, professional cover letter (3 paragraphs, under 250 words) for:

    Position: {job_title} at {company}
    Job Description: {job_description}

    Candidate: Suraj Kushwaha, Senior Backend Engineer
    - 4+ years at CultureX Entertainment (B2B SaaS, Influencer Marketing)
    - Core Stack: Node.js, TypeScript, GraphQL, Golang, JavaScript
    - Backend: Express.js, Hono, MongoDB, PostgreSQL, MySQL, Redis, Microservices
    - Cloud: AWS (Lambda, SQS, SNS, EventBridge, S3, EC2), Docker, CI/CD
    - Led zero-downtime migration for 30+ global brands
    - Architected event-driven systems handling 10M+ monthly requests
    - Built 10+ MVPs, owns public-facing API products
    - Remote/Async native, strong written communication

    Guidelines:
    - Be professional and enthusiastic
    - Highlight 2-3 most relevant experiences for this specific role
    - Show understanding of the company/role
    - Keep it concise and impactful
    - Do NOT use generic phrases like "I am excited to apply"
    """

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating cover letter: {e}"


@tools.action('Calculate job match score based on requirements')
def calculate_match_score(job_title: str, job_description: str, company: str) -> ActionResult:
    """Calculate how well a job matches the candidate profile."""
    score = calculate_job_score(job_title, company, job_description)

    if score < 0:
        return ActionResult(
            extracted_content=f"SKIP: {company} is in the blacklist",
            is_done=False
        )

    recommendation = "APPLY" if score >= MIN_JOB_SCORE else "SKIP"

    return ActionResult(
        extracted_content=f"Score: {score}/100 - {recommendation}",
        long_term_memory=f"Job at {company} scored {score}/100"
    )


# =============================================================================
# JOB SCORING FUNCTIONS
# =============================================================================

def calculate_job_score(job_title: str, company: str, description: str) -> int:
    """Score job based on match with candidate profile (0-100). Returns -1 for blacklisted."""
    # Check blacklist
    if company.lower() in [c.lower() for c in BLACKLIST_COMPANIES]:
        return -1

    score = 0
    text = f"{job_title} {description}".lower()

    # Required skills match (+8 each, max ~88)
    for keyword in REQUIRED_KEYWORDS:
        if keyword in text:
            score += 8

    # Bonus keywords (+4 each)
    for keyword in BONUS_KEYWORDS:
        if keyword in text:
            score += 4

    # Experience level match
    if any(x in text for x in ["2-4 years", "2+ years", "3+ years", "4+ years", "mid-level", "senior"]):
        score += 10

    # Remote preference
    if "remote" in text:
        score += 5

    return min(score, 100)


# =============================================================================
# JOB TRACKING FUNCTIONS
# =============================================================================

def load_applied_jobs() -> dict:
    """Load previously applied jobs from JSON file. Migrates old schema if needed."""
    default_data = {
        "jobs": [],
        "stats": {
            "total_applied": 0,
            "by_portal": {},
            "by_status": {"success": 0, "failed": 0},
            "avg_score": 0
        }
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
        # Remove old root-level total_applied
        data.pop("total_applied", None)

    return data


def save_applied_job(job_info: dict):
    """Save newly applied job to tracking file with enhanced schema."""
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

    with open(APPLIED_JOBS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_applied_job_identifiers() -> list:
    """Get list of already applied job identifiers (company - title - portal)."""
    data = load_applied_jobs()
    return [
        f"{j.get('company', '')} - {j.get('title', '')} ({j.get('portal', '')})"
        for j in data["jobs"]
    ]


# =============================================================================
# TASK BUILDERS
# =============================================================================

def build_portal_task(portal_key: str, job_number: int, total_jobs: int, applied_jobs: list) -> str:
    """Build the task prompt for a specific portal."""
    portal = JOB_PORTALS[portal_key]
    applied_jobs_str = "\n".join(f"  - {job}" for job in applied_jobs[-30:]) if applied_jobs else "  None yet"
    blacklist_str = ", ".join(BLACKLIST_COMPANIES) if BLACKLIST_COMPANIES else "None"

    login_instructions = ""
    if portal["needs_login"] and portal["username"]:
        login_instructions = f"""
   - Click "Log in" or "Sign in"
   - Enter Email/Username: {portal["username"]}
   - Enter Password: {portal["password"]}
   - Submit and wait for dashboard"""

    return f"""
TASK: Apply to job {job_number} of {total_jobs} on {portal["name"]}

{CANDIDATE_PROFILE}

ALREADY APPLIED (DO NOT APPLY TO THESE AGAIN):
{applied_jobs_str}

BLACKLISTED COMPANIES (SKIP THESE):
{blacklist_str}

JOB SCORING CRITERIA (only apply to jobs scoring >= {MIN_JOB_SCORE}):
- Required keywords (+8 each): {", ".join(REQUIRED_KEYWORDS)}
- Bonus keywords (+4 each): {", ".join(BONUS_KEYWORDS)}
- Experience match: +10 for 2-4 years, mid-level, senior
- Remote: +5 bonus

STEPS:

1. Navigate to {portal["url"]}
{login_instructions}

2. Search/filter for jobs:
   - Use filters: {portal["search_filters"]}
   - Look for roles matching: Backend, Platform, API, DevOps
   - Prefer: Remote, Startup (Seed to Series B)

3. Evaluate jobs before applying:
   - Use calculate_match_score tool to check job score
   - Only apply if score >= {MIN_JOB_SCORE}
   - Skip blacklisted companies
   - Skip already-applied jobs

4. For the selected job:
   - Click to view full details
   - Use generate_cover_letter tool if cover letter is needed
   - Upload resume if file upload is available (path: {RESUME_PATH})
   - Fill all required fields using candidate profile
   - Submit application

5. Return this EXACT format after applying:
   ---JOB_APPLIED---
   Portal: {portal_key}
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
   ---END---

IMPORTANT:
- Use calculate_match_score before applying
- Use generate_cover_letter when a cover letter field exists
- Skip jobs already in the applied list
- If application fails, try the next matching job
- Be thorough but efficient
"""


# =============================================================================
# APPLICATION FUNCTIONS
# =============================================================================

async def apply_to_job_on_portal(portal_key: str, job_number: int, total_jobs: int) -> dict:
    """Apply to a single job on a specific portal."""
    applied_jobs = get_applied_job_identifiers()
    task = build_portal_task(portal_key, job_number, total_jobs, applied_jobs)

    llm = ChatGoogle(model="gemini-flash-latest")
    agent = Agent(
        task=task,
        llm=llm,
        tools=tools,
        available_file_paths=[str(RESUME_PATH)],
    )

    portal_name = JOB_PORTALS[portal_key]["name"]
    print(f"\n{'='*60}")
    print(f"[{portal_name}] Applying to job {job_number}/{total_jobs}")
    print(f"{'='*60}")

    try:
        history = await agent.run(max_steps=60)
        result = history.final_result() if history else "No result"

        # Parse result
        job_info = {
            "portal": portal_key,
            "job_number": job_number,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "raw_result": str(result)[:1000] if result else ""
        }

        # Extract structured data from result
        if result:
            result_str = str(result)
            field_mappings = {
                "Company:": "company",
                "Title:": "title",
                "URL:": "url",
                "Score:": "score",
                "Status:": "status",
                "CoverLetterUsed:": "cover_letter_used",
                "ResumeUploaded:": "resume_uploaded",
                "TechStack:": "tech_stack",
                "SalaryRange:": "salary_range",
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
                            except:
                                job_info[key] = 0
                        elif key in ["cover_letter_used", "resume_uploaded"]:
                            job_info[key] = value.lower() == "true"
                        elif key == "tech_stack":
                            job_info[key] = [t.strip() for t in value.split(",")]
                        else:
                            job_info[key] = value

        save_applied_job(job_info)
        status = job_info.get("status", "unknown")
        company = job_info.get("company", "Unknown")
        print(f"✓ [{portal_name}] Applied to {company} - Status: {status}")
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
        print(f"✗ [{portal_name}] Error: {e}")
        return error_info


async def daily_multi_portal_application():
    """Main function to apply across multiple job portals."""
    total_jobs = sum(PORTAL_ALLOCATION.values())

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║              DAILY JOB APPLICATION BOT v2.0                  ║
║══════════════════════════════════════════════════════════════║
║  Target: {total_jobs} jobs across {len(PORTAL_ALLOCATION)} portals                              ║
║  Date: {datetime.now().strftime("%Y-%m-%d %H:%M")}                                       ║
║  Min Score: {MIN_JOB_SCORE}                                                  ║
╚══════════════════════════════════════════════════════════════╝
    """)

    # Show allocation
    print("Portal Allocation:")
    for portal, count in PORTAL_ALLOCATION.items():
        print(f"  - {JOB_PORTALS[portal]['name']}: {count} jobs")

    # Load stats
    data = load_applied_jobs()
    print(f"\nPreviously applied: {data['stats']['total_applied']} jobs")
    print(f"Average score: {data['stats']['avg_score']}")
    print(f"\nStarting applications...\n")

    results = []
    job_counter = 0

    for portal_key, job_count in PORTAL_ALLOCATION.items():
        if job_count == 0:
            continue

        portal_name = JOB_PORTALS[portal_key]["name"]
        print(f"\n{'─'*60}")
        print(f"Starting {portal_name} ({job_count} jobs)")
        print(f"{'─'*60}")

        for i in range(1, job_count + 1):
            job_counter += 1
            result = await apply_to_job_on_portal(portal_key, i, job_count)
            results.append(result)

            # Delay between applications
            if job_counter < total_jobs:
                delay = 10 if portal_key == "linkedin" else 5
                print(f"Waiting {delay} seconds before next application...")
                await asyncio.sleep(delay)

    # Summary
    print(f"\n{'═'*60}")
    print("DAILY SUMMARY")
    print(f"{'═'*60}")

    successful = sum(1 for r in results if r.get("status") == "success")
    failed = sum(1 for r in results if r.get("status") == "failed" or "error" in r)

    print(f"Total attempted: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")

    # By portal breakdown
    print("\nBy Portal:")
    for portal_key in PORTAL_ALLOCATION.keys():
        portal_results = [r for r in results if r.get("portal") == portal_key]
        portal_success = sum(1 for r in portal_results if r.get("status") == "success")
        print(f"  - {JOB_PORTALS[portal_key]['name']}: {portal_success}/{len(portal_results)}")

    # Updated totals
    updated_data = load_applied_jobs()
    print(f"\nAll-time total: {updated_data['stats']['total_applied']} jobs")
    print(f"Average score: {updated_data['stats']['avg_score']}")

    return results


# =============================================================================
# SINGLE PORTAL MODE (for testing)
# =============================================================================

async def apply_single_portal(portal_key: str = "workatastartup", count: int = 1):
    """Apply to jobs on a single portal (useful for testing)."""
    print(f"Single portal mode: {portal_key}, {count} job(s)")

    results = []
    for i in range(1, count + 1):
        result = await apply_to_job_on_portal(portal_key, i, count)
        results.append(result)
        if i < count:
            await asyncio.sleep(5)

    return results


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    # Run multi-portal application
    # asyncio.run(daily_multi_portal_application())

    # Or test single portal:
    asyncio.run(apply_single_portal("workatastartup", 1))
