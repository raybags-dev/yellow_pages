import asyncio
from pathlib import Path
import re, random, csv, json
from src.utils.task_utils.loader import emulator
from urllib.parse import urljoin, urlparse
from src.utils.task_utils.utilities import randomize_timeout
from playwright.async_api import async_playwright, Error as PlaywrightError
from middlewares.errors.error_handler import handle_exceptions
from src.utils.logger.logger import custom_logger, initialize_logging
from bs4 import BeautifulSoup

initialize_logging()


@handle_exceptions
def load_base_urls():
    base_urls_source_path = Path(__file__).resolve().parent.parent.parent / 'base_urls'
    txt_files = list(base_urls_source_path.glob('*.txt'))

    if txt_files:
        all_endpoints = []
        for file in txt_files:
            with file.open('r', encoding='utf-8') as f:
                endpoints = [line.strip() for line in f.readlines()]
                all_endpoints.append((file.stem, endpoints))
                custom_logger(f"Loaded {len(endpoints)} endpoints from {file.name}", log_type="info")
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
async def collect_profile_endpoints(can_run=False) -> bool:
    if not can_run:
        custom_logger("Product endpoint collection disabled!.", log_type="info")
        return False

    endpoints = load_base_urls()
    if not endpoints:
        custom_logger("No endpoints found", log_type="info")
        return False

    async with async_playwright() as p:
        emulator(message="scraping profile urls...", is_in_progress=True)

        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

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
                        updated_endpoint = f"https://www.goudengids.nl{endpoint}"
                        csvwriter.writerow([updated_endpoint])
                custom_logger(f"Profile data saved to {csv_file_path}", log_type="info")
                emulator(message="", is_in_progress=False)

    await browser.close()
    custom_logger("Profile endpoint collection completed.", log_type="info")
    return True
