"""
Example usage of the TwitterAPI.io client for Hoshyar project.

مثال‌های استفاده از کلاینت TwitterAPI.io
"""

import logging
import os
from typing import List

from lib.twitter_api import TwitterAPIClient, Tweet, User, TwitterAPIError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

# Get API key from environment variable or set it here
API_KEY = "cf5800d7a52a4df89b5df7ffe1c7303d"


def print_tweet(tweet: Tweet, indent: str = '') -> None:
    """Print tweet information in a readable format."""
    print(f"{indent}Tweet ID: {tweet.id}")
    print(f"{indent}Author: @{tweet.author.username if tweet.author else 'Unknown'}")
    print(f"{indent}Text: {tweet.text}")
    print(f"{indent}Created at: {tweet.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{indent}Retweets: {tweet.retweet_count}, Likes: {tweet.like_count}, Replies: {tweet.reply_count}")

    if tweet.quoted_tweet:
        print(f"{indent}Quoted Tweet:")
        print_tweet(tweet.quoted_tweet, indent + '  ')

    if tweet.retweeted_tweet:
        print(f"{indent}Retweeted Tweet:")
        print_tweet(tweet.retweeted_tweet, indent + '  ')


def print_user(user: User) -> None:
    """Print user information in a readable format."""
    print(f"User ID: {user.id}")
    print(f"Username: @{user.username}")
    print(f"Name: {user.name}")
    print(f"Description: {user.description}")
    print(f"Location: {user.location}")
    print(f"Verified: {user.is_blue_verified}")
    print(f"Followers: {user.followers_count}, Following: {user.following_count}")
    print(f"Created at: {user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else 'Unknown'}")


def example_search_tweets() -> None:
    """Example of searching tweets."""
    print("\n=== Search Tweets Example ===\n")

    client = TwitterAPIClient(API_KEY)

    try:
        # Search for tweets in Farsi containing specific keywords
        tweets = client.search_tweets(
            query="برنامه‌نویسی OR هوش‌مصنوعی lang:fa",
            query_type="Latest",
            max_results=5,
        )

        print(f"Found {len(tweets)} tweets:")
        for i, tweet in enumerate(tweets, 1):
            print(f"\n--- Tweet {i} ---")
            print_tweet(tweet)

    except TwitterAPIError as e:
        print(f"Error: {e}")


def example_get_user_tweets() -> None:
    """Example of getting user tweets."""
    print("\n=== Get User Tweets Example ===\n")

    client = TwitterAPIClient(API_KEY)

    try:
        # Get tweets from a specific user
        tweets = client.get_user_tweets(
            username="hashemisattar",  # Replace with a real username
            max_results=3,
        )

        print(f"Found {len(tweets)} tweets from user:")
        for i, tweet in enumerate(tweets, 1):
            print(f"\n--- Tweet {i} ---")
            print_tweet(tweet)

    except TwitterAPIError as e:
        print(f"Error: {e}")


def example_get_user_followers() -> None:
    """Example of getting user followers."""
    print("\n=== Get User Followers Example ===\n")

    client = TwitterAPIClient(API_KEY)

    try:
        # Get followers of a specific user
        followers = client.get_user_followers(
            username="elonmusk",  # Replace with a real username
            max_results=3,
        )

        print(f"Found {len(followers)} followers:")
        for i, user in enumerate(followers, 1):
            print(f"\n--- Follower {i} ---")
            print_user(user)

    except TwitterAPIError as e:
        print(f"Error: {e}")


def example_get_tweet_replies() -> None:
    """مثالی از دریافت پاسخ‌ها به یک توییت."""
    print("\n=== Get Tweet Replies Example ===\n")

    client = TwitterAPIClient(API_KEY)

    try:
        # نکته: بر اساس مستندات، فقط توییت‌های اصلی پشتیبانی می‌شوند، نه پاسخ‌ها
        responses = client.get_tweet_replies(
            tweet_id="1234567890123456789",  # جایگزین با یک ID توییت اصلی معتبر
            max_results=3,
        )

        print(f"Found {len(responses)} replies:")
        for i, tweet in enumerate(responses, 1):
            if i <= 3:  # فقط 3 پاسخ اول را نمایش می‌دهیم
                print(f"\n--- Reply {i} ---")
                print_tweet(tweet)

    except TwitterAPIError as e:
        print(f"Error: {e}")
        # پیشنهاد: پاسخ خام را برای کمک به دیباگ نشان دهید
        if hasattr(e, 'response'):
            print(f"Response data: {e.response}")


def example_using_iterators() -> None:
    """Example of using iterators for efficient pagination."""
    print("\n=== Using Iterators Example ===\n")

    client = TwitterAPIClient(API_KEY)

    try:
        # Use iterator to efficiently retrieve tweets
        tweet_iterator = client.search_tweets_iter(
            query="اخبار lang:fa",
            query_type="Latest",
            max_results=10,
        )

        print("Iterating through tweets:")
        for i, tweet in enumerate(tweet_iterator, 1):
            print(f"\n--- Tweet {i} ---")
            print(f"ID: {tweet.id}")
            print(f"Author: @{tweet.author.username if tweet.author else 'Unknown'}")
            print(f"Text: {tweet.text[:100]}...")

            # Stop after 3 tweets for this example
            if i >= 3:
                break

    except TwitterAPIError as e:
        print(f"Error: {e}")


def main() -> None:
    """Run all examples."""
    try:
        example_search_tweets()
        example_get_user_tweets()
        example_get_user_followers()
        example_get_tweet_replies()
        example_using_iterators()

    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()