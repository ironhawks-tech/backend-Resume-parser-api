from fastapi import APIRouter, Query, HTTPException
from typing import Dict, List
from services.job_scraper import scrape_all_jobs

router = APIRouter()

@router.get("/jobs", response_model=Dict)
def get_job_links(role: str = Query(..., min_length=2, example="backend developer")):
    """
    Search job listings URLs for a given role using Bing and Google.
    """
    if not role.strip():
        raise HTTPException(status_code=400, detail="Role query parameter is required")

    try:
        results = scrape_all_jobs(role)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to scrape jobs: {str(e)}")
