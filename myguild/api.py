import json
import os

import pydiscourse
import requests

DiscourseClientError = pydiscourse.exceptions.DiscourseClientError


def init():
    api_key = _my_guild_env("MY_GUILD_API_KEY")
    api_username = _my_guild_env("MY_GUILD_API_USER")
    client = pydiscourse.DiscourseClient(
        "https://my.guild.ai",
        api_username=api_username,
        api_key=api_key,
    )
    _patch_client(client)
    return client


def _my_guild_env(name):
    try:
        return os.environ[name]
    except KeyError:
        raise SystemExit(
            f"{name} environment must be set for this command\n"
            "Try 'source <( gpg -d api-<user>.gpg )' to set it."
        )


def _patch_client(client):
    # Weird 413 errors from server when `json` arg is `{}` (the
    # default). Replace api._request to ensure it's None, which works
    # fine.
    request0 = client._request

    def patched_request(*args, **kw):
        json = kw.pop("json", None)
        return request0(*args, json=json, **kw)

    client._request = patched_request


def public_get_data(url):
    resp = requests.get(url)
    if not resp.ok:
        if resp.status_code == 404:
            raise DiscourseClientError("not found: %s" % url)
        else:
            raise DiscourseClientError(
                "error reading '%s': %s (%i)" % (url, resp.reason, resp.status_code)
            )
    assert "application/json" in resp.headers.get("content-type", ""), resp.headers
    return json.loads(resp.content)
