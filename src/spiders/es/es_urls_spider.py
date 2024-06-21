import asyncio
from pathlib import Path
import re, random, csv
from src.utils.task_utils.loader import emulator
from playwright_stealth import stealth_async
from playwright.async_api import async_playwright, Error as PlaywrightError
from middlewares.errors.error_handler import handle_exceptions
from src.utils.logger.logger import custom_logger, initialize_logging
from bs4 import BeautifulSoup


initialize_logging()


@handle_exceptions
def es_load_base_urls():
    base_urls_source_path = Path(__file__).resolve().parent.parent.parent.parent / 'data' / 'es_profile_endpoints'
    txt_files = list(base_urls_source_path.glob('es_*.txt'))

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
async def es_collect_profile_endpoints(enabled=False) -> bool:
    if not enabled:
        custom_logger("profile collection mode: off.", log_type="info")
        return False

    endpoints = es_load_base_urls()
    if not endpoints:
        custom_logger("No endpoints found", log_type="info")
        return False

    async with async_playwright() as p:
        emulator(message="scraping profile urls...", is_in_progress=True)

        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-extensions",
                "--disable-gpu",
                "--disable-setuid-sandbox",
                "--disable-software-rasterizer",
                "--disable-sync",
                "--disable-translate",
                "--disable-web-security",
                "--disable-xss-auditor",
                "--disable-notifications",
                "--disable-popup-blocking",
                "--disable-renderer-backgrounding",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-breakpad",
                "--disable-client-side-phishing-detection",
                "--disable-component-extensions-with-background-pages",
                "--disable-default-apps",
                "--disable-features=TranslateUI",
                "--disable-hang-monitor",
                "--disable-ipc-flooding-protection",
                "--disable-prompt-on-repost",
                "--disable-renderer-accessibility",
                "--disable-site-isolation-trials",
                "--disable-spell-checking",
                "--disable-webgl",
                "--enable-features=NetworkService,NetworkServiceInProcess",
                "--enable-logging",
                "--log-level=0",
                "--no-first-run",
                "--no-pings",
                "--no-zygote",
                "--password-store=basic",
                "--use-mock-keychain",
                "--single-process",
                "--mute-audio",
                "--ignore-certificate-errors"
            ]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/91.0.4472.124 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )

        page = await context.new_page()
        await stealth_async(page)

        data_dir = Path(__file__).resolve().parent.parent.parent.parent / 'data' / 'es_profile_urls'
        print('>>>>>>>>>>>>>>>> ',data_dir, '>>>>>>>>>>>>>>>')
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
