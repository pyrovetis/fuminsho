import functools
import time
import traceback

import schedule

from .main import run as task


def catch_exceptions(cancel_on_failure=False):
    def catch_exceptions_decorator(job_func):
        @functools.wraps(job_func)
        def wrapper(*args, **kwargs):
            try:
                return job_func(*args, **kwargs)
            except Exception:
                print(traceback.format_exc())
                if cancel_on_failure:
                    return schedule.CancelJob
                return None

        return wrapper

    return catch_exceptions_decorator


@catch_exceptions()
def safe_task():
    task()


@catch_exceptions()
def safe_task_full_scan():
    task(full_scan=True)


schedule.every().day.at("00:00", "Asia/Tehran").do(safe_task)
schedule.every().saturday.at("06:00", "Asia/Tehran").do(safe_task_full_scan)


def run():
    while True:
        schedule.run_pending()
        time.sleep(1)
