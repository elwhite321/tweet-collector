import os
import sys
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
    if daemon:
        pid = os.fork()
        if pid == 0:
            with open(f"{db_name}.log", 'a') as log_fp:
                with open(f"{db_name}.err", 'a') as err_fp:
                    sys.stdout = log_fp
                    sys.stderr = err_fp
                    start_collector(q, db_type, db_address, db_name, recover)
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
        else:
            print(f"Starting collector in daemon pid: {pid}")
            sys.exit(0)
    else:
        start_collector(q, db_type, db_address, db_name, recover)


cli.add_command(auth)


def start_collector(q, db_type, db_address, db_name, recover):
    db_obj = None
    if db_type == "mongo":
        db_obj = MongoCollector(db_address, db_name)

    if db_obj:
        collector = TweetCollector(db_obj, q, recover=recover)
        collector.start_collector()
    else:
        print(f"No database object associated with {db_type}.")


if __name__ == "__main__":
    cli()
