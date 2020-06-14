import datetime
import json
import logging
import os
import pprint
import re
import socket
import subprocess
import time

import requests

from .api import init as init_api
from .api import DiscourseClientError
from .log_util import get_logger

from . import cache

log = get_logger()


COMMAND_HELP_POST_TEMPLATE = """
<div data-theme-toc="true"></div>
<div data-guild-cmd="true"></div>

### Usage

``` command
{usage[prog]} {usage[args]}
```

{formatted_help}

{formatted_options}{formatted_subcommands}

*Guild AI version {version}*
"""

COMMAND_INDEX_TEMPLATE = """
{header}

{formatted_commands}

*Guild AI version {version}*
"""

_cache = {}


class NoSuchCommand(Exception):
    pass


def _retry(desc, f, max_attempts=3, delay=1):
    attempts = 0
    while True:
        attempts += 1
        try:
            return f()
        except Exception as e:
            if attempts == max_attempts:
                raise
            if log.getEffectiveLevel() <= logging.DEBUG:
                log.exception(desc)
            log.error("Error running %s: %s", desc, e)
            log.info("Retrying %s after %0.1f seconds", desc, delay)
            time.sleep(delay)


###################################################################
# Publish commands
###################################################################


def publish_commands(commands, preview=False, check=False):
    api = init_api()
    commands = sorted(_guild_commands(commands))
    for name, data in commands:
        _sync_command(name, data, preview, check, api)


def _guild_commands(cmd_names=None):
    cmds = []
    if cmd_names:
        _acc_command_data(cmd_names, cmds)
    else:
        _acc_recurse_command_data("", cmds)
    return cmds


def _acc_command_data(cmd_names, cmds):
    for cmd in cmd_names:
        try:
            data = _get_cmd_help_data(cmd)
        except NoSuchCommand:
            log.error("No such command '%s'", cmd)
        else:
            cmds.append((cmd, data))


def _acc_recurse_command_data(base_cmd, acc):
    (help_data, subcommands) = _cmd_help(base_cmd)
    if base_cmd:
        acc.append((base_cmd, help_data))
    for cmd in subcommands:
        _acc_recurse_command_data(cmd, acc)


def _cmd_help(cmd):
    help_data = _get_cmd_help_data(cmd)
    log.debug("Help data for %s: %r", cmd, help_data)
    subcommands = _subcommands_for_help_data(help_data, cmd)
    return help_data, subcommands


def _get_cmd_help_data(cmd):
    cmd_desc = _cmd_desc(cmd)
    cached = cache.read(_cmd_cache_key(cmd))
    if cached:
        log.info("Reading cached command info for %s", cmd_desc)
        return json.loads(cached)
    log.info("Fetching command info for %s", cmd_desc)
    help_cmd = "guild %s --help" % cmd
    help_env = dict(os.environ)
    help_env["GUILD_HELP_JSON"] = "1"
    p = subprocess.Popen(
        help_cmd,
        env=help_env,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    out, err = p.communicate()
    if p.returncode != 0:
        log.debug("Error reading help for '%s': %s", cmd, err)
        raise NoSuchCommand(cmd)
    cache.write(_cmd_cache_key(cmd), out)
    return json.loads(out)

def _cmd_desc(cmd):
    if cmd:
        return "'%s'" % cmd
    else:
        return "guild base command"


def _cmd_cache_key(cmd):
    return "command:%s" % cmd


def _subcommands_for_help_data(help_data, base_cmd):
    subcommands = []
    for cmd in help_data.get("commands", []):
        for term in _split_cmd_term(cmd["term"]):
            subcommands.append(_join_cmd(base_cmd, term))
    return subcommands


def _split_cmd_term(cmd_term):
    """Splits a command term into mutiple parts.

    Command terms may contain aliases, which are included in the
    parts.
    """
    return [part.strip() for part in cmd_term.split(",")]


def _join_cmd(base_cmd, subcmd):
    if not base_cmd:
        return subcmd
    return "%s %s" % (base_cmd, subcmd)


def _sync_command(cmd, data, preview, check, api):
    _retry(
        "sync command '%s'" % cmd,
        lambda: _sync_command_impl(cmd, data, preview, check, api),
        max_attempts=3,
        delay=5,
    )


def _sync_command_impl(cmd, data, preview, check, api):
    try:
        post = _get_command_topic_post(cmd, api)
    except DiscourseClientError:
        _create_command_post(cmd, data, preview, check, api)
    else:
        _publish_command(cmd, data, post, api, preview=preview, check=check)


def _get_command_topic_post(cmd, api):
    assert cmd
    log.info("Fetching published help topic for '%s' from server", cmd)
    try:
        # Try permalink first.
        topic = api._get(_command_permalink(cmd))
    except DiscourseClientError:
        # If permalink doesn't exist, try topic link.
        topic = api._get(_command_topic_link(cmd))
    return api.post(topic["post_stream"]["posts"][0]["id"])


def _command_topic_link(cmd):
    return "/t/%s" % _command_help_slug(cmd)


def _command_permalink(cmd):
    return "/commands/%s" % cmd.replace(" ", "-")


def _create_command_post(cmd, data, preview, check, api):
    category = _commands_category(api)
    content = _format_command_help_post(cmd, data)
    if preview:
        print(content)
    if check:
        log.warning("Help topic for '%s' does not exist", cmd)
    if check or preview:
        return
    log.action("Creating help topic post for '%s'", cmd)
    title = _command_help_title(cmd)
    post = api.create_post(content, category, title=title)
    log.info("Created help topic post %s '%s' for '%s'", post["id"], title, cmd)


def _command_help_title(cmd):
    return "Command: %s" % cmd


def _commands_category(api):
    try:
        return _cache["commands_category"]
    except KeyError:
        id = _guild_commands_topic_category(api)
        _cache["commands_category"] = id
        return id


def _guild_commands_topic_category(api):
    try:
        topic = api.topic("guild-commands")
    except api.DiscourseClientError:
        raise SystemExit(
            "cannot find 'guild-commands' topic, which is required to "
            "denote the Commands category - create this topic and run "
            "this command again"
        )
    return topic["category_id"]


def _publish_command(cmd, help_data, post, api, preview, check):
    formatted_help = _format_command_help_post(cmd, help_data)
    if preview:
        print(formatted_help)
        if not check:
            return
    if post["raw"].strip() == formatted_help:
        log.info("Help topic post %s for '%s' is up-to-date", post["id"], cmd)
        return
    if check:
        log.warning(
            "Help topic post %s for '%s' is out-of-date", post["id"], cmd,
        )
        return
    comment = _publish_command_comment(help_data)
    log.action("Updating help topic post %s for '%s'", post["id"], cmd)
    api.update_post(post["id"], formatted_help, comment)


def _format_command_help_post(cmd, help_data):
    post = COMMAND_HELP_POST_TEMPLATE.format(
        formatted_help=_format_command_help(help_data),
        formatted_options=_format_command_help_options(help_data),
        formatted_subcommands=_format_command_subcommands(cmd, help_data),
        **help_data
    )
    return _apply_command_refs(post).strip()


def _format_command_help(help_data):
    return _remove_paragraph_lfs(help_data["help"])


def _remove_paragraph_lfs(s):
    return re.sub(r"(\S)\n(\S)", r"\1 \2", s)


def _format_command_help_options(help_data):
    lines = ["### Options", "", "| | |", "|-|-|"]
    lines.extend([_format_command_option(option) for option in help_data["options"]])
    return "\n".join(lines)


def _format_command_option(option):
    return "|`%s`|%s|" % (option["term"], option["help"])


def _format_command_subcommands(cmd, help_data):
    subcommands = help_data.get("commands")
    if not subcommands:
        return ""
    lines = [
        "",
        "",
        "### Subcommands",
        "",
        "" "| | |",
        "|-|-|",
    ]
    lines.extend([_format_subcommand(cmd, subcmd) for subcmd in subcommands])
    return "\n".join(lines)


def _format_subcommand(cmd, subcmd):
    return "|%s|%s|" % (_format_subcommand_links(cmd, subcmd), subcmd["help"])


def _format_subcommand_links(cmd, subcmd):
    return ", ".join(
        [_format_subcommand_link(cmd, term) for term in _split_cmd_term(subcmd["term"])]
    )


def _format_subcommand_link(base_cmd, subcmd_term):
    return "[%s](%s)" % (
        subcmd_term,
        _command_permalink(_join_cmd(base_cmd, subcmd_term)),
    )


def _apply_command_refs(s):
    parts = re.split(r"(``guild .+ --help``)", s)
    return "".join([_try_command_ref(part) or part for part in parts])


def _try_command_ref(s):
    m = re.match(r"``guild (.+) --help``", s)
    if m:
        return "[`guild %s`](%s)" % (m.group(1), _command_permalink(m.group(1)))
    return None


def _publish_command_comment(help_data):
    return (
        "Command help published for Guild AI version "
        "{version} from {host} on {utc_date}Z".format(
            version=help_data["version"],
            host=socket.gethostname(),
            utc_date=datetime.datetime.utcnow().isoformat(),
        )
    )


###################################################################
# Publish commands index
###################################################################


def publish_index(preview=False, check=False, test=None):
    api = init_api()
    commands = sorted(_guild_commands(test))
    assert commands
    version = commands[0][1]["version"]
    log.info("Generating command index")
    formatted_index = _format_command_index(commands, version)
    if preview:
        print(formatted_index)
        if not check:
            return
    post = _commands_index_post(api)
    if test:
        log.info("Skipping update of commands index post (%s) due to tests", post["id"])
        return
    if post["raw"].strip() == formatted_index:
        log.info("Command index post (%s) is up-to-date", post["id"])
        return
    if check:
        log.warning("Command index post (%s) is out-of-date", post["id"])
        return
    comment = _publish_index_comment(version)
    log.action("Updating command index post (%s)", post["id"])
    api.update_post(post["id"], formatted_index, comment)


def _format_command_index(commands, version):
    return COMMAND_INDEX_TEMPLATE.format(
        header=_format_command_index_header(),
        formatted_commands=_format_command_index_commands(commands),
        version=version,
    ).strip()


def _format_command_index_header():
    return "\n".join(
        [
            "Guild supports the commands listed below. You can get "
            "help for any of these commands by running:",
            "",
            "``` command",
            "guild <command> --help",
            "```" "",
        ]
    )


def _format_command_index_commands(commands):
    lines = ["| | |", "|-|-|"]
    lines.extend([_format_command_for_index(name, data) for name, data in commands])
    return "\n".join(lines)


def _format_command_for_index(name, data):
    return "|[%s](%s)|%s|" % (name, _command_permalink(name), _cmd_summary(data))


def _cmd_summary(data):
    return data["help"].split("\n")[0]


def _commands_index_post(api):
    log.info("Fetching commands index topic")
    try:
        topic = api._get("/commands")
    except DiscourseClientError:
        log.error(
            "Cannot find commands index topic for '/commands' permalink - "
            "create a valid permalink and run this command again"
        )
        raise SystemExit(1)
    else:
        if "post_stream" not in topic:
            log.error(
                "unexpected result for /commands permalink: %s", pprint.pformat(topic)
            )
            raise SystemExit(1)
        return api.post(topic["post_stream"]["posts"][0]["id"])


def _publish_index_comment(version):
    return (
        "Command index published for Guild AI version "
        "{version} from {host} on {utc_date}Z".format(
            version=version,
            host=socket.gethostname(),
            utc_date=datetime.datetime.utcnow().isoformat(),
        )
    )


###################################################################
# Check command permalinks
###################################################################


def check_command_permalinks(commands):
    api = init_api()
    commands = sorted(_guild_commands(commands))
    for cmd, _data in commands:
        _check_permalink(_command_permalink(cmd), cmd, api)


def _check_permalink(link, cmd, api):
    resp = requests.get("https://my.guild.ai/%s" % link, allow_redirects=False)
    if resp.status_code == 404:
        _no_permalink_error(link, cmd, api)
    elif resp.status_code != 301:
        log.error(
            "Unexpected non-redirect for %s: %s (%s)",
            link,
            resp.reason,
            resp.status_code,
        )
    else:
        _check_permalink_redirect(link, resp, cmd, api)


def _no_permalink_error(link, cmd, api):
    try:
        topic = api.topic(_command_help_slug(cmd))
    except DiscourseClientError:
        log.error("No permalink or broken link for %s", link)
    else:
        log.error(
            "No permalink for %s but topic %s '%s' by %s exists",
            link,
            topic["id"],
            topic["title"],
            topic["details"]["created_by"]["username"],
        )


def _command_help_slug(cmd):
    return "command-%s" % cmd.replace(" ", "-")


def _check_permalink_redirect(link, resp, cmd, api):
    location = resp.headers.get("location")
    assert location, (link, resp)
    m = re.match(r"https://my.guild.ai/t/[^/]+/([0-9]+)", location)
    if not m:
        log.error("Unexpected redirect host for %s: %s", link, location)
    topic_id = int(m.group(1))
    try:
        topic = api.topic(topic_id)
    except DiscourseClientError as e:
        log.error("Error getting topic %s from server: %s", topic_id, e)
    else:
        log.info(
            "Link %s redirects to topic %s '%s' by %s",
            link,
            topic["id"],
            topic["title"],
            topic["details"]["created_by"]["username"],
        )
        _check_topic_author(topic)
        _check_topic_slug(topic, cmd)
        _check_topic_title(topic, cmd)


def _check_topic_author(topic):
    expected = "guildai"
    author = topic["details"]["created_by"]["username"]
    if author != expected:
        log.error(
            "Unexpected author for topic %s: got '%s' expected '%s'",
            topic["id"],
            author,
            expected,
        )


def _check_topic_slug(topic, cmd):
    expected = _command_help_slug(cmd)
    if topic["slug"] != expected:
        log.error(
            "Unexpected slug for topic %s: got '%s' expected '%s'",
            topic["id"],
            topic["slug"],
            expected,
        )


def _check_topic_title(topic, cmd):
    expected = _command_help_title(cmd)
    if topic["title"] != expected:
        log.error(
            "Unexpected title for topic %s: got '%s' expected '%s'",
            topic["id"],
            topic["title"],
            expected,
        )
