import pytest
import logging
import os
import traceback
from pathlib import Path
from src.utils.logger.logger import custom_logger
from src.utils.logger.logger import initialize_logging, custom_logger

LOG_FOLDER = Path("src/logs")
LOG_FILENAMES = {
    "info": "info.log",
    "error": "error.log",
    "warning": "warn.log",
}


def test_custom_logger_error(caplog):
    message = "Testing error logging"
    try:
        # Simulate an exception
        raise ValueError("Custom error")
    except ValueError:
        custom_logger(message, log_type="error")
    assert any(record.levelname == "ERROR" and message in record.message for record in caplog.records)


def test_invalid_log_type():
    # Test for invalid log type
    with pytest.raises(ValueError, match="Invalid log type. Supported types: info, error, warn"):
        custom_logger("Invalid log type", log_type="invalid")



