from fastapi import APIRouter, Query, HTTPException, Depends
from services.job_scraper import LinkedINJobScraper
from auth.dependencies import get_current_user
import asyncio
import logging
from datetime import datetime

router = APIRouter()
scraper = LinkedINJobScraper()
logger = logging.getLogger(__name__)

@router.get("/jobs")
async def search_jobs(
    role: str = Query(..., min_length=2, example="python developer"),
    max_results: int = Query(50, ge=1, le=200),
    location: str = Query("India", description="Job location"),
    current_user_email: str = Depends(get_current_user)  # Still required for auth
):
    try:
        logger.info(f"Job search for {role} in {location}")
        
        if not role.strip():
            raise HTTPException(status_code=400, detail="Role cannot be empty")
        
        await asyncio.sleep(2)  # Rate limiting
        
        try:
            results = await asyncio.wait_for(
                scraper.scrape_all_jobs(role, max_results),
                timeout=300
            )
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=504,
                detail="Job search timed out. Please try again."
            )
        
        if results["status"] == "error":
            raise HTTPException(status_code=500, detail=results["message"])
        
        return {
            "status": "success",
            "role": role,
            "location": location,
            "total_results": results["total_results"],
            "jobs": results["jobs"],
            "timestamp": datetime.now()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Job search failed. Please try again."
        )