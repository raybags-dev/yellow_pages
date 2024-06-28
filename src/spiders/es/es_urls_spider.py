import asyncio
from pathlib import Path
import re, random, csv
from urllib.parse import quote
from src.utils.task_utils.loader import emulator
from playwright_stealth import stealth_async
from headers.headers import Headers
from playwright.async_api import async_playwright, Error as PlaywrightError
from middlewares.errors.error_handler import handle_exceptions
from src.utils.logger.logger import custom_logger, initialize_logging
from src.utils.browser_launcher import browser_args, viewport
from bs4 import BeautifulSoup

initialize_logging()


@handle_exceptions
def es_load_base_urls(depth=None):
    base_urls_source_path = Path(__file__).resolve().parent.parent.parent.parent / 'data' / 'es_profile_endpoints'
    txt_files = list(base_urls_source_path.glob('es_*.txt'))

    if txt_files:
        all_endpoints = []
        for file in txt_files:
            with file.open('r', encoding='utf-8') as f:
                endpoints = [line.strip() for line in f.readlines()]
                original_count = len(endpoints)
                if depth is not None and depth > 0:
                    print(depth)
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
async def es_process_url(page, url, retries=3):
    attempt = 0
    while attempt < retries:
        try:
            await page.goto(url, timeout=60000)
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            container = soup.select_one('div.bloque-central .central div[itemscope]')
            endpoints = []

            if container:
                for item in container.find_all('a', {'data-omniclick': 'name'}):
                    data_href = item.get('href')
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
async def es_collect_profile_endpoints(enabled=False, depth=None) -> bool:
    try:

        if not enabled:
            custom_logger("profile collection mode: off.", log_type="info")
            return False

        endpoints = es_load_base_urls(depth)
        if not endpoints:
            custom_logger("No endpoints found", log_type="info")
            return False

        async with async_playwright() as p:
            emulator(message="scraping profile urls...", is_in_progress=True)
            headers = Headers()

            arguments = await browser_args()
            view_port = await viewport()

            browser = await p.chromium.launch(
                headless=True,
                args=arguments
            )
            context = await browser.new_context(extra_http_headers=headers.es_profile_list(),viewport=view_port)
            page = await context.new_page()
            await stealth_async(page)

            data_dir = Path(__file__).resolve().parent.parent.parent.parent / 'data' / 'es_profile_urls'
            data_dir.mkdir(parents=True, exist_ok=True)

            for file_name, urls in endpoints:
                csv_file_path = data_dir / f"es_{file_name}.csv"

                all_endpoints = []
                for url in urls:
                    custom_logger(f"Processing url: {url}", log_type="info")
                    extracted_endpoints = await es_process_url(page, url)
                    all_endpoints.extend(extracted_endpoints)
                    await asyncio.sleep(randomize_wait_time(0.5, 1.5))

                if all_endpoints:
                    with csv_file_path.open('w', newline='', encoding='utf-8') as csvfile:
                        csvwriter = csv.writer(csvfile)
                        csvwriter.writerow(['Endpoint'])  # Write the header every time
                        for endpoint in all_endpoints:
                            csvwriter.writerow([endpoint])
                    custom_logger(f"Profile data saved to {csv_file_path}", log_type="info")
                    emulator(message="", is_in_progress=False)

        await browser.close()
        custom_logger("Profile endpoint collection completed.", log_type="info")
        return True
    except Exception as e:
        custom_logger(f"Something went wrong in <es_collect_profile_endpoints>\n {e}", log_type="warn")
        return False
