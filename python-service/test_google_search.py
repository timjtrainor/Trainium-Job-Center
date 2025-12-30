import os
import sys
import pandas as pd
from datetime import datetime, timedelta

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.jobspy.scraping import scrape_jobs_sync

def test_google_scrape():
    # Use a simpler query to check if jobspy is working at all
    query = '"Product Manager" "Engineering Manager" remote'
    
    print(f"--- Testing Google Search Query ---")
    print(f"Query: {query}")
    print(f"Time: {datetime.now().isoformat()}")
    
    payload = {
        "site_name": "google",
        "google_search_term": query,
        "results_wanted": 20
    }
    
    # Run the scrape (min_pause=1 to be safe but quick)
    result = scrape_jobs_sync(payload, min_pause=1, max_pause=3)
    
    print(f"\nStatus: {result.get('status')}")
    print(f"Message: {result.get('message')}")
    print(f"Jobs found: {result.get('total_found', 0)}")
    
    jobs = result.get("jobs", [])
    if jobs:
        print("\n--- Results Preview ---")
        for i, job in enumerate(jobs[:5]):
            print(f"{i+1}. {job.get('title')} at {job.get('company')}")
            print(f"   URL: {job.get('job_url')}")
            print(f"   Posted: {job.get('date_posted')}")
            print("-" * 20)
    else:
        print("\nNo jobs were returned. This might be because:")
        print("1. The query is too restrictive.")
        print("2. Google Jobs (the target of jobspy) doesn't catch these 'site:' searches well.")
        print("3. Rate limiting/bot detection by Google.")

if __name__ == "__main__":
    test_google_scrape()
