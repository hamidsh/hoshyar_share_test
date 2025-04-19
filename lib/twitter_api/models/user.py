"""
User models for TwitterAPI.io client.

مدل‌های کاربر برای کلاینت TwitterAPI.io
"""

import dataclasses
import datetime
from typing import Any, Dict, List, Optional, Union

from lib.twitter_api.utils.date_utils import parse_twitter_date


@dataclasses.dataclass
class User:
    """
    Model for Twitter user data.

    نکته: این کلاس بر اساس ساختار واقعی داده‌های TwitterAPI.io ساخته شده
    و با داده‌هایی که در مستندات API آمده متفاوت است.
    """
    # Basic user information
    id: str
    username: str  # screen_name in API response
    name: str

    # API type field (must be after non-default arguments)
    type: str = "user"  # مقدار ثابت طبق مستندات API

    # Profile details
    profile_picture: Optional[str] = None
    cover_picture: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    url: Optional[str] = None

    # Account stats
    followers_count: int = 0
    following_count: int = 0
    tweet_count: int = 0  # statusesCount in API response
    media_count: Optional[int] = None
    favourites_count: Optional[int] = None

    # Account metadata
    created_at: Optional[datetime.datetime] = None
    is_blue_verified: bool = False
    is_automated: bool = False
    automated_by: Optional[str] = None
    can_dm: Optional[bool] = None
    is_translator: Optional[bool] = None
    has_custom_timelines: Optional[bool] = None
    possibly_sensitive: Optional[bool] = None

    # Account status
    unavailable: bool = False
    unavailable_message: Optional[str] = None
    unavailable_reason: Optional[str] = None

    # Other fields
    withheld_in_countries: List[str] = dataclasses.field(default_factory=list)
    pinned_tweet_ids: List[str] = dataclasses.field(default_factory=list)

    # Raw data
    raw_data: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """
        Create User object from dictionary.

        This method handles the discrepancies between user info formats
        from different endpoints (screen_name vs userName, etc.)
        """
        # Handle different field names and nested structures
        user_id = data.get("id")

        # Username: handle both screen_name and userName
        username = data.get("screen_name") or data.get("userName") or ""

        # Name
        name = data.get("name", "")

        # Parse created_at - handle both formats
        created_at_str = data.get("created_at") or data.get("createdAt")
        created_at = None
        if created_at_str:
            try:
                created_at = parse_twitter_date(created_at_str)
            except (ValueError, TypeError):
                pass

        # Parse followers/following - handle different field names
        followers_count = 0
        for field in ["followers_count", "followers"]:
            if field in data and data[field] is not None:
                try:
                    followers_count = int(data[field])
                    break
                except (ValueError, TypeError):
                    pass

        # Handle different field names for following
        following_count = 0
        for field in ["following_count", "following", "friends_count"]:
            if field in data and data[field] is not None:
                try:
                    following_count = int(data[field])
                    break
                except (ValueError, TypeError):
                    pass

        # Handle different field names for tweets count
        tweet_count = 0
        for field in ["statuses_count", "statusesCount"]:
            if field in data and data[field] is not None:
                try:
                    tweet_count = int(data[field])
                    break
                except (ValueError, TypeError):
                    pass

        # Parse optional counts
        media_count = None
        if "media_count" in data:
            try:
                media_count = int(data["media_count"])
            except (ValueError, TypeError):
                pass
        elif "mediaCount" in data:
            try:
                media_count = int(data["mediaCount"])
            except (ValueError, TypeError):
                pass

        favourites_count = None
        for field in ["favourites_count", "favouritesCount"]:
            if field in data and data[field] is not None:
                try:
                    favourites_count = int(data[field])
                    break
                except (ValueError, TypeError):
                    pass

        # Parse verification status - handle different field names
        is_blue_verified = False
        for field in ["isBlueVerified", "verified", "isVerified"]:
            if field in data:
                is_blue_verified = bool(data[field])
                if is_blue_verified:
                    break

        # Parse profile details - handle different field names
        profile_picture = data.get("profile_image_url_https") or data.get("profilePicture")
        cover_picture = data.get("profile_banner_url") or data.get("coverPicture")
        description = data.get("description")
        location = data.get("location")
        url = data.get("url")

        # Parse boolean flags - handle both formats
        is_automated = data.get("isAutomated", False) or data.get("automated", False)
        can_dm = data.get("can_dm") if "can_dm" in data else data.get("canDm")
        is_translator = data.get("is_translator") if "is_translator" in data else data.get("isTranslator")
        has_custom_timelines = data.get("has_custom_timelines") if "has_custom_timelines" in data else data.get(
            "hasCustomTimelines")
        possibly_sensitive = data.get("possibly_sensitive") if "possibly_sensitive" in data else data.get(
            "possiblySensitive")

        # Parse unavailable status
        unavailable = data.get("unavailable", False)
        unavailable_message = data.get("message") if unavailable else None
        unavailable_reason = data.get("unavailableReason") if unavailable else None

        # Parse lists
        withheld_in_countries = data.get("withheldInCountries", []) or data.get("withheld_in_countries", [])
        if withheld_in_countries is None:
            withheld_in_countries = []

        pinned_tweet_ids = data.get("pinnedTweetIds", []) or data.get("pinned_tweet_ids", [])
        if pinned_tweet_ids is None:
            pinned_tweet_ids = []

        # Create User object
        return cls(
            id=user_id,
            username=username,
            name=name,
            profile_picture=profile_picture,
            cover_picture=cover_picture,
            description=description,
            location=location,
            url=url,
            followers_count=followers_count,
            following_count=following_count,
            tweet_count=tweet_count,
            media_count=media_count,
            favourites_count=favourites_count,
            created_at=created_at,
            is_blue_verified=is_blue_verified,
            is_automated=is_automated,
            automated_by=data.get("automatedBy"),
            can_dm=can_dm,
            is_translator=is_translator,
            has_custom_timelines=has_custom_timelines,
            possibly_sensitive=possibly_sensitive,
            unavailable=unavailable,
            unavailable_message=unavailable_message,
            unavailable_reason=unavailable_reason,
            withheld_in_countries=withheld_in_countries,
            pinned_tweet_ids=pinned_tweet_ids,
            raw_data=data
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert User object to dictionary.

        Returns:
            Dictionary representation of the user
        """
        result = {
            "type": self.type,
            "id": self.id,
            "username": self.username,
            "name": self.name,
            "followers_count": self.followers_count,
            "following_count": self.following_count,
            "tweet_count": self.tweet_count,
            "is_blue_verified": self.is_blue_verified,
            "unavailable": self.unavailable,
        }

        # Add optional fields if present
        if self.profile_picture:
            result["profile_picture"] = self.profile_picture

        if self.cover_picture:
            result["cover_picture"] = self.cover_picture

        if self.description:
            result["description"] = self.description

        if self.location:
            result["location"] = self.location

        if self.url:
            result["url"] = self.url

        if self.created_at:
            result["created_at"] = self.created_at.isoformat()

        if self.media_count is not None:
            result["media_count"] = self.media_count

        if self.favourites_count is not None:
            result["favourites_count"] = self.favourites_count

        if self.is_automated:
            result["is_automated"] = self.is_automated

        if self.automated_by:
            result["automated_by"] = self.automated_by

        if self.can_dm is not None:
            result["can_dm"] = self.can_dm

        if self.is_translator is not None:
            result["is_translator"] = self.is_translator

        if self.has_custom_timelines is not None:
            result["has_custom_timelines"] = self.has_custom_timelines

        if self.possibly_sensitive is not None:
            result["possibly_sensitive"] = self.possibly_sensitive

        if self.unavailable_message:
            result["unavailable_message"] = self.unavailable_message

        if self.unavailable_reason:
            result["unavailable_reason"] = self.unavailable_reason

        if self.withheld_in_countries:
            result["withheld_in_countries"] = self.withheld_in_countries

        if self.pinned_tweet_ids:
            result["pinned_tweet_ids"] = self.pinned_tweet_ids

        return result