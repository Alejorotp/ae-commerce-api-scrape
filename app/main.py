import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks, Header, HTTPException
from app.api.routes import router as api_router
from app.scheduler import scheduler, setup_scheduler
from app.services.scraper import run_scraper
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup and start scheduler
    setup_scheduler()
    scheduler.start()
    logger.info("Scheduler started.")
    yield
    # Shutdown scheduler
    scheduler.shutdown()
    logger.info("Scheduler stopped.")

app = FastAPI(title="H&M Colombia Scraper API", lifespan=lifespan)

app.include_router(api_router, prefix="/api")


