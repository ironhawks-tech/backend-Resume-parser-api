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

class LinkedINJobScraper:
    def __init__(self):
        self.user_agents = self._load_user_agents()
        self.jobs_per_page = 25
        self.max_retries = 3
        self.timeout = 60000
        self.db = self._init_db()
        self.seen_links = set()

    def _load_user_agents(self):
        try:
            file_path = Path(__file__).parent / "user_agents_list.txt"
            with open(file_path, 'r', encoding='utf-8') as f:
                agents = [line.strip() for line in f if line.strip()]
            return agents if agents else self._get_default_agents()
        except Exception as e:
            print(f"Failed to load user agents: {str(e)}")
            return self._get_default_agents()

    def _get_default_agents(self):
        return [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"
        ]

    def _init_db(self):
        client = MongoClient(os.getenv("MONGO_URI", "mongodb://mongodb:27017"))
        db = client[os.getenv("MONGO_DB_NAME", "resume_parser_db")]
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
                            if not href.startswith('http'):
                                 href = urljoin('https://www.linkedin.com', href)
                            clean_url = href.split('?')[0]
                            if clean_url not in self.seen_links:
                                job_links.add(clean_url)
                                self.seen_links.add(clean_url)
                                if len(job_links) >= max_results:
                                    await browser.close()
                                    return list(job_links)
                    
                    await asyncio.sleep(random.uniform(2, 4))
                
            except Exception as e:
                print(f"Error during scraping: {str(e)}")
            finally:
                await browser.close()
        
        return list(job_links)[:max_results]

    async def get_job_details(self, url):
        try:
            headers = {
                "User-Agent": random.choice(self.user_agents),
                "Accept-Language": "en-US,en;q=0.9",
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            title = soup.title.string.split("|")[0].strip() if soup.title else "No Title"
            company = "Unknown"
            location = "India"
            description = ""
            
            script_tag = soup.find('script', type='application/ld+json')
            if script_tag:
                try:
                    data = json.loads(script_tag.string)
                    company = data.get('hiringOrganization', {}).get('name', company)
                    location = data.get('jobLocation', {}).get('address', {}).get('addressLocality', location)
                    description = data.get('description', description)
                except json.JSONDecodeError:
                    pass
            
            if not description:
                description_div = soup.find('div', {'class': 'description__text'})
                if description_div:
                    description = description_div.get_text(strip=True)
            
            job_data = {
                "title": title[:200],
                "company": company[:100],
                "location": location[:100],
                "url": url,
                "description": description[:5000],
                "source": "LinkedIn",
                "country": "India",
                "timestamp": datetime.now(),
                
            }
            
            # Store only job details (no user info)
            self.db.update_one(
                {"url": job_data["url"]},
                {"$set": job_data},
                upsert=True
            )
            
            return job_data
            
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return None

    async def scrape_all_jobs(self, role, max_results=100):
        self.seen_links = set()
        try:
            job_links = await self.scrape_linkedin_jobs(role, max_results)
            
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
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now()
            }
  
