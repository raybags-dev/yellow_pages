import json
from pathlib import Path
from src.utils.logger.logger import initialize_logging, custom_logger
from middlewares.errors.error_handler import handle_exceptions


initialize_logging()

@handle_exceptions
def load_configs():
    try:
        config_file_path = Path(__file__).parent.parent / 'configurations' / 'configs.json'

        if not config_file_path.exists() or config_file_path.stat().st_size == 0:
            msg = f"> Error: true\n> Source: The configuration file '{config_file_path}'\n> Message: File does not exist or is empty"
            raise Exception(msg)

        with open(config_file_path, 'r') as file:
            configs = json.load(file)

        required_keys = ['key_word_default', 'country']
        for key in required_keys:
            if not configs.get(key):
                msg = f"> Error: true\n> Source: Configuration\n> Message: '{key}' is missing or empty"
                raise Exception(msg)

        # Validate and convert run_pipeline to boolean
        run_pipeline = configs.get('run_pipeline')
        if not isinstance(run_pipeline, bool):
            if isinstance(run_pipeline, str):
                if run_pipeline.lower() == 'true':
                    run_pipeline = True
                elif run_pipeline.lower() == 'false':
                    run_pipeline = False
                else:
                    raise ValueError("Invalid value for 'run_pipeline'. Must be a boolean.")
            else:
                raise ValueError("Invalid type for 'run_pipeline'. Must be a boolean.")

        depth = configs.get('depth')
        if isinstance(depth, str):
            if depth.lower() in ["none", "null"]:
                depth = None
            else:
                try:
                    depth = int(depth)
                except ValueError:
                    depth = 1
        elif depth is None:
            depth = 1
        elif not isinstance(depth, int):
            msg = "> Error: true\n> Source: Configuration\n> Message: 'depth' must be an integer or null"
            raise Exception(msg)

        configs['depth'] = depth
        configs['run_pipeline'] = run_pipeline

        return {
            'default_region': configs.get('default_region'),
            'key_word_default': configs['key_word_default'],
            'run_pipeline': configs['run_pipeline'],
            'country': configs['country'],
            'depth': configs['depth']
        }

    except Exception as e:
        custom_logger(f"{e}", 'warn')
        return None
