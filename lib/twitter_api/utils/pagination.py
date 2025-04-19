"""
Pagination utilities for TwitterAPI.io client.

ابزارهای صفحه‌بندی برای کلاینت TwitterAPI.io که مشکلات خاص این API را مدیریت می‌کند
"""
import logging
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, TypeVar, Union, Tuple

from lib.twitter_api.exceptions import TwitterAPIPaginationError

logger = logging.getLogger(__name__)

T = TypeVar('T')


def extract_pagination_info(response_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Extract pagination information from response data.

    Handles different pagination formats and API inconsistencies.
    """
    if "has_next_page" in response_data and "next_cursor" in response_data:
        has_next_page = response_data.get("has_next_page", False)
        next_cursor = response_data.get("next_cursor", "")
        if has_next_page and not next_cursor:
            logger.debug("API inconsistency: has_next_page=True but next_cursor empty")
            return False, ""
        return has_next_page, next_cursor
    for cursor_key in ["next_cursor", "next_token", "next_page"]:
        if cursor_key in response_data:
            cursor_value = response_data.get(cursor_key, "")
            if cursor_value:
                return True, cursor_value
    return False, ""

def paginate_resource(
    request_func: Callable[[str], Dict[str, Any]],
    resource_key: str,
    max_pages: Optional[int] = None,
    max_items: Optional[int] = None,
    stop_on_empty: bool = False,  # تغییر به False برای جلوگیری از توقف زودهنگام
    initial_cursor: str = "",
    max_empty_pages: int = 3,  # افزایش به 3 برای تحمل بیشتر
    expected_items_per_page: int = 20,  # برای هشدار صفحات ناقص
) -> List[Dict[str, Any]]:
    """
    Paginate through a resource in TwitterAPI.io.

    Args:
        request_func: Function that makes the request
        resource_key: Key containing the items
        max_pages: Maximum number of pages
        max_items: Maximum number of items
        stop_on_empty: Stop on empty pages
        initial_cursor: Initial cursor
        max_empty_pages: Max consecutive empty pages
        expected_items_per_page: Expected items per page

    Returns:
        List of items

    Raises:
        TwitterAPIPaginationError: If pagination fails
    """
    all_items = []
    cursor = initial_cursor
    page_count = 0
    empty_page_count = 0
    items_needed = max_items if max_items is not None else float('inf')

    while True:
        # بررسی محدودیت‌های کلی
        if max_pages is not None and page_count >= max_pages:
            logger.info(f"Stopping: Reached max pages ({max_pages})")
            break
        if len(all_items) >= items_needed:
            logger.info(f"Stopping: Reached max items ({len(all_items)})")
            break

        # درخواست صفحه
        try:
            response_data = request_func(cursor)
        except Exception as e:
            logger.error(f"Error fetching page {page_count + 1}: {str(e)}")
            raise
        page_count += 1

        # استخراج آیتم‌ها
        items = response_data.get(resource_key, [])
        if items is None:
            items = []
        if not isinstance(items, list):
            raise TwitterAPIPaginationError(
                f"Expected a list for '{resource_key}', got {type(items).__name__}"
            )

        # بررسی تعداد آیتم‌ها
        if len(items) < expected_items_per_page and items:
            logger.warning(
                f"Page {page_count}: Only {len(items)} items received, expected {expected_items_per_page}"
            )
        if not items:
            empty_page_count += 1
            logger.debug(f"Page {page_count}: Empty")
        else:
            empty_page_count = 0
            all_items.extend(items)
            logger.debug(f"Page {page_count}: Added {len(items)} items, total: {len(all_items)}")

        # بررسی محدودیت آیتم‌ها
        if max_items is not None and len(all_items) >= max_items:
            all_items = all_items[:max_items]
            logger.info(f"Stopping: Reached max items ({max_items})")
            break

        # بررسی صفحه بعدی
        has_next_page, next_cursor = extract_pagination_info(response_data)
        logger.debug(f"Page {page_count}: has_next_page={has_next_page}, next_cursor={next_cursor}")
        if not has_next_page or not next_cursor:
            logger.info("Stopping: No next page available")
            break

        # بررسی صفحات خالی
        if stop_on_empty and empty_page_count >= max_empty_pages:
            logger.warning(f"Stopping: {empty_page_count} consecutive empty pages")
            break

        cursor = next_cursor

    return all_items

class PaginatedIterator(Iterable[T]):
    """
    Iterator for paginated resources that fetches pages as needed.

    این کلاس یک iterator قابل استفاده در حلقه‌های for ایجاد می‌کند که صفحات را به صورت خودکار
    دریافت می‌کند و امکان پیمایش تمام نتایج را فراهم می‌سازد.
    """

    def __init__(
        self,
        request_func: Callable[[str], Dict[str, Any]],
        resource_key: str,
        transform_func: Optional[Callable[[Dict[str, Any]], T]] = None,
        max_pages: Optional[int] = None,
        max_items: Optional[int] = None,
        initial_cursor: str = "",
        max_empty_pages: int = 1,
    ):
        """
        Initialize paginated iterator.

        Args:
            request_func: Function that makes the request and takes a cursor parameter
            resource_key: Key in the response data that contains the items
            transform_func: Function to transform each item (optional)
            max_pages: Maximum number of pages to retrieve (None for unlimited)
            max_items: Maximum number of items to retrieve (None for unlimited)
            initial_cursor: Initial cursor value
            max_empty_pages: Maximum number of consecutive empty pages before stopping
        """
        self.request_func = request_func
        self.resource_key = resource_key
        self.transform_func = transform_func
        self.max_pages = max_pages
        self.max_items = max_items
        self.initial_cursor = initial_cursor
        self.max_empty_pages = max_empty_pages

        # Initialize state
        self.cursor = initial_cursor
        self.current_page = []
        self.current_index = 0
        self.page_count = 0
        self.item_count = 0
        self.has_next_page = True
        self.empty_page_count = 0

    def __iter__(self):
        return self

    def __next__(self) -> T:
        """Get the next item from the iterator."""
        # Check if we've reached the maximum number of items
        if self.max_items is not None and self.item_count >= self.max_items:
            raise StopIteration

        # If we've exhausted the current page, fetch the next page
        if self.current_index >= len(self.current_page):
            # Check if we've reached the maximum number of pages
            if self.max_pages is not None and self.page_count >= self.max_pages:
                raise StopIteration

            # Check if we've seen too many consecutive empty pages
            if self.empty_page_count >= self.max_empty_pages:
                raise StopIteration

            # Check if there's a next page
            if not self.has_next_page:
                raise StopIteration

            # Fetch the next page
            self._fetch_next_page()

            # If the page is empty, recursively try again or stop
            if not self.current_page:
                self.empty_page_count += 1
                if self.empty_page_count >= self.max_empty_pages:
                    raise StopIteration
                if self.has_next_page:
                    return self.__next__()
                else:
                    raise StopIteration

        # Get the next item
        item = self.current_page[self.current_index]
        self.current_index += 1
        self.item_count += 1

        # Transform the item if a transform function is provided
        if self.transform_func is not None:
            return self.transform_func(item)

        return item

    def _fetch_next_page(self) -> None:
        """Fetch the next page of results."""
        # Make the request
        response_data = self.request_func(self.cursor)
        self.page_count += 1

        # Extract items from the response
        items = response_data.get(self.resource_key, [])

        # Handle the case where the resource key exists but is None
        if items is None:
            items = []

        # Handle inconsistent empty array response format
        if not isinstance(items, list):
            raise TwitterAPIPaginationError(
                f"Expected a list for resource key '{self.resource_key}', got {type(items).__name__}"
            )

        # Update current page and reset index
        self.current_page = items
        self.current_index = 0

        # Update empty page counter
        if not items:
            self.empty_page_count += 1
        else:
            self.empty_page_count = 0

        # Extract pagination information
        has_next_page, next_cursor = extract_pagination_info(response_data)
        self.has_next_page = has_next_page and bool(next_cursor)
        self.cursor = next_cursor