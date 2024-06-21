from playwright.async_api import Page
from middlewares.errors.error_handler import handle_exceptions
from src.utils.logger.logger import custom_logger


@handle_exceptions
async def handle_cookies(page: Page):
    try:
        custom_logger("Checking browser readiness...", log_type="info")
        timeout_ms = 5000  # 5 seconds

        # Check if the wrapper and accept button are present
        wrapper_present = await page.evaluate('''() => {
            const wrapper = document.getElementById("cookiescript_injected_wrapper");
            return wrapper !== null;
        }''')

        accept_button_present = await page.evaluate('''() => {
            const acceptBtn = document.getElementById("cookiescript_accept");
            return acceptBtn !== null;
        }''')

        if not wrapper_present:
            custom_logger("\n____.____\n", log_type="info")
            return False

        if not accept_button_present:
            custom_logger("Cookie accept button not found.", log_type="info")
            return False

        # Click on the accept button
        custom_logger("Clicking on accept button for cookies...", log_type="info")
        await page.click("#cookiescript_accept", timeout=timeout_ms)
        custom_logger("Clicked accept button successfully.", log_type="info")

        return True

    except Exception as e:
        custom_logger(f"Error handling cookies: {str(e)}", log_type="error")
        return False
