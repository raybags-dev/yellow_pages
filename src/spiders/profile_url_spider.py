import asyncio
from pathlib import Path
import re,random, csv
from urllib.parse import quote
from src.utils.task_utils.loader import emulator
from playwright_stealth import stealth_async
from playwright.async_api import async_playwright, Error as PlaywrightError
from middlewares.errors.error_handler import handle_exceptions
from src.utils.logger.logger import custom_logger, initialize_logging
from src.utils.browser_launcher import browser_args, viewport
from bs4 import BeautifulSoup

initialize_logging()


@handle_exceptions
def load_base_urls(depth=None):
    base_urls_source_path = Path(__file__).resolve().parent.parent.parent / 'base_urls'
    txt_files = list(base_urls_source_path.glob('*.txt'))

    if txt_files:
        all_endpoints = []
        for file in txt_files:
            with file.open('r', encoding='utf-8') as f:
                endpoints = [line.strip() for line in f.readlines()]
                original_count = len(endpoints)
                if depth is not None and depth > 0:
                    endpoints = endpoints[:depth]  # Limit the number of endpoints based on the provided depth
                    custom_logger(f"Loaded {depth} profile endpoints from {file.name}", log_type="info")
                else:
                    custom_logger(f"Loaded all available {original_count} profile endpoints from {file.name}",
                                  log_type="info")
                all_endpoints.append((file.stem, endpoints))
        return all_endpoints
    else:
        custom_logger("No valid profile_base URLs to process.", log_type="info")
        return []


@handle_exceptions
async def process_url(page, url, retries=3):
    attempt = 0
    while attempt < retries:
        try:
            await page.goto(url, timeout=60000)
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            container = soup.select_one('div#results-box div.relative ol.result-items')
            endpoints = []

            if container:
                for item in container.find_all('li', class_='result-item'):
                    data_href = item.get('data-href')
                    if data_href:
                        endpoints.append(data_href)

            return endpoints
        except PlaywrightError as e:
            attempt += 1
            custom_logger(f"Error processing URL {url} (attempt {attempt}): {str(e)}", log_type="error")
            if attempt >= retries:
                custom_logger(f"Failed to process URL {url} after {retries} attempts.", log_type="error")
                return []
            await asyncio.sleep(randomize_wait_time(1, 3))


def randomize_wait_time(min_time, max_time):
    return min_time + (max_time - min_time) * random.random()


@handle_exceptions
async def collect_profile_endpoints(enabled=False, depth=None) -> bool:
    if not enabled:
        custom_logger("Profile endpoint collection disabled!.", log_type="info")
        return False

    endpoints = load_base_urls(depth)
    if not endpoints:
        custom_logger("No endpoints found", log_type="info")
        return False

    # Limit the number of endpoints to depth
    if depth is not None and depth > 0:
        endpoints = [(name, urls[:depth]) for name, urls in endpoints]

    async with async_playwright() as p:
        emulator(message="scraping profile urls...", is_in_progress=True)

        arguments = await browser_args()
        view_port = await viewport()

        browser = await p.chromium.launch(headless=True,args=arguments)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/91.0.4472.124 Safari/537.36",
            viewport=view_port
        )

        page = await context.new_page()
        await stealth_async(page)

        data_dir = Path(__file__).resolve().parent.parent.parent / 'data/profile_endpoints'
        data_dir.mkdir(parents=True, exist_ok=True)

        for file_name, urls in endpoints:
            csv_file_path = data_dir / f"{file_name}.csv"

            all_endpoints = []
            for url in urls:
                custom_logger(f"Processing URL: {url}", log_type="info")
                extracted_endpoints = await process_url(page, url)
                all_endpoints.extend(extracted_endpoints)
                await asyncio.sleep(randomize_wait_time(0.5, 1.5))

            if all_endpoints:
                with csv_file_path.open('w', newline='', encoding='utf-8') as csvfile:
                    csvwriter = csv.writer(csvfile)
                    csvwriter.writerow(['Endpoint'])  # Write the header every time
                    for endpoint in all_endpoints:
                        updated_endpoint = f"https://www.goudengids.nl{quote(endpoint)}"
                        csvwriter.writerow([updated_endpoint])
                custom_logger(f"Profile data saved to {csv_file_path}", log_type="info")
                emulator(message="", is_in_progress=False)

    await browser.close()
    custom_logger("Profile endpoint collection completed.", log_type="info")
    return True
