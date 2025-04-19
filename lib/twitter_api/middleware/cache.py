"""
Cache system for TwitterAPI.io.
"""
import hashlib
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

logger = logging.getLogger(__name__)

class TwitterAPICache:
    DEFAULT_TTL_MAPPING = {
        'twitter/user/info': 3600,
        'twitter/user/batch_info_by_ids': 3600,
        'twitter/user/last_tweets': 600,
        'twitter/tweet/advanced_search': 300,
        'twitter/user/followers': 7200,
        'twitter/user/followings': 7200,
        'twitter/tweet/replies': 900,
        'twitter/tweet/quotes': 900,
        'twitter/list/tweets': 1800,
    }

    def __init__(self, cache_dir: str = '.twitter_cache', ttl_mapping: Optional[Dict[str, int]] = None, max_cache_size_mb: int = 100):
        self.cache_dir = cache_dir
        self.ttl_mapping = self.DEFAULT_TTL_MAPPING.copy()
        if ttl_mapping:
            self.ttl_mapping.update(ttl_mapping)
        self.max_cache_size = max_cache_size_mb * 1024 * 1024
        self.stats = {'hits': 0, 'misses': 0, 'size': 0}
        os.makedirs(cache_dir, exist_ok=True)
        self._calculate_cache_stats()
        logger.info(f"Cache initialized. Path: {cache_dir}, files: {self.stats.get('files', 0)}, size: {self.stats.get('size_mb', 0):.2f} MB")

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, max_results: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieve data from cache if available and valid.

        Args:
            endpoint: API endpoint
            params: Request parameters
            max_results: Requested number of results (to ensure cache compatibility)

        Returns:
            Cached data or None if cache is invalid or insufficient
        """
        key = self._get_cache_key(endpoint, params, max_results)
        cache_path = os.path.join(self.cache_dir, f"{key}.json")

        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                cache_time = datetime.fromisoformat(cache_data['timestamp'])
                ttl = self._get_ttl_for_endpoint(endpoint)
                if datetime.now() - cache_time < timedelta(seconds=ttl):
                    # بررسی تعداد آیتم‌ها در کش
                    if max_results is not None and endpoint.endswith("tweet/advanced_search"):
                        tweets = cache_data['data'].get('tweets', [])
                        if len(tweets) < max_results:
                            logger.debug(f"Cache ignored for {endpoint}: {len(tweets)} items, needed {max_results}")
                            self.stats['misses'] += 1
                            return None
                    self.stats['hits'] += 1
                    logger.debug(f"Cache hit for {endpoint}")
                    return cache_data['data']
                else:
                    logger.debug(f"Cache expired for {endpoint}")
            except Exception as e:
                logger.warning(f"Error reading cache for {endpoint}: {str(e)}")
        self.stats['misses'] += 1
        return None

    def set(self, endpoint: str, params: Optional[Dict[str, Any]], data: Dict[str, Any], max_results: Optional[int] = None) -> bool:
        """
        Store data in cache.

        Args:
            endpoint: API endpoint
            params: Request parameters
            data: Data to store
            max_results: Requested number of results (for cache key)

        Returns:
            True if stored successfully, False otherwise
        """
        if self.stats['size'] > self.max_cache_size:
            self._cleanup_old_cache()
        key = self._get_cache_key(endpoint, params, max_results)
        cache_path = os.path.join(self.cache_dir, f"{key}.json")
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                cache_data = {
                    'timestamp': datetime.now().isoformat(),
                    'endpoint': endpoint,
                    'data': data
                }
                json.dump(cache_data, f, ensure_ascii=False)
            file_size = os.path.getsize(cache_path)
            self.stats['size'] += file_size
            if 'files' in self.stats:
                self.stats['files'] += 1
            self.stats['size_mb'] = self.stats['size'] / (1024 * 1024)
            logger.debug(f"Stored cache for {endpoint} (size: {file_size / 1024:.1f} KB)")
            return True
        except Exception as e:
            logger.warning(f"Error storing cache for {endpoint}: {str(e)}")
            return False

    def _get_cache_key(self, endpoint: str, params: Optional[Dict[str, Any]], max_results: Optional[int] = None) -> str:
        """
        Create a unique cache key.

        Args:
            endpoint: API endpoint
            params: Request parameters
            max_results: Requested number of results

        Returns:
            Unique cache key
        """
        params_str = json.dumps(params, sort_keys=True) if params else ""
        key_parts = [endpoint, params_str]
        if max_results is not None:
            key_parts.append(str(max_results))
        key_str = "_".join(key_parts)
        return hashlib.md5(key_str.encode()).hexdigest()

    def _get_ttl_for_endpoint(self, endpoint: str) -> int:
        for key, ttl in self.ttl_mapping.items():
            if key in endpoint:
                return ttl
        return 600

    def _calculate_cache_stats(self):
        total_size = 0
        file_count = 0
        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(self.cache_dir, filename)
                try:
                    file_size = os.path.getsize(file_path)
                    total_size += file_size
                    file_count += 1
                except:
                    pass
        self.stats['size'] = total_size
        self.stats['size_mb'] = total_size / (1024 * 1024)
        self.stats['files'] = file_count

    def _cleanup_old_cache(self):
        files_info = []
        for filename in os.listdir(self.cache_dir):
            if not filename.endswith('.json'):
                continue
            file_path = os.path.join(self.cache_dir, filename)
            try:
                mtime = os.path.getmtime(file_path)
                size = os.path.getsize(file_path)
                files_info.append((file_path, mtime, size))
            except:
                continue
        files_info.sort(key=lambda x: x[1])
        target_size = self.max_cache_size * 0.8
        current_size = self.stats['size']
        deleted_count = 0
        for file_path, _, size in files_info:
            if current_size <= target_size:
                break
            try:
                os.remove(file_path)
                current_size -= size
                deleted_count += 1
            except:
                continue
        if deleted_count > 0:
            logger.info(f"Cleaned {deleted_count} old cache files")
            self._calculate_cache_stats()
        return deleted_count

    def get_stats(self) -> Dict[str, Union[int, float]]:
        self._calculate_cache_stats()
        hit_rate = 0
        total_requests = self.stats['hits'] + self.stats['misses']
        if total_requests > 0:
            hit_rate = (self.stats['hits'] / total_requests) * 100
        return {
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'hit_rate_percent': hit_rate,
            'size_bytes': self.stats['size'],
            'size_mb': self.stats['size_mb'],
            'files': self.stats.get('files', 0),
            'max_size_mb': self.max_cache_size / (1024 * 1024)
        }

    @staticmethod
    def _format_age(td: timedelta) -> str:
        total_seconds = int(td.total_seconds())
        days, remainder = divmod(total_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        parts = []
        if days > 0:
            parts.append(f"{days} days")
        if hours > 0:
            parts.append(f"{hours} hours")
        if minutes > 0:
            parts.append(f"{minutes} minutes")
        if seconds > 0 or not parts:
            parts.append(f"{seconds} seconds")
        return " and ".join(parts)