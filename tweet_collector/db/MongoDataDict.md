Mongo Data Dictionary
=====================

#### Version 0.1.0
Within the given database  5 collections are made:

All documents have an _id field of type ObjectId (bson) auto generated
by mongo. These will be omitted from the following dictionary to keep it
brief.

The coordinate fields have a mongo geosphere index on them making them
easier to query with mongo geo queries



**meta** : metadata on each collection run
This is used by the mongo client and tweet collector to recover if
collection did not complete properly and not all tweets in a range
where collected

{

    next_max_id: (Number Long) The next tweet id to be collected,
    since_id: (NumberLong) collect up to this tweet id,
    done: (Boolean) Did this collection run exauhst all tweets
                in its path?
}

**places** : A shorter twitter place object for all tweets that are
marked with places. See the twitter doc for more details on this object,
especially the fields marked N/A

{

    id: (string) The twitter place id from the api, linking it to tweets,
    url: (string) twitter api endpoint to get more data on the place,
    place_type: (string) see twitter api for more details,
    name: (string) name of the place,
    full_name: (string) full name of the place (ex: state + country),
    country_code: (string) country abreviation (ex: US),
    country: (string) full country name,
    contained_within: N/A,
    bounding_box: (JOSN object) JSON formatted geocoordinates for the place: {
        type: (string) the type of coordinated,
        coordinated: (array) matching the expected type (ex: Point is an array
        of two points)
    },
    attributes: N/A
}

**retweets** : for retweets, links to the user who retweeted to
the retweet

{
    id: (NumberLong) The twitter tweet id,
    tweet_id: (NumberLong) The original tweet_id,
    created_at: (string) Twitter created at string,
    timestamp: (ISODate) Timestamp extrapolated from created_at field
}


**tweets** : collection of tweets!!

{

    id: (NumberLong) Twitter tweet id. These ids are not sqeuntial but
    are ordered
    created_at: (string) Twitter created at string,
    timestamp: (ISODate) Timestamp extrapolated from created_at field,
    full_text: (string) the tweet's full text (no truncation),
    is_retweeted: (Boolean, nullable) True if a tweet is collected from
    a retweet, otherwise field does not exist,
    user_id: (int) the user who tweeted the tweet,
    place_id: (string, nullable) link to place if place was tagged,
    coordinated: (coords dict) if coordinated were tagged in the tweet
}


**users** : dict of users

{

    id: (int) user id to link to tweets and retweets,
    name: (string) the user's name,
    screen_name: (string) unique name id,
    location: (string, nullable) user entered location,
    description: (string) user entered description,
    followers_count: (int) number of followers from last tweet,
    friends_count: (int) friends from last tweet,
    created_at: (string) Twitter created at string,
    timestamp: (ISODate) Timestamp extrapolated from created_at field,
    statuses_count: tweets tweeted as of last tweet collected,
    profile_image_url_https: secure url to user's profile image,
    last_tweet_id: (NumberLong) id of last tweet user tweeted,
    last_tweet_ts (ISODate) time of last tweet sent

}