from sys import maxsize
import numpy as np
import pymongo
from pymongo.errors import DuplicateKeyError
from pymongo import MongoClient
from .DbInterface import DbInterface
from ..config import created_at_to_ts, REQUIRED_TWEET_ATTRS, \
    REQUIRED_USER_ATTRS, RETWEET_ATTRS

# collections used
TWEET_COLLECTION_NAME = "tweets"
USER_COLLECTION_NAME = "users"
PLACES_COLLECTION_NAME = "places"
META_COLLECTION_NAME = "meta"
RETWEET_COLLECTION_NAME = "retweets"

# all tweet attrs to collect, includes required and optional attributes
COLLECT_TWEET_ATTRS = REQUIRED_TWEET_ATTRS + \
                      ["coordinates", "place", "in_reply_to_id",
                       "in_reply_to_status_id", "quoted_id"]


class MongoCollector(DbInterface):
    def __init__(self, host, db_name):
        self.mongo = MongoClient(host=host)
        self.db = self.mongo.get_database(db_name)
        self.tweets = self.db[TWEET_COLLECTION_NAME]
        self.users = self.db[USER_COLLECTION_NAME]
        self.places = self.db[PLACES_COLLECTION_NAME]
        self.meta = self.db[META_COLLECTION_NAME]
        self.retweets = self.db[RETWEET_COLLECTION_NAME]

        self.setup()

    def setup(self):
        """create indexes"""
        tweet_indexes = [
            pymongo.IndexModel([("id", pymongo.ASCENDING)], unique=True),
            pymongo.IndexModel([("user_id", pymongo.ASCENDING)]),
            pymongo.IndexModel([("timestamp", pymongo.DESCENDING)]),
            pymongo.IndexModel([("full_text", pymongo.TEXT)]),
            pymongo.IndexModel([("coordinates", pymongo.GEOSPHERE)],
                               sparse=True)
        ]

        user_indexes = [
            pymongo.IndexModel([("id", pymongo.ASCENDING)], unique=True),
            pymongo.IndexModel([("last_tweet_id", pymongo.ASCENDING)],
                               unique=True),
            pymongo.IndexModel([("last_tweet_ts", pymongo.DESCENDING)])
        ]

        place_indexes = [
            pymongo.IndexModel([("id", pymongo.ASCENDING)], unique=True),
            pymongo.IndexModel([("bounding_box", pymongo.GEOSPHERE)],
                               sparse=True)
        ]

        meta_indexes = [
            pymongo.IndexModel([("timestamp", pymongo.DESCENDING)])
        ]

        retweet_indexes = [
            pymongo.IndexModel([("tweet_id", pymongo.ASCENDING)]),
            pymongo.IndexModel([("user_id", pymongo.ASCENDING)]),
            pymongo.IndexModel([("timestamp", pymongo.DESCENDING)])
        ]

        self.tweets.create_indexes(tweet_indexes)
        self.users.create_indexes(user_indexes)
        self.places.create_indexes(place_indexes)
        self.meta.create_indexes(meta_indexes)
        self.retweets.create_indexes(retweet_indexes)

    def get_user(self, user_id):
        return self.users.find_one({"id": user_id})

    def get_place(self, place_id):
        return self.places.findOne({"id": place_id})

    def get_max_tweet_id(self):
        """Assuming tweet ids are ordered."""

        max_id = list(self.tweets.find({}, {"_id": 0, "id": 1})
                      .sort("id", -1)
                      .limit(1))
        return max_id[0]["id"] if max_id else 0

    def get_min_tweet_id(self):

        max_id = list(self.tweets.find({}, {"_id": 0, "id": 1})
                      .sort("id", -1)
                      .limit(1))
        return max_id[0]["id"] if max_id else maxsize

    def insert_place(self, place_id, place_dict):

        # need to close bounding box for mongo geo index
        coords = []

        # need to connect box with end coord
        for box in place_dict["bounding_box"]["coordinates"]:

            # some boxes have 3 repeated coords; change Polygon to Point
            if len(np.unique(box)) < len(box):
                coords = box[0]
                place_dict["bounding_box"]["type"] = "Point"
                break
            box.append(box[0])
            coords.append(box)
        place_dict["bounding_box"]["coordinates"] = coords

        try:
            self.places.insert(place_dict)
        except DuplicateKeyError:
            return

    def insert_user(self, user_dict, tweet_ts, tweet_id):
        # delete all unused attributes
        del_keys = [key for key, val in user_dict.items() if key not in
                    REQUIRED_USER_ATTRS or val is None]

        for key in del_keys:
            del user_dict[key]

        user_dict["last_tweet_id"] = tweet_id
        user_dict["last_tweet_ts"] = tweet_ts

        # insert if does not exist, else update
        try:
            self.users.insert(user_dict)
        except DuplicateKeyError:
            if "_id" in user_dict:
                del user_dict["_id"]
            self.users.update(
                {"id": user_dict["id"], "last_tweet_ts": {"$lt": tweet_ts}},
                user_dict
            )

    def insert_tweet(self, tweet_attrs, user_attrs):

        # interface's method will make sure the required attributes are
        # present in the arguments.
        super().insert_tweet(tweet_attrs, user_attrs)

        # Remove all keys we are not interested in
        # ie those not in COLLECT_TWEET_ATTRS
        del_keys = [key for key, val in tweet_attrs.items() if key not in
                    COLLECT_TWEET_ATTRS or val is None]
        for key in del_keys:
            del tweet_attrs[key]

        # Set the tweets timestamp parsed from created_at string
        tweet_timestamp = created_at_to_ts(tweet_attrs["created_at"])
        tweet_attrs["timestamp"] = tweet_timestamp
        tweet_attrs["user_id"] = user_attrs["id"]

        # insert the user
        self.insert_user(user_attrs, tweet_timestamp, tweet_attrs["id"])

        # set place id and insert into places collection
        if "place" in tweet_attrs and tweet_attrs["place"]:
            tweet_attrs["place_id"] = tweet_attrs["place"]["id"]
            self.insert_place(tweet_attrs["place_id"], tweet_attrs["place"])
            del tweet_attrs["place"]

        try:
            self.tweets.insert(tweet_attrs)
        except DuplicateKeyError:
            return

    def insert_retweet(self, retweet, user):
        retweet["tweet_id"] = retweet["retweeted_status"]["id"]
        if "place" in retweet and retweet["place"]:
            retweet["place_id"] = retweet["place"]["id"]
            self.insert_place(retweet["place_id"], retweet["place"])

        retweet_ts = created_at_to_ts(retweet["created_at"])
        retweet["timestamp"] = retweet_ts

        self.insert_user(user, retweet_ts, retweet["id"])

        del_keys = [key for key in retweet if key not in RETWEET_ATTRS]
        for key in del_keys:
            del retweet[key]

        self.retweets.insert(retweet)
