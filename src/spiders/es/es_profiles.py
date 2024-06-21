import asyncio
import csv
import re
import io
from pathlib import Path
import aiofiles
from aiofiles import os as aiofiles_os
from playwright_stealth import stealth_async
from playwright.async_api import async_playwright, Error as PlaywrightError
from playwright._impl._errors import TargetClosedError
from headers.headers import Headers
from src.utils.storage.storage_hundler import save_stream_to_s3
from middlewares.errors.error_handler import handle_exceptions
from src.utils.task_utils.utilities import generate_uuid
from src.utils.logger.logger import custom_logger, initialize_logging
from src.utils.parsers.es_parse_profile import es_extract_profile_data
from src.utils.task_utils.loader import emulator

initialize_logging()

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / 'data' / 'es_profile_data'
if not DATA_DIR.exists():
    DATA_DIR.mkdir(parents=True)


class EsMainProfileProcessor:
    def __init__(self, save_to_s3=False, save_to_local=True):
        self.data_dir = DATA_DIR
        self.success_count = 0
        self.retries = []
        self.save_to_s3 = save_to_s3
        self.save_to_local = save_to_local

    @handle_exceptions
    async def es_load_profile_endpoints_csv_files(self):
        base_dir = Path(__file__).resolve().parent.parent.parent.parent / 'data' / 'es_profile_urls'
        if not base_dir.exists() or not base_dir.is_dir():
            custom_logger(f"The directory {base_dir} does not exist or is not a directory.", log_type="error")
            return []

        csv_files = list(base_dir.glob('es_*.csv'))
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

        return list(profile_url_constructs)

    @handle_exceptions
    async def es_download_and_process_page(self, page, url):
        try:
            emulator(message="Downloading page...", is_in_progress=True)

            # Navigate to the URL with a random timeout
            await page.goto(url, timeout=60000)

            # Wait for the profile element to be available
            await page.wait_for_selector('.data-contact', timeout=60000)

            # Extract profile data
            content = await page.content()
            profile_data = es_extract_profile_data(content)

            # Ensure the function waits for extract_profile_data to finish processing
            if profile_data:
                return profile_data
            else:
                custom_logger(f"No profile data extracted from {url}.", log_type="warn")

            # Close the page if data extraction was successful
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
    async def es_save_profile_data(self, filename, data):
        emulator(message=f"Saving data object for {filename}...", is_in_progress=True)

        if self.save_to_s3:
            await self.es_save_to_s3(filename, data)
        elif self.save_to_local:
            await self.es_save_to_local(filename, data)
        else:
            custom_logger("Both save_to_s3 and save_to_local are False. No action taken.", log_type="warn")
            return

    @handle_exceptions
    async def initialize_profile_data_file(self, filename):
        filename = re.sub(r'(?<!^)es_', '', filename)
        profile_data_file = self.data_dir / f"{filename}_profile_data.csv"

        fieldnames = [
            'uuid', 'business_id', 'profession',  'crawled_url', 'phone', 'address',
            'business_url', 'email', 'description', 'business_images', 'miscellaneous_info',
            'profile_title', 'latitude', 'longitude'
        ]

        # Rewrite the file with the headers
        async with aiofiles.open(profile_data_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            await writer.writeheader()

        custom_logger(f"Initialized profile data file for {filename}.", log_type="info")

    @handle_exceptions
    async def es_save_to_local(self, filename, data):
        filename = re.sub(r'(?<!^)es_', '', filename)
        profile_data_file = self.data_dir / f"{filename}_profile_data.csv"

        fieldnames = [
            'uuid', 'business_id', 'profession', 'crawled_url', 'phone', 'address',
            'business_url', 'email', 'description', 'business_images', 'miscellaneous_info',
            'profile_title', 'latitude', 'longitude'
        ]

        # Dynamically update fieldnames with any new keys found in the data
        for key in data.keys():
            if key not in fieldnames:
                fieldnames.append(key)

        # Check if the file exists and if it is empty
        file_exists = await aiofiles_os.path.exists(profile_data_file)
        write_header = True
        if file_exists:
            async with aiofiles.open(profile_data_file, 'r', newline='', encoding='utf-8') as readfile:
                existing_content = await readfile.read()
                if existing_content:
                    write_header = False

        # Append new data to the CSV file
        async with aiofiles.open(profile_data_file, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # Write the header only if the file is new or empty
            if write_header:
                await writer.writeheader()

            key = data.get('email') or data.get('phone') or data.get('business_name')

            # Read existing data to check for duplicates
            existing_data = {}
            try:
                async with aiofiles.open(profile_data_file, 'r', newline='', encoding='utf-8') as readfile:
                    reader = csv.DictReader(await readfile.read())
                    for row in reader:
                        row_key = row.get('email') or row.get('phone') or row.get('business_name')
                        if row_key:
                            existing_data[row_key] = row
            except FileNotFoundError:
                custom_logger(f"File {profile_data_file} not found. It will be created.", log_type="info")

            # Add new entry if it doesn't already exist
            if key and key not in existing_data:
                await writer.writerow(data)
                self.success_count += 1
                custom_logger(f"Appended profile data for {filename}. Total saved: {self.success_count}",
                              log_type="info")
            else:
                custom_logger(f"Duplicate entry found for {filename}, not appending.", log_type="info")

    @handle_exceptions
    async def es_save_to_s3(self, filename, data):
        filename = re.sub(r'(?<!^)es_', '', filename)

        uuid_str = generate_uuid()
        fieldnames = [
            'uuid', 'business_id', 'profession', 'crawled_url', 'phone', 'address',
            'business_url', 'email', 'description', 'business_images', 'miscellaneous_info',
            'profile_title', 'latitude', 'longitude'
        ]

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

    @handle_exceptions
    async def es_process_product_endpoints(self, endpoints, save_to_s3=True, save_to_local=True, concurrency=3):
        async with async_playwright() as p:
            project_headers_obj = Headers()
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

            context = await browser.new_context(extra_http_headers=project_headers_obj.es_get_urls_headers(),
                                                viewport={"width": 1920, "height": 1080})

            # Initialize the profile data file
            filename = endpoints[0][0] if endpoints else "default"
            await self.initialize_profile_data_file(filename)

            async def es_download_and_process_page(filename, url):
                try:
                    page = await context.new_page()
                    await stealth_async(page)
                    custom_logger(f"Downloading in progress...", log_type="info")
                    await page.goto(url)
                    page_content = await page.content()
                    profile_data = es_extract_profile_data(page_content)
                    emulator(message="Processing page...", is_in_progress=True)
                    if "error" in profile_data:
                        emulator(is_in_progress=False)
                        return {"url": url, "error": profile_data["error"], "message": profile_data["message"]}
                    if profile_data:
                        if save_to_s3:
                            await self.es_save_to_s3(filename, profile_data)
                        elif save_to_local:
                            await self.es_save_to_local(filename, profile_data)
                    emulator(is_in_progress=False)
                    return profile_data
                except Exception as e:
                    custom_logger(f"Failed to process page {url}: {e}", log_type="error")
                    return None

            async def es_process_batch(batch):
                tasks = [es_download_and_process_page(filename, url) for filename, url in batch]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                return results

            batch_size = concurrency
            for i in range(0, len(endpoints), batch_size):
                current_batch = endpoints[i:i + batch_size]
                await es_process_batch(current_batch)

            if self.retries:
                custom_logger(f"Retrying {len(self.retries)} failed endpoints.", log_type="info")
                await es_process_batch(self.retries)
                self.retries.clear()

            await context.close()
            await browser.close()

        custom_logger(f"Successfully processed {self.success_count} endpoints.")
        return self.success_count > 0

    @handle_exceptions
    async def es_start(self, enabled=True, save_to_s3=False, save_to_local=True):
        if not enabled:
            custom_logger("Product processing is disabled.", log_type="info")
            return False

        endpoints = await self.es_load_profile_endpoints_csv_files()
        if not endpoints:
            custom_logger("No product endpoints to process.", log_type="info")
            return False

        # Process endpoints and save data based on parameters
        try:
            await self.es_process_product_endpoints(endpoints, save_to_s3=save_to_s3, save_to_local=save_to_local)
        except TargetClosedError as e:
            custom_logger(f"Error: Browser context or page was closed unexpectedly: {e}", log_type="error")
        except Exception as e:
            custom_logger(f"An unexpected error occurred: {e}", log_type="error")
