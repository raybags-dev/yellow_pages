import json
from pathlib import Path
from src.utils.logger.logger import initialize_logging, custom_logger
from middlewares.errors.error_handler import handle_exceptions

initialize_logging()

@handle_exceptions
def load_configs():
    try:
        # Ensure the path is correct relative to the script location
        config_file_path = Path(__file__).parent.parent / 'configurations' / 'configs.json'

        if not config_file_path.exists() or config_file_path.stat().st_size == 0:
            msg = f"> Error: true\n> Source: The configuration file '{config_file_path}'\n> Message: File does not exist Or is empty"
            raise Exception(msg)

        with open(config_file_path, 'r') as file:
            configs = json.load(file)

        default_region = configs.get('default_region')
        key_word_default = configs.get('key_word_default')
        run_pipeline = configs.get('run_pipeline')

        return {
            'default_region': default_region,
            'key_word_default': key_word_default,
            'run_pipeline': run_pipeline
        }

    except Exception as e:
        custom_logger(f"{e}", 'error')
        return None
