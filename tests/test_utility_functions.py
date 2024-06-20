import pytest, unittest
import asyncio, io, sys, time
import threading
import uuid
from datetime import datetime
from colorama import Fore
from unittest.mock import AsyncMock, patch, MagicMock
from src.utils.task_utils.handle_cookies import handle_cookies
from src.utils.task_utils.loader import LoadingEmulator, emulator
from src.utils.task_utils.utilities import randomize_timeout, generate_uuid


@pytest.mark.asyncio
async def test_handle_cookies_success():
    page = AsyncMock()

    page.evaluate.side_effect = [True, True]

    with patch('src.utils.task_utils.handle_cookies.custom_logger') as mock_logger:
        result = await handle_cookies(page)

        mock_logger.assert_any_call("Checking for cookie consent overlay...", log_type="info")
        mock_logger.assert_any_call("Clicking on accept button for cookies...", log_type="info")
        mock_logger.assert_any_call("Clicked accept button successfully.", log_type="info")

        page.click.assert_awaited_with("#cookiescript_accept", timeout=5000)

        assert result is True


@pytest.mark.asyncio
async def test_handle_cookies_wrapper_not_found():
    page = AsyncMock()

    page.evaluate.side_effect = [
        False,  # wrapper_present
        True  # accept_button_present (not actually checked)
    ]

    with patch('src.utils.task_utils.handle_cookies.custom_logger') as mock_logger:
        result = await handle_cookies(page)

        mock_logger.assert_any_call("Checking for cookie consent overlay...", log_type="info")
        mock_logger.assert_any_call("Cookie script injected wrapper not found.", log_type="info")

        assert result is False


@pytest.mark.asyncio
async def test_handle_cookies_accept_button_not_found():
    page = AsyncMock()

    page.evaluate.side_effect = [
        True,  # wrapper_present
        False  # accept_button_present
    ]

    with patch('src.utils.task_utils.handle_cookies.custom_logger') as mock_logger:
        result = await handle_cookies(page)

        mock_logger.assert_any_call("Checking for cookie consent overlay...", log_type="info")
        mock_logger.assert_any_call("Cookie accept button not found.", log_type="info")

        assert result is False


@pytest.mark.asyncio
async def test_handle_cookies_exception():
    page = AsyncMock()

    page.evaluate.side_effect = Exception("Some error")

    with patch('src.utils.task_utils.handle_cookies.custom_logger') as mock_logger:
        result = await handle_cookies(page)

        mock_logger.assert_any_call("Checking for cookie consent overlay...", log_type="info")
        mock_logger.assert_any_call("Error handling cookies: Some error", log_type="error")

        assert result is False


# ============= emulator =========

class TestLoadingEmulator(unittest.TestCase):

    @patch('src.utils.task_utils.loader.time.sleep', return_value=None)
    def test_emulate_loading_start(self, mock_sleep):
        loader = LoadingEmulator()
        with patch('builtins.print') as mock_print:
            loader.emulate_loading(message='Loading started...', start_loading=True)
            self.assertIsNotNone(loader.loading_thread)
            self.assertTrue(loader.loading_thread.is_alive())
            mock_print.assert_any_call('\x1b[35mLoading started...\x1b[39m')
            # Stop the loader
            loader.emulate_loading(start_loading=False)

    @patch('src.utils.task_utils.loader.time.sleep', return_value=None)
    def test_emulate_loading_stop(self, mock_sleep):
        loader = LoadingEmulator()
        loader.emulate_loading(message='Loading started...', start_loading=True)
        with patch('builtins.print') as mock_print:
            time.sleep(0.1)  # Allow the loading to start
            loader.emulate_loading(start_loading=False)
            self.assertTrue(loader.stopped)
            self.assertIsNotNone(loader.end_time)
            mock_print.assert_any_call('\x1b[32m.........\x1b[39m')
            mock_print.assert_any_call('\033[K', end='')

    @patch('src.utils.task_utils.loader.time.sleep', return_value=None)
    def test_emulator_function_start(self, mock_sleep):
        with patch('builtins.print') as mock_print:
            emulator(message='Loading started...', is_in_progress=True)
            mock_print.assert_any_call('\x1b[35mLoading started...\x1b[39m')
            # Stop the emulator
            emulator(is_in_progress=False)

    @patch('src.utils.task_utils.loader.time.sleep', return_value=None)
    def test_emulator_function_stop(self, mock_sleep):
        emulator(message='Loading started...', is_in_progress=True)
        with patch('builtins.print') as mock_print:
            time.sleep(0.1)  # Allow the loading to start
            emulator(is_in_progress=False)
            mock_print.assert_any_call('\x1b[32m.........\x1b[39m')
            mock_print.assert_any_call('\033[K', end='')

    @patch('src.utils.task_utils.loader.time.sleep', return_value=None)
    def test_update_progress(self, mock_sleep):
        loader = LoadingEmulator()
        loader.start_time = datetime.now()
        loader.stopped = False

        with patch('builtins.print') as mock_print:
            thread = threading.Thread(target=loader.update_progress)
            thread.start()
            time.sleep(0.5)
            loader.stopped = True
            thread.join()

        self.assertTrue(loader.stopped)
        mock_print.assert_any_call(
            f'\r> 100% - (start_time: {loader.start_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]}+0000, end_time: {datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]}+0000): ',
            end=''
        )
        mock_print.assert_any_call(f' {Fore.GREEN}> Current process completed.{Fore.RESET}')
        mock_print.assert_any_call('\033[K', end='')


class TestUtilities(unittest.TestCase):
    @patch('src.utils.task_utils.utilities.random.choice')
    def test_randomize_timeout(self, mock_random_choice):
        min_timeout = 10000
        max_timeout = 30000
        mock_random_choice.return_value = 15000

        result = randomize_timeout(min_timeout, max_timeout)
        self.assertEqual(result, 15000)

        increments = 5000
        possible_timeouts = list(range(min_timeout, max_timeout + increments, increments))
        mock_random_choice.assert_called_with(possible_timeouts)

    def test_randomize_timeout_range(self):
        min_timeout = 10000
        max_timeout = 30000
        result = randomize_timeout(min_timeout, max_timeout)

        self.assertTrue(min_timeout <= result <= max_timeout)
        self.assertEqual(result % 5000, 0)  # Check if result is a multiple of 5000

    def test_generate_uuid(self):
        uuid_str = generate_uuid()
        self.assertIsInstance(uuid_str, str)

        try:
            uuid_obj = uuid.UUID(uuid_str, version=4)
        except ValueError:
            self.fail(f"{uuid_str} is not a valid UUID")

        self.assertEqual(str(uuid_obj), uuid_str)
