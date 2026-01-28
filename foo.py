from browser_use import Agent, ChatGoogle
from dotenv import load_dotenv
import asyncio
import os

load_dotenv()

TASK = """
1. Go to https://www.workatastartup.com/jobs/78968

2. Extract the following company and job details from the page:
   - Company Name
   - YC Batch (e.g., S22, W23)
   - Company Description/Tagline
   - Job Title
   - Salary Range
   - Location
   - Job Type (Full-time, Part-time, Contract)
   - Required Experience
   - Visa Requirements
   - Key Responsibilities (summarized)
   - Required Skills/Qualifications (summarized)
   - Benefits (if listed)
   - Interview Process (if listed)

3. Return all extracted details in a structured format.
"""

async def main():
    llm = ChatGoogle(model="gemini-flash-latest")
    agent = Agent(task=TASK, llm=llm)
    await agent.run()

if __name__ == "__main__":
    asyncio.run(main())