import datetime
import json
import logging
import os
import re
import socket
import subprocess

from .api import init as init_api
from .api import DiscourseClientError

log = logging.getLogger()

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


def sync_commands():
    commands = sorted(_guild_commands())
    for name, data in commands:
        log.info("Syncing %s", name)


def _guild_commands():
    cmds = []
    _acc_guild_commands("", cmds)
    return cmds


def _acc_guild_commands(base_cmd, acc):
    (help_data, subcommands) = _cmd_help(base_cmd)
    acc.append((base_cmd, help_data))
    for cmd in subcommands:
        _acc_guild_commands(cmd, acc)


def _cmd_help(cmd):
    log.info("Getting help info for %s", cmd)
    help_data = _cmd_help_data(cmd)
    log.debug("Help data for %s: %r", cmd, help_data)
    subcommands = _subcommands_for_help_data(help_data, cmd)
    return help_data, subcommands


def _cmd_help_data(cmd):
    help_cmd = "guild %s --help" % cmd
    help_env = dict(os.environ)
    help_env["GUILD_HELP_JSON"] = "1"
    out = subprocess.check_output(help_cmd, env=help_env, shell=True)
    return json.loads(out)


def _subcommands_for_help_data(help_data, base_cmd):
    return [_join_cmd(base_cmd, cmd["term"]) for cmd in help_data.get("commands", [])]


def _join_cmd(base_cmd, cmd_term):
    return "%s %s" % (base_cmd, _strip_aliases(cmd_term))


def _strip_aliases(cmd_term):
    return cmd_term.split(",", 1)[0].strip()


def publish_command(cmd, preview=False):
    api = init_api()
    log.info("Generating help topic")
    help_data = _cmd_help_data(cmd)
    formatted_help = _format_command_help_post(help_data)
    if preview:
        print(formatted_help)
    post = _get_command_topic_post(cmd, api)
    if post["raw"] == formatted_help:
        log.info("Help topic post (%s) unchanged, skipping", post["id"])
        return
    if preview:
        log.info("Help topic post (%s) is out-of-date and will be updated", post["id"])
        return
    log.info("Updating help topic post (%s)", post["id"])
    comment = _publish_command_comment(help_data)
    api.update_post(post["id"], formatted_help, comment)


def _get_command_topic_post(cmd, api):
    log.info("Getting current help topic from server")
    try:
        topic = api.topic(_command_slug(cmd))
    except DiscourseClientError as e:
        if log.getEffectiveLevel() <= logging.DEBUG:
            log.exception("topic for %s", cmd)
        raise SystemExit(
            "a topic for command '%s' does not exist\n"
            "Create a topic 'Command: %s' and run this command again."
        )
    else:
        return api.post(topic["post_stream"]["posts"][0]["id"])


def _command_slug(cmd):
    return "command-%s" % cmd.replace(" ", "-")


def _format_command_help_post(help_data):
    return COMMAND_HELP_POST_TEMPLATE.format(
        formatted_help=_format_command_help(help_data),
        formatted_options=_format_command_help_options(help_data),
        formatted_subcommands=_format_command_subcommands(help_data),
        **help_data
    ).rstrip()


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


def _format_command_subcommands(help_data):
    commands = help_data.get("commands")
    if not commands:
        return ""
    lines = [
        "",
        "",
        "### Subcommands",
        "",
        "" "| | |",
        "|-|-|",
    ]
    lines.extend([_format_subcommand(cmd) for cmd in commands])
    return "\n".join(lines)


def _format_subcommand(cmd):
    return "|[`%s`](%s)|%s|" % (cmd["term"], _cmd_url_path(cmd["term"]), cmd["help"])


def _cmd_url_path(cmd):
    return "/commands/%s" % _command_slug(_strip_aliases(cmd))


def _publish_command_comment(help_data):
    return (
        "Command help published for Guild AI version "
        "{version} from {host} on {utc_date}Z".format(
            version=help_data["version"],
            host=socket.gethostname(),
            utc_date=datetime.datetime.utcnow().isoformat(),
        )
    )
