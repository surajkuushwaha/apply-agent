"""
Allow running as: python -m job_bot
"""

from job_bot.main import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
