import tweepy
from django.conf import settings
from tweepy.auth import OAuthHandler
from sentry_sdk import capture_exception


def get_tweets():
    access_token = settings.TWITTER_ACCESS_TOKEN
    access_token_secret = settings.TWITTER_ACCESS_SECRET

    auth = OAuthHandler(
        settings.TWITTER_OAUTH_CONSUMER_KEY,
        settings.TWITTER_OAUTH_CONSUMER_SECRET,
    )
    auth.set_access_token(access_token, access_token_secret)

    api = tweepy.API(auth)

    twitter_users = [
        settings.TWITTER_DEPT_USER,
        settings.TWITTER_PERM_SEC_USER,
    ]

    tweets = []

    try:
        for twitter_user in twitter_users:
            if not twitter_user:
                continue
            for status in tweepy.Cursor(
                api.user_timeline,
                screen_name=twitter_user,
                include_rts=False,
                exclude_replies=True,
            ).items(5):
                tweets.append(status)
    except Exception as e:
        capture_exception(e)

    return tweets
