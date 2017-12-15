Tweet Collector
===

A multithreaded tweet collector

#### UNDER DEVELOPMENT - TODO:
This project is still under development. At a minimum the following need to be done:
* tests tests and more tests. No tests currently :/
* Needs logging (multiloger with slack logging). Just a couple lazy print statments currently

#### OTHER FEATURES - TODO:
* add sql db module
* enhance the cli tool take more search api params


## Addind a db module
This is not a trivial task. The db module needs to structure the database tables and make sure
the unique fields are thread safe. See more at the [db readme](https://github.com/elwhite321/tweet-collector/tree/master/tweet_collector/db).


