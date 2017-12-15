import os
import json
import requests
import base64

DEFAULT_AUTH_FILE = os.path.join(
    os.path.expanduser("~"), ".twitter", "auth.json"
)


def get_bearer(key, secret):
    cred_str = str.encode(f"{key}:{secret}")
    creds = base64.b64encode(cred_str).decode("utf-8")
    auth_header = {
        "Authorization": f"Basic {creds}",
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
    }
    body = "grant_type=client_credentials"
    res = requests.post("https://api.twitter.com/oauth2/token",
                        data=body,
                        headers=auth_header)
    json_res = res.json()
    if res.ok:
        return {
            "token_type": json_res["token_type"],
            "access_token": res.json()["access_token"]
        }
    else:
        res.raise_for_status()


def get_tokens(auth_file=DEFAULT_AUTH_FILE):
    with open(auth_file, 'r') as fp:
        return list(json.load(fp).values())


def get_auth_header(token):
    return {
        "Authorization": f"{token['token_type']} {token['access_token']}"
    }
