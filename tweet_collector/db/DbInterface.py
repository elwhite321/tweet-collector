"""Interface class for adding a database interface for the tweet collector
to use

The tweet collector is threaded. The order of inserts to the database
cannot be predicted. """

import abc
from ..config import REQUIRED_USER_ATTRS, REQUIRED_TWEET_ATTRS

class DbInterface(abc.ABC):
    @abc.abstractmethod
    def get_max_tweet_id(self):
        """Id of the newest tweet in the database. The collector will 
        collect tweets with ids greater then this one.
        
        Returns:
            (int) max tweet id or 0 if no tweets have been entered yet
        """

    @abc.abstractmethod
    def insert_retweet(self, retweet, user):
        """insert a retweet, a reference to the original tweet"""

    @abc.abstractmethod
    def insert_tweet(self, tweet_attrs, user_attrs):
        """Insert a t tweet and user into the database. 
        super().insert_tweet(twitter_attrs, user_attrs) should be used to check 
        the attrs dicts have the minimum required keys we want to collect
        
        TODO:
            Check if user is added already in the database to 
            avoid duplicates. Update appropriate fields if duplicate
            user (example: followers_count). Also for followers count, 
            can have a followers_count: {'timetamp": follower_count } structure.
            
            Check for duplicate tweet. Raise warning on duplicate tweet and 
            ignore tweet.
            
            Use created_at field to make a timestamp field. In tweet colleciton 
            / table, insert as timestamp. In user update a counts object to 
            reflect changes in followers_count, following_count, listed_count,
            and any other counting data kept. Do this in a way to keep 
            historical counting data at each tweet.

        Args:
            tweet_attrs: dict of twitter attributes
            user_attrs: dict of user attributes


        Returns: None
        """

        missing_tweet_attrs = [key for key in REQUIRED_TWEET_ATTRS
                               if key not in tweet_attrs.keys()
                               or tweet_attrs[key] is None]

        missing_user_attrs = [key for key in REQUIRED_USER_ATTRS
                              if key not in user_attrs.keys()
                              or user_attrs[key] is None]

        if missing_user_attrs or missing_tweet_attrs:
            raise KeyError(f"Missing attributes:\n\tmissing tweet"
                           f"attributes: {missing_tweet_attrs}\n\t"
                           f"missing user attributes {missing_user_attrs}")
        return
