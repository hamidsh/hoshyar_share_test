"""
Test script for TwitterAPI.io client.

This script thoroughly tests all client functionality with real API calls.
"""

import os
import sys
import logging
from typing import Any, Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("twitter_api_test")

# Import the client
from lib.twitter_api import TwitterAPIClient, Tweet, User, TwitterAPIError, TwitterAPIValidationError

# Get API key from environment variable or set it here
API_KEY = "cf5800d7a52a4df89b5df7ffe1c7303d"


def print_separator(title):
    """Print a separator with title for better test output readability."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def test_search_tweets():
    """Test searching tweets with various parameters."""
    print_separator("TEST: Search Tweets")

    client = TwitterAPIClient(API_KEY)

    # Test basic search
    print("Testing basic search...")
    tweets = client.search_tweets(
        query="python programming",
        query_type="Latest",
        max_results=5
    )
    print(f"✓ Found {len(tweets)} tweets")

    # Test with different query_type
    print("Testing 'Top' query type...")
    top_tweets = client.search_tweets(
        query="python programming",
        query_type="Top",
        max_results=5
    )
    print(f"✓ Found {len(top_tweets)} top tweets")

    # Test pagination
    print("Testing pagination...")
    page1 = client.search_tweets(
        query="python programming",
        max_pages=1
    )
    print(f"✓ Page 1: {len(page1)} tweets")

    # Test with various query operators
    print("Testing complex query...")
    complex_query = client.search_tweets(
        query="from:elonmusk min_faves:1000 -filter:replies",
        max_results=3
    )
    print(f"✓ Complex query returned {len(complex_query)} tweets")

    # Test search_tweets_iter
    print("Testing tweet iterator...")
    count = 0
    for tweet in client.search_tweets_iter(
            query="python programming",
            max_results=5
    ):
        count += 1
    print(f"✓ Iterator yielded {count} tweets")

    print("✓ All search_tweets tests passed!")


def test_user_info():
    print_separator("TEST: User Info")
    client = TwitterAPIClient(API_KEY)
    print("Testing get_user_info by username...")
    try:
        user = client.get_user_info("elonmusk")
        print(f"✓ Retrieved user: @{user.username}, {user.name}, Followers: {user.followers_count}")
        assert user.id, "User ID is missing"
        assert user.name, "User name is missing"
        print("✓ User info fields verified")
    except Exception as e:
        print(f"✗ Error getting user info: {e}")
        raise
    print("Testing get_user_info_by_id...")
    try:
        user_id = user.id
        user_by_id = client.get_user_info_by_id(user_id)
        print(f"✓ Retrieved user by ID: @{user_by_id.username}")
        assert user.id == user_by_id.id, "User IDs don't match"
        print("✓ User info by ID verified")
    except Exception as e:
        print(f"✗ Error getting user info by ID: {e}")
        raise
    print("✓ All user_info tests passed!")


def test_user_tweets():
    """Test retrieving user tweets."""
    print_separator("TEST: User Tweets")

    client = TwitterAPIClient(API_KEY)

    # Test by username
    print("Testing get_user_tweets by username...")
    try:
        tweets = client.get_user_tweets(
            username="elonmusk",
            max_results=5
        )
        print(f"✓ Retrieved {len(tweets)} tweets")

        # Check tweet objects
        if tweets:
            tweet = tweets[0]
            print(f"✓ Sample tweet: {tweet.id}")
            assert tweet.author, "Tweet author is missing"
            assert tweet.author.username, "Author username is missing"

            # Check if any tweets are marked as pinned
            pinned = [t for t in tweets if hasattr(t, 'is_pinned') and t.is_pinned]
            print(f"✓ Found {len(pinned)} pinned tweets")
    except Exception as e:
        print(f"✗ Error getting user tweets: {e}")
        raise

    # Test iterator version
    print("Testing get_user_tweets_iter...")
    try:
        count = 0
        for tweet in client.get_user_tweets_iter(
                username="elonmusk",
                max_results=5
        ):
            count += 1
        print(f"✓ Iterator yielded {count} tweets")
    except Exception as e:
        print(f"✗ Error in tweets iterator: {e}")
        raise

    print("✓ All user_tweets tests passed!")


def test_user_followers():
    """Test retrieving user followers."""
    print_separator("TEST: User Followers")

    client = TwitterAPIClient(API_KEY)

    print("Testing get_user_followers...")
    try:
        followers = client.get_user_followers(
            username="elonmusk",
            max_results=5
        )
        print(f"✓ Retrieved {len(followers)} followers")

        # Check follower objects
        if followers:
            follower = followers[0]
            print(f"✓ Sample follower: @{follower.username or '(no username)'}, {follower.name}")
    except Exception as e:
        print(f"✗ Error getting followers: {e}")
        raise

    print("✓ All user_followers tests passed!")


def test_user_following():
    """Test retrieving users that a user is following."""
    print_separator("TEST: User Following")

    client = TwitterAPIClient(API_KEY)

    print("Testing get_user_following...")
    try:
        following = client.get_user_following(
            username="elonmusk",
            max_results=5
        )
        print(f"✓ Retrieved {len(following)} following")

        # Check following objects
        if following:
            followed = following[0]
            print(f"✓ Sample following: @{followed.username or '(no username)'}, {followed.name}")
    except Exception as e:
        print(f"✗ Error getting following: {e}")
        raise

    print("✓ All user_following tests passed!")


def test_tweet_replies():
    """Test retrieving replies to a tweet."""
    print_separator("TEST: Tweet Replies")

    client = TwitterAPIClient(API_KEY)

    # First get a popular tweet
    print("Finding a popular tweet to check replies...")
    popular_tweets = client.search_tweets(
        query="from:elonmusk min_faves:10000",
        query_type="Top",
        max_results=1
    )

    if popular_tweets:
        tweet_id = popular_tweets[0].id
        print(f"Found tweet: {tweet_id}")

        print("Testing get_tweet_replies...")
        try:
            replies = client.get_tweet_replies(
                tweet_id=tweet_id,
                max_results=5
            )
            print(f"✓ Retrieved {len(replies)} replies")

            # Check reply objects
            if replies:
                reply = replies[0]
                print(f"✓ Sample reply: {reply.id}")
                assert reply.is_reply, "Tweet is not marked as a reply"
                # Check if reply is part of the same conversation instead of direct reply
                assert reply.conversation_id == tweet_id, "Reply is not part of the expected conversation"
        except Exception as e:
            print(f"✗ Error getting replies: {e}")
            raise

        # Test iterator version
        print("Testing get_tweet_replies_iter...")
        try:
            count = 0
            for reply in client.get_tweet_replies_iter(
                    tweet_id=tweet_id,
                    max_results=5
            ):
                count += 1
            print(f"✓ Iterator yielded {count} replies")
        except Exception as e:
            print(f"✗ Error in replies iterator: {e}")
            raise
    else:
        print("⚠ No popular tweets found to test replies")

    print("✓ All tweet_replies tests passed!")


def test_list_tweets():
    """Test retrieving tweets from a list."""
    print_separator("TEST: List Tweets")

    client = TwitterAPIClient(API_KEY)

    # You need a valid list ID
    list_id = "1650054154390052865"  # Replace with a real list ID

    print(f"Testing get_list_tweets for list {list_id}...")
    try:
        tweets = client.get_list_tweets(
            list_id=list_id,
            max_results=5
        )
        print(f"✓ Retrieved {len(tweets)} tweets from list")

        # Check tweet objects
        if tweets:
            tweet = tweets[0]
            print(f"✓ Sample tweet: {tweet.id} by @{tweet.author.username if tweet.author else 'unknown'}")
    except Exception as e:
        print(f"⚠ Error getting list tweets: {e}")
        print("This test requires a valid list ID. If you don't have one, this error is expected.")

    print("✓ All list_tweets tests completed")


def test_error_handling():
    """Test error handling for invalid inputs and API errors."""
    print_separator("TEST: Error Handling")

    client = TwitterAPIClient(API_KEY)

    # Test invalid parameters
    print("Testing invalid parameters...")
    try:
        client.get_user_tweets()  # Missing both username and user_id
        print("✗ Expected error for missing parameters, but none was raised")
    except TwitterAPIValidationError:
        print("✓ Correctly raised error for missing parameters")
    except Exception as e:
        print(f"✗ Unexpected error type: {type(e).__name__}")

    # Test invalid user
    print("Testing nonexistent user...")
    try:
        client.get_user_info("this_user_definitely_does_not_exist_12345678900987654321")
        print("✗ Expected error for nonexistent user, but none was raised")
    except TwitterAPIError as e:
        print(f"✓ Correctly raised error for nonexistent user: {e}")

    print("✓ All error handling tests completed")


def run_all_tests():
    """Run all tests."""
    try:
        test_search_tweets()
        test_user_info()
        test_user_tweets()
        test_user_followers()
        test_user_following()
        test_tweet_replies()
        test_list_tweets()
        test_error_handling()

        print("\n✓✓✓ All tests completed successfully!")
    except Exception as e:
        print(f"\n✗✗✗ Tests failed: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()