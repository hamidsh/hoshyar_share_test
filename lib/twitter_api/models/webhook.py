"""
Webhook models for TwitterAPI.io client.

مدل‌های وبهوک برای کلاینت TwitterAPI.io
"""

import dataclasses
from typing import Any, Dict, Optional

from lib.twitter_api.exceptions import TwitterAPIValidationError

@dataclasses.dataclass
class WebhookRule:
    """
    Model for TwitterAPI.io webhook/websocket tweet filter rule.

    TwitterAPI.io امکان ایجاد قوانین فیلتر توییت برای وبهوک/وبسوکت را فراهم می‌کند
    که می‌توان با آن توییت‌های موردنظر را به صورت خودکار دریافت کرد.
    """
    # Rule properties
    tag: str
    value: str
    interval_seconds: int

    # Rule status
    rule_id: Optional[str] = None
    is_active: bool = False

    # Raw data
    raw_data: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WebhookRule':
        """
        Create WebhookRule object from dictionary.

        Args:
            data: Dictionary containing webhook rule data from TwitterAPI.io

        Returns:
            WebhookRule object
        """
        # Parse rule data
        rule_id = data.get("rule_id")
        tag = data.get("tag", "")
        value = data.get("value", "")
        interval_seconds = int(data.get("interval_seconds", 0))

        # Check if rule is active (from is_effect if available)
        is_active = bool(data.get("is_effect", 0)) if "is_effect" in data else False

        # Create WebhookRule object
        return cls(
            rule_id=rule_id,
            tag=tag,
            value=value,
            interval_seconds=interval_seconds,
            is_active=is_active,
            raw_data=data
        )

    def to_dict(self, include_rule_id: bool = True) -> Dict[str, Any]:
        """
        Convert WebhookRule object to dictionary.

        Args:
            include_rule_id: Whether to include rule_id in the result

        Returns:
            Dictionary representation of the webhook rule
        """
        result = {
            "tag": self.tag,
            "value": self.value,
            "interval_seconds": self.interval_seconds,
        }

        # Include rule_id if requested and available
        if include_rule_id and self.rule_id:
            result["rule_id"] = self.rule_id

        # Include is_effect for update operations
        if include_rule_id:  # Only include in operations that would use rule_id
            result["is_effect"] = 1 if self.is_active else 0

        return result