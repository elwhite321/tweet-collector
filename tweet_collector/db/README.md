# Data Interface

The tweet collector uses classes derived from the DbInterface class. This
makes the collector usable with different database classes.

## DbInterface

#### Config.py
The config.py file supplies the following for the database interface and its
derived class:
 * Required tweet and user attributes
 * The datetime formating string and a function to convert the created_at
 field to a timestamp.

Creating a derived class
---
Derive the class from the DbInterface class.

In each class, create USER_ATTRS and TWEET_ATTRS variables to indicate the
optional attributes collected by the database.

Call the parent's insert_tweet function like so:  `super().insert_tweet
(twitter_attrs, user_attrs)`  The parent method will check that the required
atttributes are defined with in the twitter and user attribute dicts.

Check the DbInterface class's docstrings for more information on the required
 override methods, their expected arguments, and return values.

Thread Safety
---

The tweets are inserted into the database in different threads. Thus the order
of insertion cannot be garunteed. Extra care must be taken to inserting places
and users with unique fields. Checking the user instance is in the db before
inserting will cause a race condition and thus is insuficient. It eventually would 
be the case that the user will be entered into the db by a seperate thread after 
a different thread has checked the user is not in the db but before said thread
enters the user into the db. A duplicate key error will be thrown.
