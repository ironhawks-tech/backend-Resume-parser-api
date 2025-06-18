import asyncio
import random
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import requests
import json
from datetime import datetime
from pymongo import MongoClient
from pathlib import Path
import os
from bson import ObjectId

class LinkedINJobScraper:
    def __init__(self):
        self.user_agents = self._load_user_agents()
        self.jobs_per_page = 25
        self.max_retries = 3
        self.timeout = 60000
        self.db = self._init_db()
        self.seen_urls = set()

    def _load_user_agents(self):
        """Load user agents from file or return defaults"""
        try:
            file_path = Path(__file__).parent / "user_agents_list.txt"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"User agent load error: {str(e)}")
        return self._get_default_agents()

    def _get_default_agents(self):
        """Fallback user agents"""
        return [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"
        ]

    def _init_db(self):
        client = MongoClient(os.getenv("MONGO_URI", "mongodb://mongodb:27017"))
        db = client[os.getenv("MONGO_DB_NAME", "resume_parser_db")]
        db.jobs.create_index([("url", 1)], unique=True)
        return db.jobs

    async def scrape_linkedin_jobs(self, role, max_results=100):
        job_links = set()
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=random.choice(self.user_agents),
                locale="en-IN",
                timezone_id="Asia/Kolkata"
            )
            
            page = await context.new_page()
            
            try:
                pages_to_scrape = (max_results // self.jobs_per_page) + 2
                
                for page_num in range(pages_to_scrape):
                    start = page_num * self.jobs_per_page
                    search_url = (
                        f"https://www.linkedin.com/jobs/search/?keywords={role.replace(' ', '%20')}"
                        f"&location=India"
                        f"&start={start}"
                    )
                    
                    await page.goto(search_url, timeout=self.timeout)
                    await page.wait_for_selector('a[href*="/jobs/view/"]', timeout=15000)
                    
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await asyncio.sleep(2)
                    
                    links = await page.query_selector_all('a[href*="/jobs/view/"]')
                    for link in links:
                        href = await link.get_attribute("href")
                        if href and "/jobs/view/" in href:
                            full_url = urljoin('https://www.linkedin.com', href.split('?')[0])
                            if full_url not in self.seen_urls:
                                job_links.add(full_url)
                                self.seen_urls.add(full_url)
                                if len(job_links) >= max_results:
                                    await browser.close()
                                    return list(job_links)
                    
                    await asyncio.sleep(random.uniform(2, 4))
                
            except Exception as e:
                print(f"Scraping error: {str(e)}")
            finally:
                await browser.close()
        
        return list(job_links)[:max_results]

    async def get_job_details(self, url):
        """Fetch job details with duplicate prevention"""
        try:
            # Check if job already exists
            existing_job = self.db.find_one({"url": url})
            if existing_job:
                print(f"Job already exists, skipping: {url}")
                return self._convert_to_json_serializable(existing_job)

            headers = {
                "User-Agent": random.choice(self.user_agents),
                "Accept-Language": "en-US,en;q=0.9",
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            job_data = {
                "title": "No Title",
                "company": "Unknown",
                "location": "India",
                "url": url,
                "source": "LinkedIn",
                "timestamp": datetime.now(),
                "description": "",
                "last_updated": datetime.now()
            }

            # Extract from JSON-LD
            script_tag = soup.find('script', type='application/ld+json')
            if script_tag:
                try:
                    data = json.loads(script_tag.string)
                    job_data.update({
                        "title": data.get('title', job_data["title"]).strip(),
                        "company": data.get('hiringOrganization', {}).get('name', job_data["company"]).strip(),
                        "location": data.get('jobLocation', {}).get('address', {}).get('addressLocality', job_data["location"]).strip(),
                        "description": self._clean_text(data.get('description', ''))
                    })
                except (json.JSONDecodeError, AttributeError) as e:
                    print(f"JSON parse error for {url}: {str(e)}")

            # HTML fallback
            if not job_data["description"]:
                description_div = soup.find('div', {'class': 'description__text'}) or \
                                soup.find('div', {'class': 'description'})
                if description_div:
                    job_data["description"] = self._clean_text(description_div.get_text())

            # Insert with duplicate protection
            try:
                result = self.db.insert_one(job_data)
                job_data["_id"] = str(result.inserted_id)  # Convert ObjectId to string
                print(f"New job stored: {url}")
                return job_data
            except Exception as e:
                print(f"Duplicate prevented for {url}: {str(e)}")
                existing = self.db.find_one({"url": url})
                return self._convert_to_json_serializable(existing)
            
        except requests.exceptions.RequestException as e:
            print(f"Request failed for {url}: {str(e)}")
        except Exception as e:
            print(f"Unexpected error processing {url}: {str(e)}")
        return None

    def _clean_text(self, text):
        """Convert to clean, formatted text without HTML"""
        if not text:
            return ""
        
        lines = []
        for line in text.splitlines():
            line = line.strip()
            if line:
                lines.append(line)
        
        text = '\n\n'.join(lines)
        text = text.replace('\u00a0', ' ')
        text = text.replace('\u2022', '•')
        
        return text

    def _convert_to_json_serializable(self, doc):
        """Convert MongoDB document to JSON-serializable format"""
        if not doc:
            return None
        doc = dict(doc)
        doc["_id"] = str(doc["_id"])  # Convert ObjectId to string
        doc["timestamp"] = doc["timestamp"].isoformat() if "timestamp" in doc else None
        doc["last_updated"] = doc["last_updated"].isoformat() if "last_updated" in doc else None
        return doc

    async def scrape_all_jobs(self, role, max_results=100):
        """Main scraping controller"""
        self.seen_urls = set()
        try:
            print(f"\nStarting scrape for: {role}")
            
            job_links = await self.scrape_linkedin_jobs(role, max_results)
            print(f"Found {len(job_links)} job links")
            
            jobs = []
            for url in job_links:
                job = await self.get_job_details(url)
                if job:
                    jobs.append(job)
                await asyncio.sleep(random.uniform(1, 3))
            
            return {
                "status": "success",
                "role": role,
                "total_results": len(jobs),
                "jobs": jobs,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }