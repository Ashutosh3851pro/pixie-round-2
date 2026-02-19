import time
from datetime import datetime, timedelta
from functools import wraps
from typing import Callable, Optional

import requests
from fake_useragent import UserAgent


def retry_on_failure(max_retries: int = 3, delay: float = 2.0):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        time.sleep(delay * (attempt + 1))
            raise last_error

        return wrapper

    return decorator


def get_user_agent() -> str:
    try:
        return UserAgent().random
    except Exception:
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


def make_request(
    url: str, timeout: int = 30, headers: Optional[dict] = None
) -> requests.Response:
    if headers is None:
        headers = {"User-Agent": get_user_agent()}
    response = requests.get(url, timeout=timeout, headers=headers)
    response.raise_for_status()
    return response


def parse_date(date_string: str) -> Optional[datetime]:
    from dateutil import parser

    try:
        return parser.parse(date_string)
    except Exception:
        return None


def is_date_expired(date_string: str, days_offset: int = 0) -> bool:
    date_obj = parse_date(date_string)
    if not date_obj:
        return False
    threshold = datetime.now() + timedelta(days=days_offset)
    return date_obj < threshold
