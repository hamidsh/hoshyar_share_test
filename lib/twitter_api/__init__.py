"""
TwitterAPI.io client for Hoshyar project.

این پکیج یک کلاینت برای TwitterAPI.io فراهم می‌کند که یک سرویس API شخص ثالث برای توییتر است
با ساختار و نقاط پایانی مخصوص به خود.
"""

__version__ = "0.1.0"

from lib.twitter_api.client import TwitterAPIClient
from lib.twitter_api.exceptions import (
    TwitterAPIAuthError,
    TwitterAPIConnectionError,
    TwitterAPIError,
    TwitterAPINotFoundError,
    TwitterAPIPaginationError,
    TwitterAPIRateLimitError,
    TwitterAPIServerError,
    TwitterAPITimeoutError,
    TwitterAPIValidationError,
)
from lib.twitter_api.models import Tweet, User, WebhookRule

__all__ = [
    "TwitterAPIClient",
    "TwitterAPIError",
    "TwitterAPIConnectionError",
    "TwitterAPITimeoutError",
    "TwitterAPIRateLimitError",
    "TwitterAPIAuthError",
    "TwitterAPINotFoundError",
    "TwitterAPIValidationError",
    "TwitterAPIServerError",
    "TwitterAPIPaginationError",
    "Tweet",
    "User",
    "WebhookRule",
]