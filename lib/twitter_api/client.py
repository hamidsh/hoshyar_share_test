"""
Main client for TwitterAPI.io.

کلاس اصلی کلاینت TwitterAPI.io که رابط کاربری نهایی را برای استفاده از API فراهم می‌کند
"""

import datetime
import logging
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, TypeVar, Union

from lib.twitter_api.base import TwitterAPIBase
from lib.twitter_api.exceptions import TwitterAPIError, TwitterAPIValidationError
from lib.twitter_api.models import Tweet, User, WebhookRule
from lib.twitter_api.utils.date_utils import validate_time_range
from lib.twitter_api.utils.pagination import PaginatedIterator, paginate_resource
from lib.twitter_api.utils.validators import (
    validate_boolean_param,
    validate_cursor,
    validate_enum_param,
    validate_numeric_param,
    validate_required_params,
    validate_string_param,
)

T = TypeVar('T')


class TwitterAPIClient:
    """
    Client for TwitterAPI.io with high-level methods.

    این کلاس متدهای سطح بالا برای استفاده راحت از API های TwitterAPI.io را فراهم می‌کند
    """

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        api_version: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
        backoff_factor: Optional[float] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize TwitterAPIClient.

        Args:
            api_key: TwitterAPI.io API key
            base_url: Base URL for TwitterAPI.io API
            api_version: API version (e.g., "v1")
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            backoff_factor: Backoff factor for retries (exponential backoff)
            logger: Logger instance
        """
        self.base = TwitterAPIBase(
            api_key=api_key,
            base_url=base_url,
            api_version=api_version,
            timeout=timeout,
            max_retries=max_retries,
            backoff_factor=backoff_factor,
            logger=logger,
        )
        self.logger = logger or logging.getLogger(__name__)

    #
    # Search Methods
    #

    def search_tweets(
        self,
        query: str,
        query_type: str = "Latest",
        cursor: Optional[str] = None,
        max_pages: Optional[int] = None,
        max_results: Optional[int] = None,
        convert_to_models: bool = True,
    ) -> Union[List[Dict[str, Any]], List[Tweet]]:
        """
        Search for tweets using Twitter's advanced search syntax.

        Args:
            query: Search query (e.g., "from:username", "keyword", etc.)
            query_type: Type of search ("Latest" or "Top")
            cursor: Pagination cursor (use None for first page)
            max_pages: Maximum number of pages to retrieve
            max_results: Maximum number of results to return
            convert_to_models: Whether to convert results to Tweet objects

        Returns:
            List of tweets (as dictionaries or Tweet objects)

        Raises:
            TwitterAPIError: If there's an error with the API
            TwitterAPIValidationError: If parameters are invalid
        """
        # Validate parameters
        validate_string_param(query, "query")
        validate_enum_param(query_type, "queryType", ["Latest", "Top"])
        cursor = validate_cursor(cursor)

        def fetch_page(cursor: str) -> Dict[str, Any]:
            params = {
                "query": query,
                "queryType": query_type,
                "cursor": cursor,
            }
            return self.base.make_request("GET", "twitter/tweet/advanced_search", params=params)

        # Fetch and paginate results
        tweets = paginate_resource(
            fetch_page,
            "tweets",
            max_pages=max_pages,
            max_items=max_results,
            initial_cursor=cursor,
        )

        # Convert to model objects if requested
        if convert_to_models:
            return self._convert_tweets_with_authors(tweets)

        return tweets

    def search_tweets_iter(
        self,
        query: str,
        query_type: str = "Latest",
        cursor: Optional[str] = None,
        max_pages: Optional[int] = None,
        max_results: Optional[int] = None,
        convert_to_models: bool = True,
    ) -> Iterable[Union[Dict[str, Any], Tweet]]:
        """
        Search for tweets using Twitter's advanced search syntax, returning an iterator.

        This method returns an iterator that fetches pages as needed, which is
        more memory-efficient for large result sets.

        Args:
            query: Search query (e.g., "from:username", "keyword", etc.)
            query_type: Type of search ("Latest" or "Top")
            cursor: Pagination cursor (use None for first page)
            max_pages: Maximum number of pages to retrieve
            max_results: Maximum number of results to return
            convert_to_models: Whether to convert results to Tweet objects

        Returns:
            Iterator of tweets (as dictionaries or Tweet objects)

        Raises:
            TwitterAPIError: If there's an error with the API
            TwitterAPIValidationError: If parameters are invalid
        """
        # Validate parameters
        validate_string_param(query, "query")
        validate_enum_param(query_type, "queryType", ["Latest", "Top"])
        cursor = validate_cursor(cursor)

        def fetch_page(cursor: str) -> Dict[str, Any]:
            params = {
                "query": query,
                "queryType": query_type,
                "cursor": cursor,
            }
            return self.base.make_request("GET", "twitter/tweet/advanced_search", params=params)

        # Create transform function if needed
        transform_func = None
        if convert_to_models:
            def transform_func(tweet_data: Dict[str, Any]) -> Tweet:
                return self._convert_tweet_with_author(tweet_data)

        # Return iterator
        return PaginatedIterator(
            fetch_page,
            "tweets",
            transform_func=transform_func,
            max_pages=max_pages,
            max_items=max_results,
            initial_cursor=cursor,
        )

    #
    # Tweet Methods
    #

    def get_tweet_replies(
        self,
        tweet_id: str,
        since_time: Optional[Union[int, str, datetime.datetime]] = None,
        until_time: Optional[Union[int, str, datetime.datetime]] = None,
        cursor: Optional[str] = None,
        max_pages: Optional[int] = None,
        max_results: Optional[int] = None,
        convert_to_models: bool = True,
    ) -> Union[List[Dict[str, Any]], List[Tweet]]:
        """
        Get replies to a specific tweet.

        Note: According to API behavior, replies are returned in the 'tweets' field,
        not 'replies' as documented. This method handles the inconsistency.

        Note: This endpoint may return empty results even when has_next_page is true,
        which is a known API limitation.

        Args:
            tweet_id: ID of the tweet to get replies for
            since_time: Filter replies after this time (Unix timestamp, datetime, or Twitter date string)
            until_time: Filter replies before this time (Unix timestamp, datetime, or Twitter date string)
            cursor: Pagination cursor (use None for first page)
            max_pages: Maximum number of pages to retrieve
            max_results: Maximum number of results to return
            convert_to_models: Whether to convert results to Tweet objects

        Returns:
            List of reply tweets (as dictionaries or Tweet objects)

        Raises:
            TwitterAPIError: If there's an error with the API
            TwitterAPIValidationError: If parameters are invalid
        """
        # Validate parameters
        validate_string_param(tweet_id, "tweetId")
        since_timestamp, until_timestamp = validate_time_range(since_time, until_time)
        cursor = validate_cursor(cursor)

        def fetch_page(cursor: str) -> Dict[str, Any]:
            params = {
                "tweetId": tweet_id,
                "cursor": cursor,
            }

            if since_timestamp:
                params["sinceTime"] = since_timestamp

            if until_timestamp:
                params["untilTime"] = until_timestamp

            return self.base.make_request("GET", "twitter/tweet/replies", params=params)

        # Fetch and paginate results - replies are in 'tweets' field, not 'replies'
        replies = paginate_resource(
            fetch_page,
            "tweets",  # API actually returns data in 'tweets' field, not 'replies'
            max_pages=max_pages,
            max_items=max_results,
            initial_cursor=cursor,
            stop_on_empty=True,  # Stop on empty results due to API pagination inconsistency
        )

        # Convert to model objects if requested
        if convert_to_models:
            return self._convert_tweets_with_authors(replies)

        return replies

    def get_tweet_replies_iter(
        self,
        tweet_id: str,
        since_time: Optional[Union[int, str, datetime.datetime]] = None,
        until_time: Optional[Union[int, str, datetime.datetime]] = None,
        cursor: Optional[str] = None,
        max_pages: Optional[int] = None,
        max_results: Optional[int] = None,
        convert_to_models: bool = True,
    ) -> Iterable[Union[Dict[str, Any], Tweet]]:
        """
        Get replies to a specific tweet, returning an iterator.

        Note: According to API behavior, replies are returned in the 'tweets' field,
        not 'replies' as documented. This method handles the inconsistency.

        Args:
            tweet_id: ID of the tweet to get replies for
            since_time: Filter replies after this time (Unix timestamp, datetime, or Twitter date string)
            until_time: Filter replies before this time (Unix timestamp, datetime, or Twitter date string)
            cursor: Pagination cursor (use None for first page)
            max_pages: Maximum number of pages to retrieve
            max_results: Maximum number of results to return
            convert_to_models: Whether to convert results to Tweet objects

        Returns:
            Iterator of reply tweets (as dictionaries or Tweet objects)

        Raises:
            TwitterAPIError: If there's an error with the API
            TwitterAPIValidationError: If parameters are invalid
        """
        # Validate parameters
        validate_string_param(tweet_id, "tweetId")
        since_timestamp, until_timestamp = validate_time_range(since_time, until_time)
        cursor = validate_cursor(cursor)

        def fetch_page(cursor: str) -> Dict[str, Any]:
            params = {
                "tweetId": tweet_id,
                "cursor": cursor,
            }

            if since_timestamp:
                params["sinceTime"] = since_timestamp

            if until_timestamp:
                params["untilTime"] = until_timestamp

            return self.base.make_request("GET", "twitter/tweet/replies", params=params)

        # Create transform function if needed
        transform_func = None
        if convert_to_models:
            def transform_func(tweet_data: Dict[str, Any]) -> Tweet:
                return self._convert_tweet_with_author(tweet_data)

        # Return iterator - replies are in 'tweets' field, not 'replies'
        return PaginatedIterator(
            fetch_page,
            "tweets",  # API actually returns data in 'tweets' field, not 'replies'
            transform_func=transform_func,
            max_pages=max_pages,
            max_items=max_results,
            initial_cursor=cursor,
        )

    #
    # User Methods
    #

    def get_user_info(self, username: str, convert_to_model: bool = True) -> Union[Dict[str, Any], User]:
        """
        Get information about a Twitter user by username.

        Note: According to API behavior, user data is returned in the 'data' field,
        not 'user' as documented. This method handles the inconsistency.

        Args:
            username: Twitter username (without @)
            convert_to_model: Whether to convert result to User object

        Returns:
            User information (as dictionary or User object)

        Raises:
            TwitterAPIError: If there's an error with the API
            TwitterAPIValidationError: If parameters are invalid
        """
        # Validate parameters
        validate_string_param(username, "userName")

        # Make request
        params = {"userName": username}
        response = self.base.make_request("GET", "twitter/user/info", params=params)

        # Convert to model if requested
        if convert_to_model and "user" in response:
            return User.from_dict(response["user"])

        return response.get("user", {})

    def get_user_info_by_id(self, user_id: str, convert_to_model: bool = True) -> Union[Dict[str, Any], User]:
        """
        Get information about a Twitter user by user ID using batch endpoint.

        Args:
            user_id: Twitter user ID
            convert_to_model: Whether to convert result to User object

        Returns:
            User information (as dictionary or User object)

        Raises:
            TwitterAPIError: If there's an error with the API or no user found
            TwitterAPIValidationError: If parameters are invalid
        """
        validate_string_param(user_id, "userId")

        # Use batch endpoint with a single user ID
        params = {"userIds": user_id}
        response = self.base.make_request("GET", "twitter/user/batch_info_by_ids", params=params)

        # Extract user data
        users = response.get("users", [])
        if not users:
            raise TwitterAPIError(f"No user data returned for user_id: {user_id}")

        # Since we only sent one ID, take the first result
        user_data = users[0]

        # Verify the ID matches
        if user_data.get("id") != user_id:
            raise TwitterAPIError(f"Returned user ID {user_data.get('id')} does not match requested ID {user_id}")

        # Convert to model if requested
        if convert_to_model:
            return User.from_dict(user_data)

        return user_data

    def get_user_tweets(
            self,
            username: Optional[str] = None,
            user_id: Optional[str] = None,
            cursor: Optional[str] = None,
            max_pages: Optional[int] = None,
            max_results: Optional[int] = None,
            convert_to_models: bool = True,
    ) -> Union[List[Dict[str, Any]], List[Tweet]]:
        """
        Get tweets from a specific user.

        Note: According to API behavior, tweets are returned in a complex
        structure with 'pin_tweet' and 'tweets' fields. This method normalizes
        the response to provide a consistent list of tweets.

        Note: This endpoint will not return tweets that are replies. If you need
        replies, use the advanced search endpoint with the query "from:username is:reply".

        Args:
            username: Twitter username (without @)
            user_id: Twitter user ID (alternative to username)
            cursor: Pagination cursor (use None for first page)
            max_pages: Maximum number of pages to retrieve
            max_results: Maximum number of results to return
            convert_to_models: Whether to convert results to Tweet objects

        Returns:
            List of tweets (as dictionaries or Tweet objects)

        Raises:
            TwitterAPIError: If there's an error with the API
            TwitterAPIValidationError: If parameters are invalid
        """
        # Validate parameters - either username or user_id must be provided
        if username is None and user_id is None:
            raise TwitterAPIValidationError("Either username or user_id must be provided")

        if username is not None:
            validate_string_param(username, "userName")

        if user_id is not None:
            validate_string_param(user_id, "userId")

        cursor_value = validate_cursor(cursor)

        def fetch_page(current_cursor: str) -> Dict[str, Any]:
            params = {"cursor": current_cursor}
            if user_id is not None:
                params["userId"] = user_id
            else:
                params["userName"] = username
            return self.base.make_request("GET", "twitter/user/last_tweets", params=params)

        try:
            # Initialize empty result list
            tweets = []

            # Get first page
            response = fetch_page(cursor_value)
            # Check if response is a dictionary
            if not isinstance(response, dict):
                self.logger.error(f"Unexpected response type: {type(response)}, content: {response}")
                raise TwitterAPIError(f"Invalid response format from API: {response}")
            page_count = 1

            # Tweets will be normalized to the 'tweets' field by _normalize_response
            tweets.extend(response.get("tweets", []))

            # Check for more pages
            has_next_page = response.get("has_next_page", False)
            next_cursor = response.get("next_cursor", "")

            # Paginate if needed
            while (has_next_page and next_cursor and
                   (max_pages is None or page_count < max_pages) and
                   (max_results is None or len(tweets) < max_results)):
                # Get next page
                response = fetch_page(next_cursor)
                # Check if response is a dictionary
                if not isinstance(response, dict):
                    self.logger.error(f"Unexpected response type: {type(response)}, content: {response}")
                    raise TwitterAPIError(f"Invalid response format from API: {response}")
                page_count += 1

                # Add tweets from this page
                page_tweets = response.get("tweets", [])
                tweets.extend(page_tweets)

                # If this page had no tweets, stop (even if has_next_page is True)
                if not page_tweets:
                    break

                # Update pagination info
                has_next_page = response.get("has_next_page", False)
                next_cursor = response.get("next_cursor", "")

            # Truncate to max_results if needed
            if max_results is not None and len(tweets) > max_results:
                tweets = tweets[:max_results]

            # Convert to model objects if requested
            if convert_to_models:
                return self._convert_tweets_with_authors(tweets)

            return tweets

        except Exception as e:
            self.logger.error(f"Error in get_user_tweets: {str(e)}")
            raise


    def get_user_tweets_iter(
            self,
            username: Optional[str] = None,
            user_id: Optional[str] = None,
            cursor: Optional[str] = None,
            max_pages: Optional[int] = None,
            max_results: Optional[int] = None,
            convert_to_models: bool = True,
    ) -> Iterable[Union[Dict[str, Any], Tweet]]:
        """
        Get tweets from a specific user, returning an iterator.

        Note: According to API behavior, tweets are returned in the 'data' field,
        which might be a dictionary instead of a list. This iterator handles this inconsistency.

        Note: This endpoint will not return tweets that are replies. If you need
        replies, use the advanced search endpoint with the query "from:username is:reply".

        Args:
            username: Twitter username (without @)
            user_id: Twitter user ID (alternative to username)
            cursor: Pagination cursor (use None for first page)
            max_pages: Maximum number of pages to retrieve
            max_results: Maximum number of results to return
            convert_to_models: Whether to convert results to Tweet objects

        Returns:
            Iterator of tweets (as dictionaries or Tweet objects)

        Raises:
            TwitterAPIError: If there's an error with the API
            TwitterAPIValidationError: If parameters are invalid
        """
        # Validate parameters - either username or user_id must be provided
        if username is None and user_id is None:
            raise TwitterAPIValidationError("Either username or user_id must be provided")

        if username is not None:
            validate_string_param(username, "userName")

        if user_id is not None:
            validate_string_param(user_id, "userId")

        cursor_value = validate_cursor(cursor)

        # تابع تبدیل برای تبدیل داده خام به مدل Tweet
        transform_func = None
        if convert_to_models:
            def transform_func(tweet_data: Dict[str, Any]) -> Tweet:
                return self._convert_tweet_with_author(tweet_data)

        # کلاس ایتریتور سفارشی برای مدیریت ساختار خاص پاسخ
        class UserTweetsIterator:
            def __init__(self, client, username, user_id, cursor_val, max_pg, max_items, transform):
                self.client = client
                self.username = username
                self.user_id = user_id
                self.cursor = cursor_val
                self.max_pages = max_pg
                self.max_items = max_items
                self.transform = transform

                self.page_count = 0
                self.item_count = 0
                self.buffer = []
                self.buffer_index = 0
                self.has_more = True

            def __iter__(self):
                return self

            def __next__(self):
                # If we need to fetch more items
                if self.buffer_index >= len(self.buffer):
                    # Check if we've hit limits
                    if not self.has_more:
                        raise StopIteration

                    if self.max_pages is not None and self.page_count >= self.max_pages:
                        raise StopIteration

                    if self.max_items is not None and self.item_count >= self.max_items:
                        raise StopIteration

                    # Fetch next page
                    self._fetch_next_page()

                    # If we still don't have items, we're done
                    if not self.buffer:
                        raise StopIteration

                # Get next item
                item = self.buffer[self.buffer_index]
                self.buffer_index += 1
                self.item_count += 1

                # Apply transform if needed
                if self.transform:
                    return self.transform(item)

                return item

            def _fetch_next_page(self):
                # Prepare parameters
                params = {"cursor": self.cursor}
                if self.user_id is not None:
                    params["userId"] = self.user_id
                else:
                    params["userName"] = self.username

                # Make API request
                response = self.client.base.make_request("GET", "twitter/user/last_tweets", params=params)
                self.page_count += 1

                # Extract tweets (after normalization, they're in 'tweets')
                tweets = response.get("tweets", [])

                # Update state
                self.buffer = tweets
                self.buffer_index = 0
                self.has_more = response.get("has_next_page", False)
                self.cursor = response.get("next_cursor", "")

                # If this page had no tweets but has_next_page is True,
                # we'll try one more page before giving up
                if not tweets and self.has_more and self.page_count < 2:
                    self._fetch_next_page()

        # Return custom iterator
        return UserTweetsIterator(
            self,
            username,
            user_id,
            cursor_value,
            max_pages,
            max_results,
            transform_func
        )

    def get_user_mentions(
        self,
        username: str,
        since_time: Optional[Union[int, str, datetime.datetime]] = None,
        until_time: Optional[Union[int, str, datetime.datetime]] = None,
        cursor: Optional[str] = None,
        max_pages: Optional[int] = None,
        max_results: Optional[int] = None,
        convert_to_models: bool = True,
    ) -> Union[List[Dict[str, Any]], List[Tweet]]:
        """
        Get tweets mentioning a specific user.

        Args:
            username: Twitter username (without @)
            since_time: Filter mentions after this time (Unix timestamp, datetime, or Twitter date string)
            until_time: Filter mentions before this time (Unix timestamp, datetime, or Twitter date string)
            cursor: Pagination cursor (use None for first page)
            max_pages: Maximum number of pages to retrieve
            max_results: Maximum number of results to return
            convert_to_models: Whether to convert results to Tweet objects

        Returns:
            List of mentions (as dictionaries or Tweet objects)

        Raises:
            TwitterAPIError: If there's an error with the API
            TwitterAPIValidationError: If parameters are invalid
        """
        # Validate parameters
        validate_string_param(username, "userName")
        since_timestamp, until_timestamp = validate_time_range(since_time, until_time)
        cursor = validate_cursor(cursor)

        def fetch_page(cursor: str) -> Dict[str, Any]:
            params = {
                "userName": username,
                "cursor": cursor,
            }

            if since_timestamp:
                params["sinceTime"] = since_timestamp

            if until_timestamp:
                params["untilTime"] = until_timestamp

            return self.base.make_request("GET", "twitter/user/mentions", params=params)

        # Fetch and paginate results
        mentions = paginate_resource(
            fetch_page,
            "tweets",
            max_pages=max_pages,
            max_items=max_results,
            initial_cursor=cursor,
            stop_on_empty=True,  # Stop on empty results due to API pagination inconsistency
        )

        # Convert to model objects if requested
        if convert_to_models:
            return self._convert_tweets_with_authors(mentions)

        return mentions

    def get_user_followers(
        self,
        username: str,
        cursor: Optional[str] = None,
        max_pages: Optional[int] = None,
        max_results: Optional[int] = None,
        convert_to_models: bool = True,
    ) -> Union[List[Dict[str, Any]], List[User]]:
        """
        Get followers of a specific user.

        Note: According to API behavior, follower data structure differs from
        the documented structure. This method handles these differences.

        Args:
            username: Twitter username (without @)
            cursor: Pagination cursor (use None for first page)
            max_pages: Maximum number of pages to retrieve
            max_results: Maximum number of results to return
            convert_to_models: Whether to convert results to User objects

        Returns:
            List of followers (as dictionaries or User objects)

        Raises:
            TwitterAPIError: If there's an error with the API
            TwitterAPIValidationError: If parameters are invalid
        """
        # Validate parameters
        validate_string_param(username, "userName")
        cursor = validate_cursor(cursor)

        def fetch_page(cursor: str) -> Dict[str, Any]:
            params = {
                "userName": username,
                "cursor": cursor,
            }

            return self.base.make_request("GET", "twitter/user/followers", params=params)

        # Fetch and paginate results
        followers = paginate_resource(
            fetch_page,
            "followers",
            max_pages=max_pages,
            max_items=max_results,
            initial_cursor=cursor,
            stop_on_empty=True,
        )

        # Convert to model objects if requested
        if convert_to_models:
            return [User.from_dict(user_data) for user_data in followers]

        return followers

    def get_user_following(
        self,
        username: str,
        cursor: Optional[str] = None,
        max_pages: Optional[int] = None,
        max_results: Optional[int] = None,
        convert_to_models: bool = True,
    ) -> Union[List[Dict[str, Any]], List[User]]:
        """
        Get users that a specific user is following.

        Note: According to API behavior, user data structure differs from
        the documented structure. This method handles these differences.

        Args:
            username: Twitter username (without @)
            cursor: Pagination cursor (use None for first page)
            max_pages: Maximum number of pages to retrieve
            max_results: Maximum number of results to return
            convert_to_models: Whether to convert results to User objects

        Returns:
            List of following users (as dictionaries or User objects)

        Raises:
            TwitterAPIError: If there's an error with the API
            TwitterAPIValidationError: If parameters are invalid
        """
        # Validate parameters
        validate_string_param(username, "userName")
        cursor = validate_cursor(cursor)

        def fetch_page(cursor: str) -> Dict[str, Any]:
            params = {
                "userName": username,
                "cursor": cursor,
            }

            return self.base.make_request("GET", "twitter/user/followings", params=params)

        # Fetch and paginate results
        following = paginate_resource(
            fetch_page,
            "followings",
            max_pages=max_pages,
            max_items=max_results,
            initial_cursor=cursor,
            stop_on_empty=True,
        )

        # Convert to model objects if requested
        if convert_to_models:
            return [User.from_dict(user_data) for user_data in following]

        return following

    #
    # Batch Methods
    #

    def get_users_by_ids(
        self,
        user_ids: List[str],
        convert_to_models: bool = True,
    ) -> Union[List[Dict[str, Any]], List[User]]:
        """
        Get information about multiple Twitter users by user IDs.

        Args:
            user_ids: List of Twitter user IDs
            convert_to_models: Whether to convert results to User objects

        Returns:
            List of users (as dictionaries or User objects)

        Raises:
            TwitterAPIError: If there's an error with the API
            TwitterAPIValidationError: If parameters are invalid
        """
        # Validate parameters
        if not user_ids:
            raise TwitterAPIValidationError("user_ids cannot be empty")

        # Make request
        params = {"userIds": ",".join(user_ids)}
        response = self.base.make_request("GET", "twitter/user/batch_info_by_ids", params=params)

        # Convert to model objects if requested
        users = response.get("users", [])

        if convert_to_models:
            return [User.from_dict(user_data) for user_data in users]

        return users

    #
    # List Methods
    #

    def get_list_tweets(
        self,
        list_id: str,
        include_replies: bool = True,
        since_time: Optional[Union[int, str, datetime.datetime]] = None,
        until_time: Optional[Union[int, str, datetime.datetime]] = None,
        cursor: Optional[str] = None,
        max_pages: Optional[int] = None,
        max_results: Optional[int] = None,
        convert_to_models: bool = True,
    ) -> Union[List[Dict[str, Any]], List[Tweet]]:
        """
        Get tweets from a specific Twitter list.

        Args:
            list_id: ID of the Twitter list
            include_replies: Whether to include replies in the results
            since_time: Filter tweets after this time (Unix timestamp, datetime, or Twitter date string)
            until_time: Filter tweets before this time (Unix timestamp, datetime, or Twitter date string)
            cursor: Pagination cursor (use None for first page)
            max_pages: Maximum number of pages to retrieve
            max_results: Maximum number of results to return
            convert_to_models: Whether to convert results to Tweet objects

        Returns:
            List of tweets (as dictionaries or Tweet objects)

        Raises:
            TwitterAPIError: If there's an error with the API
            TwitterAPIValidationError: If parameters are invalid
        """
        # Validate parameters
        validate_string_param(list_id, "listId")
        include_replies = validate_boolean_param(include_replies, "includeReplies")
        since_timestamp, until_timestamp = validate_time_range(since_time, until_time)
        cursor = validate_cursor(cursor)

        def fetch_page(cursor: str) -> Dict[str, Any]:
            params = {
                "listId": list_id,
                "includeReplies": include_replies,
                "cursor": cursor,
            }

            if since_timestamp:
                params["sinceTime"] = since_timestamp

            if until_timestamp:
                params["untilTime"] = until_timestamp

            return self.base.make_request("GET", "twitter/list/tweets", params=params)

        # Fetch and paginate results
        tweets = paginate_resource(
            fetch_page,
            "tweets",
            max_pages=max_pages,
            max_items=max_results,
            initial_cursor=cursor,
            stop_on_empty=True,
        )

        # Convert to model objects if requested
        if convert_to_models:
            return self._convert_tweets_with_authors(tweets)

        return tweets

    #
    # Webhook Methods
    #

    def get_webhook_rules(self, convert_to_models: bool = True) -> Union[List[Dict[str, Any]], List[WebhookRule]]:
        """
        Get all webhook/websocket tweet filter rules.

        Args:
            convert_to_models: Whether to convert results to WebhookRule objects

        Returns:
            List of webhook rules (as dictionaries or WebhookRule objects)

        Raises:
            TwitterAPIError: If there's an error with the API
        """
        # Make request
        response = self.base.make_request("GET", "oapi/tweet_filter/get_rules")

        # Extract rules
        rules = response.get("rules", [])

        # Convert to model objects if requested
        if convert_to_models:
            return [WebhookRule.from_dict(rule_data) for rule_data in rules]

        return rules

    def add_webhook_rule(
        self,
        tag: str,
        value: str,
        interval_seconds: int,
        convert_to_model: bool = True,
    ) -> Union[Dict[str, Any], WebhookRule]:
        """
        Add a new webhook/websocket tweet filter rule.

        Args:
            tag: Custom tag to identify the rule
            value: Rule to filter tweets (e.g., "from:username", "keyword", etc.)
            interval_seconds: Interval to check tweets (in seconds, min 100, max 86400)
            convert_to_model: Whether to convert result to WebhookRule object

        Returns:
            Added webhook rule (as dictionary or WebhookRule object)

        Raises:
            TwitterAPIError: If there's an error with the API
            TwitterAPIValidationError: If parameters are invalid
        """
        # Validate parameters
        validate_string_param(tag, "tag", max_length=255)
        validate_string_param(value, "value", max_length=255)
        interval_seconds = validate_numeric_param(interval_seconds, "interval_seconds", min_value=100, max_value=86400)

        # Prepare request data
        data = {
            "tag": tag,
            "value": value,
            "interval_seconds": interval_seconds,
        }

        # Make request
        response = self.base.make_request("POST", "oapi/tweet_filter/add_rule", data=data)

        # Extract rule ID and create WebhookRule object
        rule_id = response.get("rule_id")

        if not rule_id:
            raise TwitterAPIError("Failed to get rule_id from response")

        # Combine response with request data for complete rule object
        rule_data = {
            "rule_id": rule_id,
            **data,
            "is_effect": 0,  # New rules are inactive by default
        }

        # Convert to model object if requested
        if convert_to_model:
            return WebhookRule.from_dict(rule_data)

        return rule_data

    def update_webhook_rule(
        self,
        rule_id: str,
        tag: str,
        value: str,
        interval_seconds: int,
        is_active: bool = False,
    ) -> bool:
        """
        Update an existing webhook/websocket tweet filter rule.

        Args:
            rule_id: ID of the rule to update
            tag: Custom tag to identify the rule
            value: Rule to filter tweets (e.g., "from:username", "keyword", etc.)
            interval_seconds: Interval to check tweets (in seconds, min 100, max 86400)
            is_active: Whether the rule is active (will trigger notifications)

        Returns:
            True if the update was successful

        Raises:
            TwitterAPIError: If there's an error with the API
            TwitterAPIValidationError: If parameters are invalid
        """
        # Validate parameters
        validate_string_param(rule_id, "rule_id")
        validate_string_param(tag, "tag", max_length=255)
        validate_string_param(value, "value", max_length=255)
        interval_seconds = validate_numeric_param(interval_seconds, "interval_seconds", min_value=100, max_value=86400)

        # Prepare request data
        data = {
            "rule_id": rule_id,
            "tag": tag,
            "value": value,
            "interval_seconds": interval_seconds,
            "is_effect": 1 if is_active else 0,
        }

        # Make request
        response = self.base.make_request("POST", "oapi/tweet_filter/update_rule", data=data)

        # Check if update was successful
        return response.get("status") == "success"

    def delete_webhook_rule(self, rule_id: str) -> bool:
        """
        Delete a webhook/websocket tweet filter rule.

        Args:
            rule_id: ID of the rule to delete

        Returns:
            True if the deletion was successful

        Raises:
            TwitterAPIError: If there's an error with the API
            TwitterAPIValidationError: If parameters are invalid
        """
        # Validate parameters
        validate_string_param(rule_id, "rule_id")

        # Prepare request data
        data = {"rule_id": rule_id}

        # Make request
        response = self.base.make_request("DELETE", "oapi/tweet_filter/delete_rule", data=data)

        # Check if deletion was successful
        return response.get("status") == "success"

    #
    # Helper Methods
    #

    def _convert_tweets_with_authors(self, tweets_data: List[Dict[str, Any]]) -> List[Tweet]:
        """
        Convert tweet dictionaries to Tweet objects with authors.

        Args:
            tweets_data: List of tweet dictionaries from TwitterAPI.io

        Returns:
            List of Tweet objects with authors
        """
        return [self._convert_tweet_with_author(tweet_data) for tweet_data in tweets_data]

    def _convert_tweet_with_author(self, tweet_data: Dict[str, Any]) -> Tweet:
        """
        Convert a tweet dictionary to a Tweet object with author.

        Args:
            tweet_data: Tweet dictionary from TwitterAPI.io

        Returns:
            Tweet object with author
        """
        tweet = Tweet.from_dict(tweet_data)

        # Set author if present in tweet data
        if "author" in tweet_data and tweet_data["author"]:
            tweet.author = User.from_dict(tweet_data["author"])

        return tweet