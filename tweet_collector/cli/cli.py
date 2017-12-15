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
def collect_tweets(q, db_type, db_address, db_name):
    db_obj = None
    if db_type == "mongo":
        db_obj = MongoCollector(db_address, db_name)
        print(db_obj)

    if db_obj:
        collector = TweetCollector(db_obj, q)
        collector.start_collector()


cli.add_command(auth)

if __name__ == "__main__":
    cli()