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

        key_word_default = configs.get('key_word_default')
        if not key_word_default:
            msg = "> Error: true\n> Source: Configuration\n> Message: 'key_word_default' is missing or empty"
            raise Exception(msg)

        country = configs.get('country')
        if not country:
            msg = "> Error: true\n> Source: Configuration\n> Message: 'country' is missing or empty (options: nl|es)"
            raise Exception(msg)

        default_region = configs.get('default_region')
        key_word_default = configs.get('key_word_default')
        run_pipeline = configs.get('run_pipeline')
        country = configs.get('country')

        return {
            'default_region': default_region,
            'key_word_default': key_word_default,
            'run_pipeline': run_pipeline,
            'country': country
        }

    except Exception as e:
        custom_logger(f"{e}", 'warn')
        return None
