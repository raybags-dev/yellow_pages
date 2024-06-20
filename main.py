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


async def main():
    if country == 'nl':
        processor = MainProfileProcessor()
        try:
            if run_pipeline:
                paging_ready = await collect_regional_search_endpoints(can_run=True)
                if paging_ready:
                    urls_available = await collect_profile_endpoints(can_run=True)
                    if urls_available:
                        await processor.run_profilers_main_worker(enable_processing=True, save_to_s3=False,
                                                                  save_to_local=True)
            else:
                await collect_regional_search_endpoints(can_run=False)
                await collect_profile_endpoints(can_run=False)
                await processor.run_profilers_main_worker(enable_processing=False, save_to_s3=False,
                                                          save_to_local=True)
        except Exception as e:
            custom_logger(f"An error occurred during execution: {e}", log_type="error")
        finally:
            emulator(is_in_progress=False)

    elif country == 'es':
        processor = EsMainProfileProcessor()
        try:
            if run_pipeline:
                es_paging_ready = await e_search_endpoints(can_run=True)
                if es_paging_ready:
                    es_endpoints_ready = await es_collect_profile_endpoints(can_run=True)
                    if es_endpoints_ready:
                        await (processor
                               .es_run_profilers_main_worker(enable_processing=True,
                                                             save_to_s3=False,
                                                             save_to_local=True))
            else:
                await e_search_endpoints(can_run=False)
                await es_collect_profile_endpoints(can_run=False)
                await (processor
                       .es_run_profilers_main_worker(enable_processing=True,
                                                     save_to_s3=False,
                                                     save_to_local=True))

        except Exception as e:
            custom_logger(f"An error occurred during execution: {e}", log_type="error")
        finally:
            emulator(is_in_progress=False)
    else:
        custom_logger(f"Sorry this country is not supported - opts: (nl|es)", log_type="warn")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
