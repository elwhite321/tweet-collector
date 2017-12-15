"""Set authentication for the """

import os
import json
import requests
import base64
from getpass import getpass
import click
from tweet_collector.auth import get_bearer


DEFAULT_OUTPUT = os.path.join(os.path.expanduser("~"),
                              ".twitter",
                              "auth.json")


@click.group()
def auth():
    """authentication api"""


@auth.command("set-tokens")
@click.argument("name", required=False)
@click.argument("key", required=False)
@click.argument("secret", required=False)
@click.option("--input-file")
@click.option("--output_file")
def set_tokens(name, key, secret, input_file, output_file):
    """
    Set the bearer token to use with twitter search api
    :param name: 
    :param key: 
    :param secret: 
    :param input_file: 
    :param output_file: 
    :return: 
    """
    auth_keys = {}
    # check either key and secret or input file were passed to the cli
    if (name and key and secret) or (input_file and os.path.exists(input_file)):
        if name and key and secret:
            auth_keys[name] = {key: secret}
        if input_file and os.path.exists(input_file):
            with open(input_file) as fp:
                for line in fp:
                    if not line.strip().startswith('#'):
                        name, key, secret = line.strip().split(" ")
                        auth_keys[name] = {key: secret}
    else:
        user = input("Application name: ")
        key = getpass(prompt="Consumer key: ")
        secret = getpass(prompt="Consumer secret: ")
        auth_keys[user] = {key: secret}

    if not output_file:
        output_file = DEFAULT_OUTPUT

    if not os.path.exists(output_file):
        path, filename = os.path.split(output_file)
        if not os.path.exists(path):
            os.mkdir(path)
        with open(output_file, "w") as fp:
            json.dump({}, fp)
    with open(output_file, 'r') as fp:
        try:
            output_auth = json.load(fp)
        except json.decoder.JSONDecodeError:
            print("Could not decode auth_cli.json file. Overriding file")
            output_auth = {}

        print(auth_keys)
        for name, creds in auth_keys.items():
            key, secret = list(creds.items())[0]
            try:
                bearer = get_bearer(key, secret)
                output_auth[name] = bearer
            except requests.exceptions.HTTPError as e:
                print(f"HTTPError for account {name} {e}")
    with open(output_file, 'w') as fp:
        json.dump(output_auth, fp)
