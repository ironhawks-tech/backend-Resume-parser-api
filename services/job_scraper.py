from playwright.sync_api import sync_playwright
from undetected_chromedriver import Chrome, ChromeOptions
import time, random, contextlib

def _random_user_agent():
    return random.choice([
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3) AppleWebKit/605.1.15 Version/16.1 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/113.0.5672.92 Safari/537.36",
        "Mozilla/5.0 (Linux\; Android 9\; Mi MIX 2S) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.111 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux\; Android 9\; SAMSUNG SM-G960F Build/PPR1.180610.011) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/9.4 Chrome/67.0.3396.87 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux\; Android 9\; SM-G950F Build/PPR1.180610.011\; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/76.0.3809.111 Mobile Safari/537.36 GSA/10.33.5.21.arm64",
        "Mozilla/5.0 (Linux\; Android 9\; SM-J600FN) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.111 Mobile Safari/537.36"
        ])


def scrape_bing_jobs(role: str, max_results=60):
    query = f'"{role}" jobs'
    search_url = f"https://www.bing.com/search?q={query.replace(' ', '+')}"
    job_links = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=_random_user_agent())
        page = context.new_page()
        page.goto(search_url)
        time.sleep(random.uniform(3, 6))

        anchors = page.query_selector_all('a[href^="http"]')
        for a in anchors:
            href = a.get_attribute("href")
            if href and not href.startswith("https://go.microsoft.com"):
                job_links.add(href)
                if len(job_links) >= max_results:
                    break
        browser.close()

    return list(job_links)

def scrape_google_jobs(role: str, max_results=60):
    options = ChromeOptions()
    options.add_argument("--headless")
    options.add_argument(f"user-agent={_random_user_agent()}")
    driver = Chrome(options=options, use_subprocess=True)

    query = f'"{role}" jobs site:linkedin.com OR site:indeed.com OR site:naukri.com OR site:glassdoor.com'
    search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"

    job_links = set()
    try:
        driver.get(search_url)
        time.sleep(random.uniform(3, 5))
        anchors = driver.find_elements("xpath", '//a[@href]')
        for a in anchors:
            href = a.get_attribute("href")
            if href and any(x in href for x in ["linkedin.com", "indeed.com", "naukri.com"]):
                job_links.add(href)
                if len(job_links) >= max_results:
                    break
    except Exception as e:
        print(f"[Google Error] {e}")
    finally:
        with contextlib.suppress(Exception):
            driver.quit()

    return list(job_links)

def scrape_all_jobs(role: str):
    print(f"[Google] Searching for: {role}")
    google_links = scrape_google_jobs(role)
    print(f"[Google] Found {len(google_links)} links")

    print(f"[Bing] Searching for: {role}")
    bing_links = scrape_bing_jobs(role)
    print(f"[Bing] Found {len(bing_links)} links")

    all_links = list(set(link.strip() for link in google_links + bing_links if link.strip()))
    return {
        "role": role,
        "total_links": len(all_links),
        "job_links": all_links
    }
