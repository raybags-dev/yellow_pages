import asyncio
import sys
from src.utils.task_utils.loader import emulator
from ochestrator.ochestrator import load_configs
from src.spiders.base_url_spider import collect_regional_search_endpoints
from src.spiders.profile_url_spider import collect_profile_endpoints
from src.spiders.es.es_paginator import e_search_endpoints
from src.spiders.es.es_urls_spider import es_collect_profile_endpoints
from src.spiders.es.es_profiles import EsMainProfileProcessor
from src.spiders.profiler_spider import MainProfileProcessor
from src.utils.logger.logger import custom_logger

configs = load_configs()

if not configs:
    custom_logger("Failed to load configurations. Exiting the application.", log_type="error")
    sys.exit(1)

run_pipeline = configs['run_pipeline']
country = configs['country']
max_depth = configs['depth']


async def main():
    try:
        if country == 'nl':
            processor = MainProfileProcessor()
            try:
                if run_pipeline:
                    custom_logger(f"running pipeline {country} pipeline...", 'info')
                    paging_ready = await collect_regional_search_endpoints(enabled=True)
                    if paging_ready:
                        urls_available = await collect_profile_endpoints(enabled=True, depth=max_depth)
                        if urls_available:
                            await processor.run_nl_worker(enabled=True, save_to_s3=False, save_to_local=True)
                else:
                    await collect_regional_search_endpoints(enabled=False)
                    await collect_profile_endpoints(enabled=False, depth=max_depth)
                    await processor.run_nl_worker(enabled=False,  save_to_s3=False, save_to_local=True)
            except Exception as e:
                custom_logger(f"An error occurred during NL execution: {e}", log_type="error")
            finally:
                emulator(is_in_progress=False)

        elif country == 'es':
            processor = EsMainProfileProcessor()
            try:
                if run_pipeline:
                    custom_logger(f"running pipeline {country} pipeline...", "info")
                    es_paging_ready = await e_search_endpoints(enabled=True)
                    if es_paging_ready:
                        es_endpoints_ready = await es_collect_profile_endpoints(enabled=True, depth=max_depth)
                        if es_endpoints_ready:
                            await (processor
                                   .es_start(enabled=True, save_to_s3=False, save_to_local=True))
                else:
                    await e_search_endpoints(enabled=False)
                    await es_collect_profile_endpoints(enabled=False, depth=max_depth)
                    await (processor.es_start(enabled=False, save_to_s3=False, save_to_local=True))

            except Exception as e:
                custom_logger(f"An error occurred during ES execution: {e}", log_type="error")
            finally:
                emulator(is_in_progress=False)
        else:
            custom_logger(f"Sorry this country is not supported - opts: (nl|es)", log_type="warn")
            sys.exit(1)

    except Exception as e:
        custom_logger(f"An unexpected error occurred in the main function: {e}", log_type="error")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
