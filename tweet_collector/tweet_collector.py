import os
import json
from sys import maxsize
import requests
import asyncio
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import multiprocessing
from datetime import datetime
import time

from tweet_collector.auth import DEFAULT_AUTH_FILE, get_auth_header, get_tokens


class TweetCollector(object):
    def __init__(self, db_obj, q, auth_file=DEFAULT_AUTH_FILE, **kwargs):

        # get auth tokens from file set by auth cli
        self.tokens = get_tokens(auth_file=auth_file)
        if not self.tokens:
            raise ValueError("twitter api tokens not set. Use cli tool "
                             "to set tokens")

        # get remaining search limits from twitter api
        self.token_reset_ts, self.token_limit_remaining = \
            self.get_current_rate_limits()

        self.db = db_obj

        # parse input search params (passed through kwargs); restrict to
        # following
        used_search_params = ["geocode", "lang", "locale", "result_type"]
        del_keys = [key for key in kwargs if key not in used_search_params]
        if del_keys:
            print(f"Unused parameters passed to collector: {del_keys}")
        for key in del_keys:
            del kwargs[key]

        # set up url and parameters
        self.host = f"https://api.twitter.com/1.1/search/tweets.json?q={q}"
        self.count = 100

        # set the next_max_id to collect the most recent tweets
        self.__next_max_id = maxsize

        # get the since_id (max tweet id) from the database
        # collect tweets with ids greater then this one

        # set some of the static api parameters we will use

        self.params = {
            **kwargs,
            "q": q,
            "count": self.count,
            "tweet_mode": "extended",
            "since_id": self.db.get_max_tweet_id()
        }

        self.tweets_collected = 0

        # set the executor for the event loop run_in_executor
        cpus = multiprocessing.cpu_count()
        max_workers = (cpus - 2) if cpus > 2 else 1
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def get_current_rate_limits(self):
        """Get the tokens current rate limits to help __init__ class vals"""
        url = "https://api.twitter.com/1.1/application/rate_limit_status.json" \
              "?resources=search"
        token_reset_ts = []
        token_limit_remaining = []
        for token in self.tokens:
            res = requests.get(url, headers=get_auth_header(token)).json()
            rate_info = res["resources"]["search"]["/search/tweets"]
            token_reset_ts.append(rate_info["reset"])
            token_limit_remaining.append(rate_info["remaining"])

        print(token_reset_ts, token_limit_remaining)
        return token_reset_ts, token_limit_remaining

    def get_next_url(self):
        next_url = self.host
        for param, value in self.params.items():
            next_url += f"&{param}={value}"
        next_url += f"&max_id={self.__next_max_id}"
        return next_url

    def get_min_id(self, tweets):
        """get the min id in a group of tweets to use with the next api call"""
        return min(tweets, key=lambda tweet: tweet["id"])["id"] - 1

    def get_next_token(self):
        """get the next token that is ready for use or wait for the next 
        token to be ready"""
        while True:
            self.token_reset_ts, self.token_limit_remaining = \
                self.get_current_rate_limits()
            if max(self.token_limit_remaining) > 0:
                token_idx = np.argmax(self.token_limit_remaining)

            else:
                token_idx = np.argmin(self.token_reset_ts)
                token_reset_ts = self.token_reset_ts[token_idx]
                sleep_for = token_reset_ts - datetime.now().timestamp() + 1
                if sleep_for > 0:
                    print(f"SLEEPING FOR TOKEN: {sleep_for/60} min")
                    time.sleep(sleep_for)
                    self.token_reset_ts, self.token_limit_remaining = \
                        self.get_current_rate_limits()
            yield self.tokens[token_idx], token_idx

    def start_collector(self):
        """start collecting tweets"""
        insert_tweet_tasks = []
        done = False
        for token, token_idx in self.get_next_token():
            print(f"SWITCHING TOKENS: {token_idx}")
            # initialize rate limit info for this token
            limit_remaining = self.token_limit_remaining[token_idx]
            # loop while the token is not over the rate limit
            while limit_remaining > 0 and not done:

                # get the next url using __next_max_id set in the previous iter
                next_url = self.get_next_url()
                limit_remaining, limit_reset, tasks, done = \
                    self.get_tweets(next_url, token)

                if limit_remaining is None:
                    print("Did not receive limit_remaining from response")
                    self.token_reset_ts, self.token_limit_remaining = \
                        self.get_current_rate_limits()
                    limit_remaining = self.token_limit_remaining[token_idx]

                print(limit_remaining, self.tweets_collected)

                insert_tweet_tasks += tasks

            self.token_reset_ts[token_idx] = limit_reset
            self.token_limit_remaining[token_idx] = limit_remaining
            if done:
                break

        # handle insert_tweet_tasks
        self.block_for_futures(insert_tweet_tasks)

    def get_tweets(self, url, token):
        """get the tweets in an async manner"""
        auth_header = get_auth_header(token)
        res = requests.get(url, headers=auth_header)
        # if the request fails, raise an error
        res.raise_for_status()
        tweets = res.json()["statuses"]

        # get next max id before insert_tweet changes the tweets
        self.__next_max_id = self.get_min_id(tweets)

        # insert tweets into db
        insert_tasks = self.insert_tweets(tweets)

        # if the api returned less then the number of tweets requested,
        # it has no more tweets for us.
        if len(tweets) == 0:
            done = True
        else:
            done = False
            # set the max_id param for the next api call (used by get_next_url)

        # get the rate limiting information from the header
        limit_remaining = int(res.headers["x-rate-limit-remaining"]) if \
            "x-rate-limit-remaining" in res.headers else None
        limit_reset = int(res.headers["x-rate-limit-reset"]) if \
            "x-rate-limit-reset" in res.headers else None

        return limit_remaining, limit_reset, insert_tasks, done

    async def await_futures(self, futures):
        completed, pending = await asyncio.wait(futures)
        return [task.result() for task in completed]

    def block_for_futures(self, futures):
        if futures:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.await_futures(futures))
        return []

    def insert_tweets(self, tweets):
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(self.executor, self.insert_tweet, tweet)
            for tweet in tweets
        ]
        return tasks

    def insert_tweet(self, tweet):
        if "retweeted_status" in tweet:
            self.insert_tweet(tweet["retweeted_status"])
            self.db.insert_retweet(tweet, tweet["user"])

        else:
            if "quoted_status" in tweet:
                quoted_tweet = tweet["quoted_status"]
                tweet["quoted_id"] = quoted_tweet["id"]
                self.insert_tweet(quoted_tweet)

            self.db.insert_tweet(tweet, tweet["user"])
            self.tweets_collected += 1
