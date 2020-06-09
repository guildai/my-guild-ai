import os

import pydiscourse

DiscourseClientError = pydiscourse.exceptions.DiscourseClientError


def init():
    try:
        api_key = os.environ["MY_GUILD_API_KEY"]
    except KeyError:
        raise SystemExit("MY_GUILD_API_KEY environment must be set for this command")
    else:
        return pydiscourse.DiscourseClient(
            "https://my.guild.ai", api_username="guildai", api_key=api_key
        )
