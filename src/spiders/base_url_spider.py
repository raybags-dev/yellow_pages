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
from src.utils.task_utils.handle_cookies import handle_cookies
from playwright.async_api import async_playwright, Error as PlaywrightError
from src.utils.logger.logger import custom_logger, initialize_logging
from src.utils.browser_launcher import browser_args, viewport


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

def clean_total_count(count_str):
    return int(re.sub(r'[^\d]', '', count_str))

@handle_exceptions
async def collect_regional_search_endpoints(enabled=False):
    if not enabled:
        custom_logger("Base-url collection disabled!", log_type="info")
        return False

    base_url = f'https://www.goudengids.nl/nl/zoeken/{keyword}'
    if region:
        base_url += f'/{region}'

    file_name = f"{keyword}"
    if region:
        file_name += f"_{region}"

    base_urls_file = Path(f'base_urls/{file_name}.txt')
    base_urls_file.parent.mkdir(parents=True, exist_ok=True)

    emulator(message="Starting URL scraping process...", is_in_progress=True)

    retries = 3

    while retries > 0:
        try:
            async with async_playwright() as p:
                # Launch browser with additional arguments
                arguments = await browser_args()
                view_port = await viewport()
                browser = await p.chromium.launch(
                    headless=True,
                    args=arguments
                )

                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                               "Chrome/91.0.4472.124 Safari/537.36",
                    viewport=view_port
                )

                page = await context.new_page()
                # Enable stealth mode
                await stealth_async(page)

                # Set extra HTTP headers
                project_headers_obj = Headers()
                await page.set_extra_http_headers(project_headers_obj.get_profile_headers())

                await handle_cookies(page)

                custom_logger(f"Navigating to {base_url}", log_type="info")
                await page.goto(base_url, timeout=60000)
                await page.wait_for_selector('.result-info__count', state='visible', timeout=30000)

                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')

                total_element = soup.select_one('.result-info__count span.count')
                if total_element:
                    total_count = clean_total_count(total_element.text)
                    custom_logger(f"\n********\n-Total search results found: << {total_count} >>"
                                  f"\n************\n", log_type="warn")
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
                for page_num in range(1, total_count // 20 + 2):  # Ensure we cover all pages
                    page_url = f'{base_url}/{page_num}'
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
                custom_logger("All retries exhausted. Please try again later or consider updating headers.", log_type="error")
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
