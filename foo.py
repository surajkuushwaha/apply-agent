from browser_use import Agent, ChatGoogle
from dotenv import load_dotenv
import asyncio
import os

load_dotenv()

TASK = """
1. Go to https://www.workatastartup.com/ and click "Log in"
2. Login with:
   - Email/Username: surajkuushwaha
   - Password: Suraj@9106

3. After login, search/filter for jobs matching:
   - Role: Backend Engineer, Software Engineer, or Full Stack Engineer
   - Skills: Node.js, TypeScript, AWS, Microservices
   - Experience: 2-4 years

4. Find the BEST matching job for a candidate with:
   - 2.5+ years backend experience with Node.js, TypeScript, AWS
   - Microservices architecture (handling 5M+ requests/month)
   - MySQL, PostgreSQL, Redis, Docker, CI/CD experience
   - B2B SaaS background

5. Click on the most relevant job listing and apply.
   - Fill any required fields
   - Submit the application

6. Return the job title, company name, and confirmation of application submission.
"""

async def main():
    llm = ChatGoogle(model="gemini-flash-latest")
    agent = Agent(task=TASK, llm=llm)
    await agent.run()

if __name__ == "__main__":
    asyncio.run(main())