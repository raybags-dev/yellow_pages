import asyncio
import csv
import io
from pathlib import Path
import aiofiles
from playwright.async_api import async_playwright, Error as PlaywrightError
from playwright._impl._errors import TargetClosedError
from headers.headers import Headers
from playwright_stealth import stealth_async
from src.utils.storage.storage_hundler import save_stream_to_s3
from middlewares.errors.error_handler import handle_exceptions
from src.utils.task_utils.utilities import generate_uuid
from src.utils.logger.logger import custom_logger, initialize_logging
from src.utils.parsers.parse_profile import extract_profile_data
from src.utils.task_utils.handle_cookies import handle_cookies
from src.utils.task_utils.loader import emulator
from src.utils.browser_launcher import browser_args, viewport


initialize_logging()

DATA_DIR = Path(__file__).resolve().parent.parent.parent / 'data' / 'profile_data'
if not DATA_DIR.exists():
    DATA_DIR.mkdir()


class MainProfileProcessor:
    def __init__(self, save_to_s3=False, save_to_local=True):
        self.data_dir = DATA_DIR
        self.success_count = 0
        self.retries = []
        self.save_to_s3 = save_to_s3
        self.save_to_local = save_to_local

    @handle_exceptions
    async def load_profile_endpoints_csv_files(self):
        base_dir = Path(__file__).resolve().parent.parent.parent / 'data' / 'profile_endpoints'
        if not base_dir.exists() or not base_dir.is_dir():
            custom_logger(f"The directory {base_dir} does not exist or is not a directory.", log_type="error")
            return []

        csv_files = list(base_dir.glob('*.csv'))
        if not csv_files:
            custom_logger("No CSV files found in the directory.", log_type="info")
            return []

        profile_url_constructs = set()
        for csv_file in csv_files:
            if csv_file.stat().st_size == 0:
                custom_logger(f"The file {csv_file.name} is empty.", log_type="warning")
                continue

            with csv_file.open(mode='r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                custom_logger(f"Processing file: {csv_file.name}", log_type="info")
                for row in reader:
                    url = row['Endpoint']
                    if url:
                        profile_url_constructs.add((csv_file.stem, url))

        endpoints_list = list(profile_url_constructs)
        return list(endpoints_list)

    @handle_exceptions
    async def download_and_process_page(self, page, url):
        try:
            emulator(message="Downloading page...", is_in_progress=True)
            # Navigate to the URL with a random timeout
            await page.goto(url, timeout=60000)
            cookie_handled = await handle_cookies(page)
            if cookie_handled:
                custom_logger("Cookie consent handled successfully.", log_type="info")
            else:
                custom_logger("consent handled.", log_type="info")

            # Wait for the profile element to be available
            await page.wait_for_selector('#profile', timeout=60000)

            # Extract profile data
            content = await page.content()
            profile_data = extract_profile_data(content)

            # Ensure the function waits for extract_profile_data to finish processing
            if profile_data:
                return profile_data
            else:
                custom_logger(f"No profile data extracted from {url}.", log_type="warn")

            await page.close()

            emulator(is_in_progress=False)
            return profile_data

        except PlaywrightError as e:
            custom_logger(f"Error fetching {url}: {e}", log_type="error")
            return None
        except Exception as e:
            custom_logger(f"Exception processing {url}: {e}", log_type="error")
            return None

    @handle_exceptions
    async def save_profile_data(self, filename, data):
        emulator(message=f"Saving data object for {filename}...", is_in_progress=True)

        if self.save_to_s3:
            await self._save_to_s3(filename, data)
        elif self.save_to_local:
            await self._save_to_local(filename, data)
        else:
            custom_logger("Both save_to_s3 and save_to_local are False. No action taken.", log_type="warn")
            return

    @handle_exceptions
    async def _save_to_local(self, filename, data):
        profile_data_file = self.data_dir / f"{filename}_profile_data.csv"

        fieldnames = ['uuid', 'business_id', 'business_name', 'crawled_url', 'phone', 'address',
                      'business_url', 'email', 'description', 'business_images', 'miscellaneous_info',
                      'competitors']

        # Dynamically update fieldnames with any new keys found in the data
        for key in data.keys():
            if key not in fieldnames:
                fieldnames.append(key)

        # Save data to local CSV file
        async with aiofiles.open(profile_data_file, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if profile_data_file.stat().st_size == 0:  # Write header if file is empty
                await writer.writeheader()
            await writer.writerow(data)

        self.success_count += 1
        custom_logger(f"Saved profile data for {filename}. Total saved: {self.success_count}", log_type="info")

    @handle_exceptions
    async def _save_to_s3(self, filename, data):
        uuid_str = generate_uuid()
        fieldnames = ['uuid', 'business_id', 'business_name', 'crawled_url', 'phone', 'address',
                      'business_url', 'email', 'description', 'business_images', 'miscellaneous_info',
                      'competitors']

        # Dynamically update fieldnames with any new keys found in the data
        for key in data.keys():
            if key not in fieldnames:
                fieldnames.append(key)

        # Use StringIO to generate CSV content in memory
        csv_content = io.StringIO()
        writer = csv.DictWriter(csv_content, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(data)

        # Convert CSV content to bytes and save to S3
        data_stream = io.BytesIO(csv_content.getvalue().encode('utf-8'))
        await save_stream_to_s3(data_stream, f"{filename}_{uuid_str}.csv", content_type='text/csv')

        self.success_count += 1
        custom_logger(f"Saved profile data for {filename}. Total saved: {self.success_count}", log_type="info")

    # @handle_exceptions
    # async def process_product_endpoints(self, endpoints, save_to_s3=True, save_to_local=True, concurrency=4):
    #     async with async_playwright() as p:
    #         headers = Headers()
    #         arguments = await browser_args()
    #         view_port = await viewport()
    #
    #         browser = await p.chromium.launch(headless=True,args=arguments)
    #         context = await browser.new_context(extra_http_headers=headers.get_profile_headers(),
    #                                             viewport=view_port)
    #
    #         async def download_and_process_page(filename, url):
    #             try:
    #                 page = await context.new_page()
    #                 custom_logger(f"Downloading in progress...", log_type="info")
    #                 await page.goto(url)
    #                 page_content = await page.content()
    #                 profile_data = extract_profile_data(page_content)
    #                 emulator(message="Processing page...", is_in_progress=True)
    #                 if "error" in profile_data:
    #                     emulator(is_in_progress=False)
    #                     return {"url": url, "error": profile_data["error"], "message": profile_data["message"]}
    #                 if profile_data:
    #                     if save_to_s3:
    #                         await self._save_to_s3(filename, profile_data)
    #                     elif save_to_local:
    #                         await self._save_to_local(filename, profile_data)
    #                 emulator(is_in_progress=False)
    #                 return profile_data
    #             except Exception as e:
    #                 custom_logger(f"Failed to process page {url}: {e}", log_type="error")
    #                 return None
    #
    #         async def process_batch(batch):
    #             tasks = [download_and_process_page(filename, url) for filename, url in batch]
    #             results = await asyncio.gather(*tasks, return_exceptions=True)
    #             return results
    #
    #         batch_size = concurrency
    #         for i in range(0, len(endpoints), batch_size):
    #             current_batch = endpoints[i:i + batch_size]
    #             await process_batch(current_batch)
    #
    #         if self.retries:
    #             custom_logger(f"Retrying {len(self.retries)} failed endpoints.", log_type="info")
    #             await process_batch(self.retries)
    #             self.retries.clear()
    #
    #         await context.close()
    #         await browser.close()
    #
    #     custom_logger(f"Successfully processed {self.success_count} endpoints.")
    #     return self.success_count > 0

    @handle_exceptions
    async def process_product_endpoints(self, endpoints, save_to_s3=True, save_to_local=True, concurrency=4):
        retries = 3
        while retries > 0:
            try:
                async with async_playwright() as p:
                    headers = Headers()
                    arguments = await browser_args()
                    view_port = await viewport()

                    browser = await p.chromium.launch(headless=True, args=arguments)
                    context = await browser.new_context(extra_http_headers=headers.get_profile_headers(), viewport=view_port)

                    async def download_and_process_page(filename, url):
                        try:
                            page = await context.new_page()
                            custom_logger(f"Downloading in progress...", log_type="info")
                            await stealth_async(page)
                            await page.goto(url)
                            page_content = await page.content()
                            profile_data = extract_profile_data(page_content)
                            emulator(message="Processing page...", is_in_progress=True)
                            if "error" in profile_data:
                                emulator(is_in_progress=False)
                                return {"url": url, "error": profile_data["error"], "message": profile_data["message"]}
                            if profile_data:
                                if save_to_s3:
                                    await self._save_to_s3(filename, profile_data)
                                elif save_to_local:
                                    await self._save_to_local(filename, profile_data)
                            emulator(is_in_progress=False)
                            return profile_data
                        except TargetClosedError as e:
                            custom_logger(f"TargetClosedError processing page {url}: {e}", log_type="error")
                            self.retries.append((filename, url))
                            return None
                        except Exception as e:
                            custom_logger(f"Failed to process page {url}: {e}", log_type="error")
                            return None

                    async def process_batch(batch):
                        tasks = [download_and_process_page(filename, url) for filename, url in batch]
                        results = await asyncio.gather(*tasks, return_exceptions=True)
                        return results

                    batch_size = concurrency
                    for i in range(0, len(endpoints), batch_size):
                        current_batch = endpoints[i:i + batch_size]
                        await process_batch(current_batch)

                    if self.retries:
                        custom_logger(f"Retrying {len(self.retries)} failed endpoints.", log_type="info")
                        await process_batch(self.retries)
                        self.retries.clear()

                    await context.close()
                    await browser.close()

                custom_logger(f"Successfully processed {self.success_count} endpoints.")
                return self.success_count > 0
            except Exception as e:
                custom_logger(f"An error occurred: {e}", log_type="error")
                retries -= 1
                if retries == 0:
                    custom_logger("Max retries reached. Exiting.", log_type="error")
                    return False
                else:
                    custom_logger(f"Retrying... {retries} attempts left.", log_type="warn")
                    await asyncio.sleep(5)  # Wait before retrying

    @handle_exceptions
    async def run_nl_worker(self, enabled=True, save_to_s3=False, save_to_local=False):
        if not enabled:
            custom_logger("Profile data collection disabled!", log_type="info")
            return False

        endpoints = await self.load_profile_endpoints_csv_files()
        if not endpoints:
            custom_logger("No profile endpoints to process.", log_type="info")
            return False
        # Process endpoints and save data based on parameters
        await self.process_product_endpoints(endpoints, save_to_s3=save_to_s3, save_to_local=save_to_local)
