import json
import os

import pydiscourse
import requests

DiscourseClientError = pydiscourse.exceptions.DiscourseClientError


def init():
    try:
        api_key = os.environ["MY_GUILD_API_KEY"]
    except KeyError:
        raise SystemExit(
            "MY_GUILD_API_KEY environment must be set for this command\n"
            "Try 'source <( gpg -d api-creds.gpg )' to set it."
        )
    else:
        client = pydiscourse.DiscourseClient(
            "https://my.guild.ai", api_username="guildai", api_key=api_key
        )
        _patch_client(client)
        return client


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
