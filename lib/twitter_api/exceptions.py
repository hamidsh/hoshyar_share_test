"""
Custom exceptions for TwitterAPI.io client.

کلاس‌های استثنا برای مدیریت خطاهای TwitterAPI.io
"""

class TwitterAPIError(Exception):
    """Base exception for all TwitterAPI.io errors."""

    def __init__(self, message, status_code=None, response=None, request=None):
        self.message = message
        self.status_code = status_code
        self.response = response
        self.request = request
        super().__init__(self.message)


class TwitterAPIConnectionError(TwitterAPIError):
    """Raised when there is a connection error with TwitterAPI.io."""
    pass


class TwitterAPITimeoutError(TwitterAPIConnectionError):
    """Raised when a request to TwitterAPI.io times out."""
    pass


class TwitterAPIRateLimitError(TwitterAPIError):
    """Raised when TwitterAPI.io rate limit is exceeded."""

    def __init__(self, message, status_code=429, response=None, request=None, reset_time=None):
        self.reset_time = reset_time
        super().__init__(message, status_code, response, request)


class TwitterAPIAuthError(TwitterAPIError):
    """Raised when there is an authentication error with TwitterAPI.io."""
    pass


class TwitterAPINotFoundError(TwitterAPIError):
    """Raised when a resource is not found on TwitterAPI.io."""
    pass


class TwitterAPIValidationError(TwitterAPIError):
    """Raised when there is a validation error with TwitterAPI.io."""
    pass


class TwitterAPIServerError(TwitterAPIError):
    """Raised when TwitterAPI.io returns a server error."""
    pass


class TwitterAPIPaginationError(TwitterAPIError):
    """Raised when there is an error with pagination in TwitterAPI.io."""
    pass