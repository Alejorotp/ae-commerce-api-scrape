import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.scraper import run_scraper

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler(timezone="America/Bogota")

async def scrape_job():
    logger.info("Executing scheduled scrape job...")
    try:
        await run_scraper()
    except Exception as e:
        logger.error(f"Scheduled scrape job failed: {e}")

def setup_scheduler():
    scheduler.add_job(scrape_job, 'cron', hour=12, minute=0, id='daily_scrape_hm')
    logger.info("Configured daily scrape job at 12:00 PM America/Bogota.")
