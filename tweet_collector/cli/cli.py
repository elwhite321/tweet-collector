import os
import sys
import logging
import click
from .auth_cli.commands import auth
from tweet_collector.db.mongo import MongoCollector
from tweet_collector.tweet_collector import TweetCollector


@click.group()
def cli():
    """run the cli. triggered in __main__.py"""


@cli.command("collect")
@click.argument("q")
@click.argument("db-type")
@click.argument("db-address")
@click.argument("db-name")
@click.option("--recover", is_flag=True)
@click.option("--daemon", is_flag=True)
def collect_tweets(q, db_type, db_address, db_name, recover, daemon):
    formatter = logging.Formatter("[ %(asctime)s ] \t\t %(message)s")
    fileHandle = logging.FileHandler(f"{db_name}.log")
    fileHandle.setFormatter(formatter)
    logger = logging.getLogger(db_name)
    logger.addHandler(fileHandle)
    logger.setLevel(logging.INFO)

    if daemon:
        print("Forking daemon process")
        pid = os.fork()
        if pid == 0:
            start_collector(q, db_type, db_address,
                db_name, recover, logger)
        else:
            print(f"Starting collector in daemon pid: {pid}")
            sys.exit(0)
    else:
        start_collector(q, db_type, db_address, db_name, logger)


cli.add_command(auth)


def start_collector(q, db_type, db_address, db_name, recover, logger):
    db_obj = None
    if db_type == "mongo":
        db_obj = MongoCollector(db_address, db_name)

    if db_obj:
        collector = TweetCollector(db_obj, q, logger=logger)
        collector.start_collector()
    else:
        print(f"No database object associated with {db_type}.")


if __name__ == "__main__":
    cli()
