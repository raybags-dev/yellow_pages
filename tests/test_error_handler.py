import pytest
from unittest.mock import patch
from src.utils.logger.logger import initialize_logging, custom_logger
from middlewares.errors.error_handler import handle_exceptions

@handle_exceptions
def test_function_no_exception():
    return "Success"


@handle_exceptions
def test_function_with_exception():
    raise ValueError("An error occurred")


@handle_exceptions
def test_function_with_args(a, b):
    return a + b


@handle_exceptions
def test_function_with_kwargs(a, b=5):
    return a + b


def test_handle_exceptions_no_exception():
    result = test_function_no_exception()
    assert result == "Success"


def test_handle_exceptions_with_args():
    result = test_function_with_args(3, 4)
    assert result == 7


def test_handle_exceptions_with_kwargs():
    result = test_function_with_kwargs(a=3, b=2)
    assert result == 5

    result = test_function_with_kwargs(a=3)
    assert result == 8
