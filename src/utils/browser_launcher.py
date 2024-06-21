from src.utils.logger.logger import custom_logger


def browser_args():
    try:
        return [
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-extensions",
            "--disable-gpu",
            "--disable-setuid-sandbox",
            "--disable-software-rasterizer",
            "--disable-sync",
            "--disable-translate",
            "--disable-web-security",
            "--disable-xss-auditor",
            "--disable-notifications",
            "--disable-popup-blocking",
            "--disable-renderer-backgrounding",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-breakpad",
            "--disable-client-side-phishing-detection",
            "--disable-component-extensions-with-background-pages",
            "--disable-default-apps",
            "--disable-features=TranslateUI",
            "--disable-hang-monitor",
            "--disable-ipc-flooding-protection",
            "--disable-prompt-on-repost",
            "--disable-renderer-accessibility",
            "--disable-site-isolation-trials",
            "--disable-spell-checking",
            "--disable-webgl",
            "--enable-features=NetworkService,NetworkServiceInProcess",
            "--enable-logging",
            "--log-level=0",
            "--no-first-run",
            "--no-pings",
            "--no-zygote",
            "--password-store=basic",
            "--use-mock-keychain",
            "--single-process",
            "--mute-audio",
            "--ignore-certificate-errors"
        ]
    except Exception as e:
        custom_logger(f"Error returning browser args: {str(e)}", log_type="warn")


def viewport():
    return {"width": 1920, "height": 1080}
