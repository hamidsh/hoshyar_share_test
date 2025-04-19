"""
Tweet models for TwitterAPI.io client.

مدل‌های توییت برای کلاینت TwitterAPI.io
"""

import dataclasses
import datetime
from typing import Any, Dict, List, Optional, Union

from lib.twitter_api.utils.date_utils import parse_twitter_date


@dataclasses.dataclass
class Entity:
    """Base class for Twitter entities."""
    indices: List[int]


@dataclasses.dataclass
class HashtagEntity(Entity):
    """Model for hashtag entity in tweets."""
    text: str


@dataclasses.dataclass
class UrlEntity(Entity):
    """Model for URL entity in tweets."""
    url: str
    display_url: str
    expanded_url: str


@dataclasses.dataclass
class UserMentionEntity(Entity):
    """Model for user mention entity in tweets."""
    id_str: str
    name: str
    screen_name: str


@dataclasses.dataclass
class Tweet:
    """
    Model for Twitter tweet data.

    نکته: این کلاس با ساختار واقعی پاسخ‌های TwitterAPI.io ساخته شده است
    و با آنچه در مستندات API آمده کمی متفاوت است
    """
    # Basic tweet information
    id: str
    text: str
    created_at: datetime.datetime

    # Tweet stats
    retweet_count: int
    reply_count: int
    like_count: int
    quote_count: int
    view_count: Optional[int] = None
    bookmark_count: Optional[int] = None

    # API type field (must be after non-default arguments)
    type: str = "tweet"  # مقدار ثابت طبق مستندات API

    # Tweet metadata
    url: Optional[str] = None
    twitter_url: Optional[str] = None  # Actual API uses twitterUrl
    source: Optional[str] = None
    lang: Optional[str] = None
    is_reply: bool = False
    in_reply_to_id: Optional[str] = None
    conversation_id: Optional[str] = None
    in_reply_to_user_id: Optional[str] = None
    in_reply_to_username: Optional[str] = None

    # Relationships
    author: Optional[Any] = None  # User object - using Any to avoid circular imports
    quoted_tweet: Optional['Tweet'] = None
    retweeted_tweet: Optional['Tweet'] = None

    # Entities
    hashtags: List[HashtagEntity] = dataclasses.field(default_factory=list)
    urls: List[UrlEntity] = dataclasses.field(default_factory=list)
    user_mentions: List[UserMentionEntity] = dataclasses.field(default_factory=list)

    # Additional fields found in real API
    extended_entities: Optional[Dict[str, Any]] = None
    card: Optional[Dict[str, Any]] = None
    place: Optional[Dict[str, Any]] = None

    # Raw data
    raw_data: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Tweet':
        """
        Create Tweet object from dictionary.

        This method handles the discrepancies between the actual API response
        and what's documented in the API documentation.

        Args:
            data: Dictionary containing tweet data from TwitterAPI.io

        Returns:
            Tweet object
        """
        # Handle different tweet types/fields
        tweet_id = data.get("id")
        text = data.get("text", "")

        # Parse created_at
        created_at_str = data.get("createdAt")
        if created_at_str:
            try:
                created_at = parse_twitter_date(created_at_str)
            except (ValueError, TypeError):
                created_at = datetime.datetime.now(tz=datetime.timezone.utc)
        else:
            created_at = datetime.datetime.now(tz=datetime.timezone.utc)

        # Parse stats (with fallbacks to 0)
        retweet_count = int(data.get("retweetCount", 0))
        reply_count = int(data.get("replyCount", 0))
        like_count = int(data.get("likeCount", 0))
        quote_count = int(data.get("quoteCount", 0))

        # Optional stats
        view_count = None
        if "viewCount" in data:
            view_count = int(data.get("viewCount", 0))

        bookmark_count = None
        if "bookmarkCount" in data:
            bookmark_count = int(data.get("bookmarkCount", 0))

        # Parse flags and relationships
        is_reply = data.get("isReply", False)
        in_reply_to_id = data.get("inReplyToId")
        conversation_id = data.get("conversationId")
        in_reply_to_user_id = data.get("inReplyToUserId")
        in_reply_to_username = data.get("inReplyToUsername")

        # URLs - API has both url and twitterUrl fields
        url = data.get("url")
        twitter_url = data.get("twitterUrl")

        # Additional fields found in real API
        extended_entities = data.get("extendedEntities")
        card = data.get("card")
        place = data.get("place")

        # Prepare entities
        hashtags = []
        urls = []
        user_mentions = []

        entities = data.get("entities", {})

        # Parse hashtags
        for hashtag_data in entities.get("hashtags", []):
            hashtags.append(HashtagEntity(
                indices=hashtag_data.get("indices", [0, 0]),
                text=hashtag_data.get("text", "")
            ))

        # Parse URLs
        for url_data in entities.get("urls", []):
            urls.append(UrlEntity(
                indices=url_data.get("indices", [0, 0]),
                url=url_data.get("url", ""),
                display_url=url_data.get("display_url", ""),
                expanded_url=url_data.get("expanded_url", "")
            ))

        # Parse user mentions
        for mention_data in entities.get("user_mentions", []):
            user_mentions.append(UserMentionEntity(
                indices=mention_data.get("indices", [0, 0]),
                id_str=mention_data.get("id_str", ""),
                name=mention_data.get("name", ""),
                screen_name=mention_data.get("screen_name", "")
            ))

        # Parse nested tweets
        quoted_tweet = None
        if "quoted_tweet" in data and data["quoted_tweet"]:
            quoted_tweet = cls.from_dict(data["quoted_tweet"])

        retweeted_tweet = None
        if "retweeted_tweet" in data and data["retweeted_tweet"]:
            retweeted_tweet = cls.from_dict(data["retweeted_tweet"])

        # Create Tweet object
        return cls(
            id=tweet_id,
            text=text,
            created_at=created_at,
            retweet_count=retweet_count,
            reply_count=reply_count,
            like_count=like_count,
            quote_count=quote_count,
            view_count=view_count,
            bookmark_count=bookmark_count,
            url=url,
            twitter_url=twitter_url,
            source=data.get("source"),
            lang=data.get("lang"),
            is_reply=is_reply,
            in_reply_to_id=in_reply_to_id,
            conversation_id=conversation_id,
            in_reply_to_user_id=in_reply_to_user_id,
            in_reply_to_username=in_reply_to_username,
            author=None,  # Will be set separately
            quoted_tweet=quoted_tweet,
            retweeted_tweet=retweeted_tweet,
            hashtags=hashtags,
            urls=urls,
            user_mentions=user_mentions,
            extended_entities=extended_entities,
            card=card,
            place=place,
            raw_data=data
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Tweet object to dictionary.

        Returns:
            Dictionary representation of the tweet
        """
        result = {
            "type": self.type,
            "id": self.id,
            "text": self.text,
            "created_at": self.created_at.isoformat(),
            "retweet_count": self.retweet_count,
            "reply_count": self.reply_count,
            "like_count": self.like_count,
            "quote_count": self.quote_count,
        }

        if self.view_count is not None:
            result["view_count"] = self.view_count

        if self.bookmark_count is not None:
            result["bookmark_count"] = self.bookmark_count

        if self.url:
            result["url"] = self.url

        if self.twitter_url:
            result["twitter_url"] = self.twitter_url

        if self.source:
            result["source"] = self.source

        if self.lang:
            result["lang"] = self.lang

        result["is_reply"] = self.is_reply

        if self.in_reply_to_id:
            result["in_reply_to_id"] = self.in_reply_to_id

        if self.conversation_id:
            result["conversation_id"] = self.conversation_id

        if self.in_reply_to_user_id:
            result["in_reply_to_user_id"] = self.in_reply_to_user_id

        if self.in_reply_to_username:
            result["in_reply_to_username"] = self.in_reply_to_username

        if self.author:
            result["author"] = self.author.to_dict()

        if self.quoted_tweet:
            result["quoted_tweet"] = self.quoted_tweet.to_dict()

        if self.retweeted_tweet:
            result["retweeted_tweet"] = self.retweeted_tweet.to_dict()

        result["entities"] = {
            "hashtags": [{"indices": h.indices, "text": h.text} for h in self.hashtags],
            "urls": [{"indices": u.indices, "url": u.url, "display_url": u.display_url, "expanded_url": u.expanded_url} for u in self.urls],
            "user_mentions": [{"indices": m.indices, "id_str": m.id_str, "name": m.name, "screen_name": m.screen_name} for m in self.user_mentions],
        }

        if self.extended_entities:
            result["extended_entities"] = self.extended_entities

        if self.card:
            result["card"] = self.card

        if self.place:
            result["place"] = self.place

        return result