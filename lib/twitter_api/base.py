"""
Base client for TwitterAPI.io.

کلاس پایه برای ارتباط با TwitterAPI.io
"""

import logging
import time
from typing import Any, Dict, List, Optional, Tuple, Union

import requests

from lib.twitter_api.exceptions import (
    TwitterAPIAuthError,
    TwitterAPIConnectionError,
    TwitterAPIError,
    TwitterAPINotFoundError,
    TwitterAPIRateLimitError,
    TwitterAPIServerError,
    TwitterAPITimeoutError,
    TwitterAPIValidationError,
)
from lib.twitter_api.utils.validators import validate_api_key


class TwitterAPIBase:
    """
    Base class for TwitterAPI.io client with low-level request handling.

    کلاس پایه برای کلاینت TwitterAPI.io با مدیریت درخواست‌های سطح پایین
    """

    DEFAULT_BASE_URL = "https://api.twitterapi.io"
    DEFAULT_TIMEOUT = 30  # seconds
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_BACKOFF_FACTOR = 0.5
    DEFAULT_API_VERSION = ""  # نسخه پیش‌فرض API (خالی برای نسخه فعلی)

    def __init__(self,
                 api_key: str,
                 base_url: Optional[str] = None,
                 api_version: Optional[str] = None,
                 timeout: Optional[int] = None,
                 max_retries: Optional[int] = None,
                 backoff_factor: Optional[float] = None,
                 logger: Optional[logging.Logger] = None):
        """
        Initialize TwitterAPIBase.

        Args:
            api_key: TwitterAPI.io API key
            base_url: Base URL for TwitterAPI.io API
            api_version: API version (e.g., "v1")
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            backoff_factor: Backoff factor for retries (exponential backoff)
            logger: Logger instance
        """
        validate_api_key(api_key)

        self.api_key = api_key
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.api_version = api_version or self.DEFAULT_API_VERSION
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self.max_retries = max_retries or self.DEFAULT_MAX_RETRIES
        self.backoff_factor = backoff_factor or self.DEFAULT_BACKOFF_FACTOR

        # آماده‌سازی URL پایه با نسخه API
        if self.api_version:
            self.base_url = f"{self.base_url}/{self.api_version}"

        # Setup logger
        self.logger = logger or logging.getLogger(__name__)

        # Setup session
        self.session = requests.Session()
        self.session.headers.update({
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

    def __enter__(self):
        """Support for context manager protocol."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up resources when used as a context manager."""
        self.session.close()

    def make_request(self,
                     method: str,
                     endpoint: str,
                     params: Optional[Dict[str, Any]] = None,
                     data: Optional[Dict[str, Any]] = None,
                     headers: Optional[Dict[str, str]] = None,
                     timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Make a request to TwitterAPI.io.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            params: Query parameters
            data: Request body for POST/PUT requests
            headers: Additional headers
            timeout: Request timeout in seconds

        Returns:
            Response data as dictionary

        Raises:
            TwitterAPIError: Base exception for all TwitterAPI.io errors
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        timeout_value = timeout or self.timeout

        # Merge headers
        request_headers = headers.copy() if headers else {}

        # Sanitize params to handle None values
        if params:
            sanitized_params = {}
            for key, value in params.items():
                if value is not None:
                    if isinstance(value, bool):
                        sanitized_params[key] = str(value).lower()
                    else:
                        sanitized_params[key] = value
            params = sanitized_params

        self.logger.debug(f"Making {method} request to {url}")
        if params:
            self.logger.debug(f"Params: {params}")

        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                    headers=request_headers,
                    timeout=timeout_value
                )
                # Log raw response for debugging
                self.logger.debug(f"Raw response for {endpoint}: {response.text}")

                # Check if the request was successful
                self._check_response(response)

                # Parse, normalize and return the response
                response_data = self._parse_response(response)
                normalized_data = self._normalize_response(endpoint, response_data)
                return normalized_data

            except TwitterAPIRateLimitError as e:
                if attempt < self.max_retries:
                    wait_time = self._calculate_backoff_time(attempt)
                    self.logger.warning(f"Rate limited. Retrying in {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
                else:
                    raise

            except (TwitterAPIConnectionError, TwitterAPIServerError) as e:
                if attempt < self.max_retries:
                    wait_time = self._calculate_backoff_time(attempt)
                    self.logger.warning(f"Request failed: {str(e)}. Retrying in {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
                else:
                    raise

            except (TwitterAPIAuthError, TwitterAPINotFoundError, TwitterAPIValidationError):
                # Don't retry these errors
                raise

            except Exception as e:
                # For unexpected errors, retry with backoff
                if attempt < self.max_retries:
                    wait_time = self._calculate_backoff_time(attempt)
                    self.logger.warning(f"Unexpected error: {str(e)}. Retrying in {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
                else:
                    raise TwitterAPIError(f"Unexpected error: {str(e)}") from e

    def _check_response(self, response: requests.Response) -> None:
        """
        Check response for errors and raise appropriate exceptions.

        Args:
            response: Response from TwitterAPI.io

        Raises:
            TwitterAPIError: If there's an error in the response
        """
        try:
            response_json = response.json() if response.content else {}
        except ValueError:
            response_json = {}

        # Check for error status in response body
        if isinstance(response_json, dict):
            # Check 'status' field if present
            if "status" in response_json and response_json["status"] == "error":
                error_message = response_json.get("message") or response_json.get("msg") or "Unknown error"
                raise TwitterAPIError(f"API error status: {error_message}", response=response_json)

        # Check HTTP status code
        if response.status_code >= 400:
            error_message = "Unknown error"

            # Try to extract error message from various formats
            for error_key in ["error", "message", "msg"]:
                if error_key in response_json:
                    error_message = str(response_json.get(error_key))
                    break

            # Check for specific error types
            if response.status_code == 401:
                raise TwitterAPIAuthError(f"Authentication error: {error_message}",
                                         status_code=response.status_code,
                                         response=response_json)

            elif response.status_code == 404:
                raise TwitterAPINotFoundError(f"Resource not found: {error_message}",
                                            status_code=response.status_code,
                                            response=response_json)

            elif response.status_code == 429:
                reset_time = None
                if "X-Rate-Limit-Reset" in response.headers:
                    try:
                        reset_time = int(response.headers["X-Rate-Limit-Reset"])
                    except (ValueError, TypeError):
                        pass

                raise TwitterAPIRateLimitError(f"Rate limit exceeded: {error_message}",
                                             status_code=response.status_code,
                                             response=response_json,
                                             reset_time=reset_time)

            elif 400 <= response.status_code < 500:
                raise TwitterAPIValidationError(f"Client error: {error_message}",
                                              status_code=response.status_code,
                                              response=response_json)

            elif response.status_code >= 500:
                raise TwitterAPIServerError(f"Server error: {error_message}",
                                          status_code=response.status_code,
                                          response=response_json)

            else:
                raise TwitterAPIError(f"API error: {error_message}",
                                    status_code=response.status_code,
                                    response=response_json)

    def _parse_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Parse response from TwitterAPI.io.

        Args:
            response: Response from TwitterAPI.io

        Returns:
            Response data as dictionary

        Raises:
            TwitterAPIError: If there's an error parsing the response
        """
        if not response.content:
            return {}

        try:
            return response.json()
        except ValueError as e:
            raise TwitterAPIError(f"Invalid JSON response: {response.text}") from e

    def _normalize_response(self, endpoint: str, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize response data from different endpoints to have a consistent structure.

        This handles inconsistencies between documented API structure and actual responses.
        """
        if not isinstance(response_data, dict):
            return response_data

        normalized = response_data.copy()

        # Normalize user/last_tweets response - complex structure
        if endpoint.endswith("/user/last_tweets") and "data" in normalized:
            data = normalized.pop("data")

            # Case 1: data is a dictionary with 'tweets' and possibly 'pin_tweet'
            if isinstance(data, dict) and "tweets" in data:
                all_tweets = []

                # Add pinned tweet if exists
                if "pin_tweet" in data and data["pin_tweet"]:
                    pin_tweet = data["pin_tweet"]
                    if isinstance(pin_tweet, dict):
                        pin_tweet["is_pinned"] = True  # Mark as pinned
                        all_tweets.append(pin_tweet)
                    elif isinstance(pin_tweet, list) and pin_tweet:
                        for t in pin_tweet:
                            if isinstance(t, dict):
                                t["is_pinned"] = True  # Mark as pinned
                                all_tweets.append(t)

                # Add regular tweets
                tweets = data["tweets"]
                if isinstance(tweets, list):
                    all_tweets.extend(tweets)
                elif isinstance(tweets, dict) and tweets:
                    all_tweets.append(tweets)

                normalized["tweets"] = all_tweets

            # Case 2: data is a dictionary but doesn't have 'tweets' (treat as single tweet)
            elif isinstance(data, dict) and "tweets" not in data and data:
                normalized["tweets"] = [data]

            # Case 3: data is a list
            elif isinstance(data, list):
                normalized["tweets"] = data

            # Default: empty list
            else:
                normalized["tweets"] = []

        # Normalize user/info response
        elif endpoint.endswith("/user/info") and "data" in normalized:
            normalized["user"] = normalized.pop("data")

        # Normalize batch_info_by_ids response
        elif endpoint.endswith("/user/batch_info_by_ids") and "users" in normalized:
            if not isinstance(normalized["users"], list):
                normalized["users"] = []

        # Normalize search response to ensure consistent fields
        elif endpoint.endswith("/tweet/advanced_search") and "status" not in normalized:
            normalized["status"] = "success"
            normalized["msg"] = ""

        # Normalize tweet/replies response - API actually returns 'tweets', not 'replies'
        elif endpoint.endswith("/tweet/replies") and "tweets" in normalized and "replies" not in normalized:
            # Keep tweets key intact, don't rename to avoid breaking changes
            pass

        # Make sure status and message fields exist
        if "status" not in normalized:
            normalized["status"] = "success"

        if "msg" not in normalized and "message" not in normalized:
            normalized["msg"] = ""

        return normalized

    def _calculate_backoff_time(self, attempt: int) -> float:
        """
        Calculate backoff time for retry with exponential backoff.

        Args:
            attempt: Current attempt number (0-based)

        Returns:
            Backoff time in seconds
        """
        return self.backoff_factor * (2 ** attempt)