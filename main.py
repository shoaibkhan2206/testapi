#!/usr/bin/env python3
"""
FastAPI Job Search and Recommendation API

This API provides endpoints to generate job searches, retrieve job listings,
and get personalized internship recommendations.

Run with: uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

import json
import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Import the existing modules
try:
    import job_search
    import recommend_internships
except ImportError as e:
    print(f"Warning: Could not import required modules: {e}")
    print("Make sure job_search.py and recommend_internships.py exist in the same directory")

# Initialize FastAPI app
app = FastAPI(
    title="Job Search & Recommendation API",
    description="API for generating job searches and getting personalized internship recommendations",
    version="1.0.0"
)

# Pydantic models for request validation
class GenerateJobsRequest(BaseModel):
    title: str
    skills: List[str]
    degree: Optional[str] = None
    location: str = "India"

    class Config:
        schema_extra = {
            "example": {
                "title": "Python Developer",
                "skills": ["Python", "Django", "REST API"],
                "degree": "Computer Science",
                "location": "India"
            }
        }

# ------------------------ Endpoints ------------------------ #

@app.post("/generate")
async def generate_jobs_and_recommendations(request: GenerateJobsRequest):
    """
    Generate job listings and top internship recommendations based on user criteria.
    """
    try:
        # Step 1: Generate job listings
        print(f"Generating jobs for: {request.title} with skills: {request.skills}")
        job_search.generate_jobs(
            title=request.title,
            skills=request.skills,
            degree=request.degree,
            location=request.location
        )

        # Load the generated jobs from output.json
        if not os.path.exists("output.json"):
            raise HTTPException(status_code=500, detail="Failed to generate output.json")

        with open("output.json", "r", encoding="utf-8") as f:
            job_data = json.load(f)

        internships_list = job_data.get("internships", [])

        if not internships_list:
            raise HTTPException(status_code=500, detail="No internships found in output.json")

        # Step 2: Generate recommendations using the correct internships argument
        print("Generating recommendations from job listings...")
        recommendations_df = recommend_internships.generate_recommendations(
            internships=internships_list,
            user_skills=request.skills,
            top_k=20
        )

        # Convert top 20 recommendations to dict for API response
        top_recommendations = recommendations_df.head(20).to_dict(orient="records")

        # Step 3: Return response with jobs and recommendations
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Jobs and recommendations generated successfully",
                "data": {
                    "search_criteria": {
                        "title": request.title,
                        "skills": request.skills,
                        "degree": request.degree,
                        "location": request.location
                    },
                    "jobs_generated": internships_list,
                    "top_recommendations": top_recommendations
                }
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating jobs and recommendations: {str(e)}"
        )


@app.get("/jobs")
async def get_jobs():
    """
    Retrieve all job listings from output.json.
    """
    try:
        if not os.path.exists("output.json"):
            raise HTTPException(status_code=404, detail="output.json not found. Please call /generate first.")
        with open("output.json", "r", encoding="utf-8") as f:
            jobs_data = json.load(f)
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Jobs retrieved successfully",
                "data": jobs_data
            }
        )
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Error parsing output.json: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading jobs: {str(e)}")


@app.get("/recommendations")
async def get_recommendations():
    """
    Retrieve top internship recommendations from recommendations.json.
    """
    try:
        if not os.path.exists("recommendations.json"):
            raise HTTPException(status_code=404, detail="recommendations.json not found. Please call /generate first.")
        with open("recommendations.json", "r", encoding="utf-8") as f:
            recommendations_data = json.load(f)
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Recommendations retrieved successfully",
                "data": recommendations_data
            }
        )
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Error parsing recommendations.json: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading recommendations: {str(e)}")


@app.get("/")
async def root():
    return JSONResponse(
        status_code=200,
        content={
            "message": "Job Search & Recommendation API",
            "version": "1.0.0",
            "endpoints": {
                "POST /generate": "Generate jobs and recommendations",
                "GET /jobs": "Get all job listings",
                "GET /recommendations": "Get top recommendations",
                "GET /docs": "Interactive API docs",
                "GET /redoc": "Alternative API docs"
            },
            "usage": {
                "generate_example": {
                    "method": "POST",
                    "url": "/generate",
                    "body": {
                        "title": "Python Developer",
                        "skills": ["Python", "Django", "REST API"],
                        "degree": "Computer Science",
                        "location": "India"
                    }
                }
            }
        }
    )


@app.get("/health")
async def health_check():
    return JSONResponse(
        status_code=200,
        content={"status": "healthy", "message": "API is running successfully"}
    )


# ------------------------ Error handlers ------------------------ #
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"status": "error", "message": "Endpoint not found", "detail": "The requested endpoint does not exist"}
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "Internal server error", "detail": "An unexpected error occurred"}
    )


# ------------------------ Run API ------------------------ #
if __name__ == "__main__":
    import uvicorn
    print("Starting Job Search & Recommendation API...")
    print("API Docs: http://localhost:8000/docs")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
