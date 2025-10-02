#!/usr/bin/env python3
"""
Job Search Module for FastAPI Integration

This module provides a simple interface to generate job listings and save them to output.json.
It reuses the existing transformation logic but provides a clean API for FastAPI.
"""

import json
import requests
import re
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse, parse_qs

# Configuration - Replace with your actual SerpAPI key
SERPAPI_KEY = "4107b58ed9de5361070187c7c43e0ab143c4a6235b53f602559e71dcefd2ad38"
DEFAULT_LOCATION = "India"
DEFAULT_LANGUAGE = "en"


def extract_salary(job_data: Dict[str, Any]) -> Optional[str]:
    """Extract salary information from job data."""
    if 'detected_extensions' in job_data and 'salary' in job_data['detected_extensions']:
        return job_data['detected_extensions']['salary']
    
    if 'extensions' in job_data:
        for ext in job_data['extensions']:
            if re.search(r'₹[\d,K–-]+\s*(a\s+year|a\s+month|per\s+month|per\s+year)', ext, re.IGNORECASE):
                return ext
    return None


def extract_time_period(job_data: Dict[str, Any]) -> Optional[str]:
    """Extract time period/schedule information from job data."""
    time_indicators = []
    
    if 'detected_extensions' in job_data:
        if 'schedule_type' in job_data['detected_extensions']:
            time_indicators.append(job_data['detected_extensions']['schedule_type'])
        if 'posted_at' in job_data['detected_extensions']:
            time_indicators.append(f"Posted {job_data['detected_extensions']['posted_at']}")
    
    if 'extensions' in job_data:
        for ext in job_data['extensions']:
            if re.search(r'(full-time|part-time|internship|contract|temporary|freelance|\d+\s+months?|\d+\s+days?\s+ago)', ext, re.IGNORECASE):
                if ext not in time_indicators:
                    time_indicators.append(ext)
    
    return ', '.join(time_indicators) if time_indicators else None


def clean_description(description: str) -> str:
    """Clean and truncate description to a reasonable length."""
    if not description:
        return ""
    return re.sub(r'\s+', ' ', description.strip())


def build_serpapi_url(query: str, location: str = DEFAULT_LOCATION, api_key: str = SERPAPI_KEY, num: Optional[int] = None) -> str:
    """Build a SerpAPI URL for job search."""
    base_url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_jobs",
        "q": query,
        "location": location,
        "hl": DEFAULT_LANGUAGE,
        "api_key": api_key
    }
    if num:
        params["num"] = num
    
    param_string = "&".join([f"{k}={v}" for k, v in params.items() if v])
    return f"{base_url}?{param_string}"


def fetch_serpapi_data(url: str) -> Dict[str, Any]:
    """Fetch job data from SerpAPI URL."""
    try:
        print(f"Fetching data from SerpAPI: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('search_metadata', {}).get('status') != 'Success':
            raise Exception(f"SerpAPI request failed: {data.get('search_metadata', {}).get('status', 'Unknown error')}")
        
        jobs_count = len(data.get('jobs_results', []))
        print(f"Successfully fetched {jobs_count} job listings from SerpAPI")
        
        return data
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch data from SerpAPI: {e}")
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse JSON response from SerpAPI: {e}")


def extract_location_from_title(title: str) -> tuple:
    """Extract location from job title if it contains 'in [location]' pattern."""
    if not title:
        return title, None
    
    pattern = r'\s+in\s+([^,]+(?:,\s*[^,]+)*(?:\s*\([^)]+\))?)\s*$'
    match = re.search(pattern, title, re.IGNORECASE)
    if match:
        location = match.group(1).strip()
        clean_title = re.sub(pattern, '', title, flags=re.IGNORECASE).strip()
        return clean_title, location
    
    return title, None


def transform_job_to_internship(job_data: Dict[str, Any]) -> Dict[str, Any]:
    """Transform a single job listing to internship data format."""
    data = {}
    
    # Extract and clean job title, checking for location in title
    original_title = job_data.get('title', 'Unknown Position')
    clean_title, title_location = extract_location_from_title(original_title)
    
    # Required fields
    data["job_title"] = clean_title
    data["description"] = clean_description(job_data.get('description', ''))
    
    # Handle location
    location = title_location or job_data.get('location')
    if location:
        data["location"] = location

    # Include company and source URL
    company = None
    if 'company_name' in job_data:
        company = job_data.get('company_name')
    elif 'hiring_company' in job_data and isinstance(job_data['hiring_company'], dict):
        company = job_data['hiring_company'].get('name')

    if company:
        data['company'] = company

    source_url = job_data.get('link') or job_data.get('source') or None
    if source_url:
        data['source_url'] = source_url
    
    salary = extract_salary(job_data)
    if salary:
        data["salary"] = salary
    
    time_period = extract_time_period(job_data)
    if time_period:
        data["time_period"] = time_period
    
    return data


def generate_jobs(title: str, skills: List[str], degree: Optional[str] = None, location: str = "India"):
    """
    Generate job listings based on search criteria and save to output.json.
    
    Args:
        title: Job title to search for
        skills: List of skills to include in search
        degree: Optional degree to include in search
        location: Location to search in
    """
    try:
        # Build search queries for multiple searches
        search_queries = []
        
        # Skills-based search
        if skills:
            skills_query = f"{' '.join(skills)} internship in {location}"
            search_queries.append(("Skills-based", skills_query))
        
        # Degree-based search
        if degree:
            degree_query = f"{degree} internship in {location}"
            search_queries.append(("Degree-based", degree_query))
        
        # Main query search
        main_query = f"{title} internship in {location}"
        search_queries.append(("Main query", main_query))
        
        print(f"🚀 Running {len(search_queries)} different searches...")
        
        all_internships = []
        
        # Run each search
        for search_name, search_query in search_queries:
            try:
                print(f"⏳ {search_name}: {search_query}")
                serpapi_url = build_serpapi_url(search_query, location=location, num=20)
                data = fetch_serpapi_data(serpapi_url)
                
                jobs = data.get('jobs_results', [])
                if jobs:
                    print(f"✅ Found {len(jobs)} jobs from {search_name}")
                    
                    # Transform jobs to internship format
                    for job in jobs:
                        try:
                            internship = transform_job_to_internship(job)
                            all_internships.append(internship)
                        except Exception as e:
                            print(f"Error processing job: {e}")
                            continue
                else:
                    print(f"⚠️ No results from {search_name}")
                    
            except Exception as e:
                print(f"❌ {search_name} failed: {e}")
                continue
        
        # Remove duplicates
        seen_signatures = set()
        unique_internships = []
        for internship in all_internships:
            title_sig = (internship.get('job_title') or '').lower()
            company_sig = (internship.get('company') or '').lower()
            location_sig = (internship.get('location') or '').lower()
            signature = f"{title_sig}|{company_sig}|{location_sig}"
            
            if signature not in seen_signatures:
                seen_signatures.add(signature)
                unique_internships.append(internship)
        
        print(f"✅ Total unique internships: {len(unique_internships)} (removed {len(all_internships) - len(unique_internships)} duplicates)")
        
        # Create output structure
        output_data = {
            "internships": unique_internships,
            "total_count": len(unique_internships),
            "search_criteria": {
                "title": title,
                "skills": skills,
                "degree": degree,
                "location": location
            },
            "source": "Generated from SerpAPI job search results",
            "schema_version": "1.0"
        }
        
        # Write to output.json
        with open('output.json', 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Results saved to output.json")
        return output_data
        
    except Exception as e:
        print(f"❌ Error generating jobs: {e}")
        raise


if __name__ == "__main__":
    # Simple test
    generate_jobs(
        title="Python Developer",
        skills=["Python", "Django"],
        degree="Computer Science",
        location="India"
    )