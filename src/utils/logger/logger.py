import logging, traceback
from pathlib import Path
from colorama import init, Fore, Style


init(autoreset=True)

root_dir = Path(__file__).resolve().parent.parent.parent
LOG_FOLDER = root_dir / "logs"
LOG_FILENAMES = {"info": "info.log", "error": "error.log", "warn": "warn.log"}


def initialize_logging() -> None:
    Path(LOG_FOLDER).mkdir(parents=True, exist_ok=True)

    for log_type, filename in LOG_FILENAMES.items():
        logger = logging.getLogger(log_type)

        # Avoid adding multiple handlers to the same logger
        if not logger.hasHandlers():
            if log_type == "info":
                logger.setLevel(logging.INFO)
            elif log_type == "error":
                logger.setLevel(logging.ERROR)
            else:
                logger.setLevel(logging.WARNING)

            # File handler
            file_handler = logging.FileHandler(Path(LOG_FOLDER) / filename)
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            logger.addHandler(file_handler)

            # Console handler with color
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(ColorFormatter())
            logger.addHandler(console_handler)


class ColorFormatter(logging.Formatter):
    def format(self, record):
        if record.levelno == logging.INFO:
            record.msg = Fore.GREEN + record.msg + Style.RESET_ALL
        elif record.levelno == logging.WARNING:
            record.msg = Fore.YELLOW + record.msg + Style.RESET_ALL
        elif record.levelno == logging.ERROR:
            record.msg = Fore.RED + record.msg + Style.RESET_ALL
        return super().format(record)


def custom_logger(message, log_type="info"):
    if log_type not in LOG_FILENAMES:
        raise ValueError("Invalid log type. Supported types: info, error, warn")

    logger = logging.getLogger(log_type)
    if log_type == "info":
        logger.info(message)
    elif log_type == "error":
        traceback_message = traceback.format_exc()
        logger.error(f"{message}\n{traceback_message}")
    else:
        logger.warning(message)
