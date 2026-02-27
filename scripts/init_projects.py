"""
Script for initializing and caching projects
Run once when first setting up the bot
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.projects_service import projects_service
from utils.logger import logger


async def initialize_projects():
    """Initialize and load projects with real data"""
    
    logger.info("=" * 60)
    logger.info("🚀 Starting projects initialization...")
    logger.info("=" * 60)
    
    try:
        logger.info("📦 Loading projects from https://projects.mospolytech.ru/...")
        logger.info("⏳ This may take 1-3 minutes depending on the site...")
        
        # Try to load fresh data from the site
        success = await projects_service.init_projects(force_refresh=True)
        
        # Get statistics
        summary = projects_service.get_projects_summary()
        
        if success and summary['total'] > 0:
            logger.info("=" * 60)
            logger.info("✅ INITIALIZATION SUCCESSFUL!")
            logger.info("=" * 60)
            logger.info(f"📊 Total projects loaded: {summary['total']}")
            logger.info("\n📂 Distribution by category:")
            
            for category, count in sorted(summary['by_category'].items()):
                logger.info(f"   • {category}: {count} projects")
            
            logger.info("\n" + "=" * 60)
            logger.info("🎉 All done! Projects loaded to cache.")
            logger.info("=" * 60)
        else:
            # If parsing failed, check cache
            if summary['total'] > 0:
                logger.info("=" * 60)
                logger.info("⚠️  Parsing failed, but found cached projects")
                logger.info("=" * 60)
                logger.info(f"📊 Total projects in cache: {summary['total']}")
                logger.info("\n📂 Distribution by category:")
                
                for category, count in sorted(summary['by_category'].items()):
                    logger.info(f"   • {category}: {count} projects")
                    
                logger.info("\n" + "=" * 60)
                logger.info("Using cached data")
                logger.info("=" * 60)
            else:
                logger.error("=" * 60)
                logger.error("❌ Error: no cache data and parsing failed")
                logger.error("Check internet connection and https://projects.mospolytech.ru/")
                logger.error("=" * 60)
    
    except Exception as e:
        logger.error(f"❌ Critical error: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(initialize_projects())
