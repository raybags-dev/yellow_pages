import threading
import time
from datetime import datetime
from colorama import init, Fore, Style

init()

class LoadingEmulator:
    def __init__(self):
        self.loading_thread = None
        self.stopped = False
        self.start_time = None
        self.end_time = None

    def emulate_loading(self, message: str = '', start_loading: bool = False):
        if start_loading:
            if message:
                print(f'{Fore.MAGENTA}{message}{Fore.RESET}')
            self.start_time = datetime.now()
            self.stopped = False
            self.loading_thread = threading.Thread(target=self.update_progress)
            self.loading_thread.start()
        else:
            self.stopped = True
            if self.loading_thread and self.loading_thread.is_alive():
                self.loading_thread.join()
            if not message:
                self.end_time = datetime.now()
                print(f'{Fore.GREEN}.........{Fore.RESET}')
                self.print_completion_message()

    def update_progress(self):
        percentage = 0
        while not self.stopped:
            current_time = datetime.now()
            start_time_str = self.start_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+0000"
            current_time_str = current_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+0000"
            print(f'\r> {percentage}% - (start_time: {start_time_str}, end_time: {current_time_str}): ', end='')
            time.sleep(0.2)  # Adjust speed of progress for demonstration
            percentage += 1

            if percentage > 95:
                percentage = 95  # Limit progress to 95% until completion

        # Display 100% upon completion
        current_time = datetime.now()
        start_time_str = self.start_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+0000"
        current_time_str = current_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+0000"
        print(f'\r> 100% - (start_time: {start_time_str}, end_time: {current_time_str}): ', end='')
        print(f' {Fore.GREEN}> Current process completed.{Fore.RESET}')
        print('\033[K', end='')

    def print_completion_message(self):
        if self.start_time and self.end_time:
            start_time_str = self.start_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+0000"
            end_time_str = self.end_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+0000"
            print(f'\r> 100% - (start_timestamp: {start_time_str}, end_timestamp: {end_time_str}): {Fore.GREEN}> Current process completed.{Fore.RESET}')


loader_instance = LoadingEmulator()


def emulator(message='', is_in_progress=False):
    if is_in_progress:
        loader_instance.emulate_loading(message=message, start_loading=True)
    else:
        loader_instance.emulate_loading(start_loading=False)
