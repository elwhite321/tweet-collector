from datetime import datetime

# Required attributes to collect from the tweet
REQUIRED_TWEET_ATTRS = [
    "created_at", "id", "full_text"
]

RETWEET_ATTRS = [
    "user_id", "tweet_id", "created_at", "place_id", "timestamp"
]

# Required user attributes to collect
REQUIRED_USER_ATTRS = [
    "screen_name", "name", "location", "profile_image_url_https", "id",
    "followers_count", "created_at", "friends_count", "statuses_count",
    "description",
]



# Tweets created_at filed datetime format for datetime.strptime
CREATED_AT_DATETIME_FORMAT = "%a %b %d %H:%M:%S %z %Y"


def created_at_to_ts(created_at):
    return datetime.strptime(created_at, CREATED_AT_DATETIME_FORMAT)
