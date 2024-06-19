import asyncio
from src.utils.task_utils.loader import emulator
from ochestrator.ochestrator import load_configs
from src.spiders.base_url_spider import collect_regional_search_endpoints
from src.spiders.profile_url_spider import collect_profile_endpoints
from src.spiders.profiler_spider import MainProfileProcessor

configs = load_configs()

if configs:
    run_pipeline = configs['run_pipeline']
else:
    print("Failed to load configurations.")


async def main():
    processor = MainProfileProcessor()
    try:
        if run_pipeline:
            paging_ready = await collect_regional_search_endpoints(can_run=True)
            if paging_ready:
                urls_available = await collect_profile_endpoints(can_run=True)
                if urls_available:
                    await processor.run_profilers_main_worker(enable_processing=True, save_to_s3=False, save_to_local=True)
        else:
            await collect_regional_search_endpoints(can_run=False)
            await collect_profile_endpoints(can_run=False)
            await processor.run_profilers_main_worker(enable_processing=False, save_to_s3=False, save_to_local=False)

    except Exception as e:
        print(f"An error occurred during execution: {e}")
        emulator(is_in_progress=False)


if __name__ == "__main__":
    asyncio.run(main())
