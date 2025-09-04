from contextlib import asynccontextmanager
from fastapi import FastAPI
from .database import create_tables
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting up DSBA LMS API...")
    
    try:
        # Create database tables
        await create_tables()
        logger.info("Database tables created successfully")
        
        # Initialize any other startup tasks here
        # - Redis connection
        # - Background task queues
        # - Cache warming
        
        logger.info("DSBA LMS API startup completed")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down DSBA LMS API...")
    
    try:
        # Cleanup tasks here
        # - Close database connections
        # - Stop background tasks
        # - Clear caches
        
        logger.info("DSBA LMS API shutdown completed")
        
    except Exception as e:
        logger.error(f"Shutdown failed: {e}")
        raise