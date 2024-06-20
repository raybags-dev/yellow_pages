import re
import asyncio
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from headers.headers import Headers
from playwright_stealth import stealth_async
from src.utils.task_utils.loader import emulator
from ochestrator.ochestrator import load_configs
from middlewares.errors.error_handler import handle_exceptions
from playwright.async_api import async_playwright, Error as PlaywrightError
from src.utils.logger.logger import custom_logger, initialize_logging

initialize_logging()

configs = load_configs()

if configs:
    keyword = configs['key_word_default']
    region = configs['default_region']
else:
    print("Failed to load configurations.")


@handle_exceptions
def is_valid_url(url):
    parsed = urlparse(url)
    return all([parsed.scheme, parsed.netloc])


def extract_total_count(count_str):
    cleaned_str = re.sub(r'[^\d]', '', count_str)
    return int(cleaned_str)


@handle_exceptions
async def e_search_endpoints(can_run=False):
    if not can_run:
        custom_logger("endpoint collection mode: off.", log_type="info")
        return False

    page_number = 1
    base_url = f'https://www.paginasamarillas.es/search/{keyword}/all-ma/all-pr/all-is/all-ci/all-ba/all-pu/all-nc/{page_number}'

    file_name = f"es_{keyword}"

    base_urls_file = Path(f'data/es_profile_endpoints/{file_name}.txt')
    base_urls_file.parent.mkdir(parents=True, exist_ok=True)

    emulator(message="Starting URL scraping process in Spain...", is_in_progress=True)

    retries = 3

    while retries > 0:
        try:
            async with async_playwright() as p:
                # Launch browser with additional arguments
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
                # Enable stealth mode
                await stealth_async(page)
                # Set extra HTTP headers
                es_url_headers_ = Headers()
                await page.set_extra_http_headers(es_url_headers_.es_get_urls_headers())

                custom_logger(f"Navigating to {base_url}", log_type="info")
                await page.goto(base_url, timeout=60000)
                await page.wait_for_selector('.first-content-listado', state='visible', timeout=30000)

                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')

                total_element = soup.select_one('span[class="h1"]')
                if total_element:
                    total_count = extract_total_count(total_element.text)
                    custom_logger(f"Total results found: {total_count}", log_type="info")
                    if total_count == 0:
                        custom_logger("No results for this search.", log_type="info")
                        emulator(is_in_progress=False)
                        return False
                else:
                    custom_logger("No results for this search.", log_type="info")
                    emulator(is_in_progress=False)
                    return False

                urls = set()

                # Generate URLs in the correct format
                total_pages = (total_count + 29) // 30  # Calculate the number of pages needed
                for page_num in range(1, total_pages + 1):
                    page_url = (f'https://www.paginasamarillas.es/search/{keyword}/all-ma/all-pr/all-is/all-ci/all-ba'
                                f'/all-pu/all-nc/{page_num}')
                    custom_logger(f"Generated URL: {page_url}", log_type="info")
                    urls.add(page_url)

                # Convert URLs to list and sort numerically
                sorted_urls = sorted(urls, key=lambda url: int(url.rsplit('/', 1)[-1]))

                if sorted_urls:
                    with base_urls_file.open('w', encoding='utf-8') as f:
                        for url in sorted_urls:
                            f.write(f"{url}\n")
                    custom_logger(f"Base URLs successfully scraped and saved to {base_urls_file}", log_type="info")
                    emulator(is_in_progress=False)
                    return True
                else:
                    custom_logger("No valid URLs found.", log_type="warn")
                    emulator(is_in_progress=False)
                    return False

        except PlaywrightError as e:
            retries -= 1
            custom_logger(f"Playwright error occurred: {str(e)}. Retries left: {retries}", log_type="error")
            if retries == 0:
                custom_logger("All retries exhausted. Please try again later or consider updating headers.",
                              log_type="error")
                emulator(is_in_progress=False)
                return False
            await asyncio.sleep(5)  # Wait before retrying
        except Exception as e:
            custom_logger(f"Unexpected error occurred: {str(e)}", log_type="error")
            emulator(is_in_progress=False)
            return False
        finally:
            try:
                await browser.close()
            except Exception:
                pass
            emulator(is_in_progress=False)

    return False
