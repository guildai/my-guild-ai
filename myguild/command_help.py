import datetime
import json
import logging
import os
import re
import socket
import subprocess
import time

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
            log.error("error running %s: %s", desc, e)
            log.info("retrying %s after %0.1f seconds", desc, delay)
            time.sleep(delay)


def sync_commands(commands, preview=False):
    api = init_api()
    commands = sorted(_guild_commands(commands))
    for name, data in commands:
        _sync_command(name, data, preview, api)


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
            log.warning("no such command '%s'", cmd)
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
    if cmd:
        log.info("Getting help info for '%s'", cmd)
    else:
        log.info("Getting help info for guild base command")
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
        log.debug("error reading help for '%s': %s", cmd, err)
        raise NoSuchCommand(cmd)
    return json.loads(out)


def _subcommands_for_help_data(help_data, base_cmd):
    return [_join_cmd(base_cmd, cmd["term"]) for cmd in help_data.get("commands", [])]


def _join_cmd(base_cmd, cmd_term):
    cmd = _strip_aliases(cmd_term)
    if not base_cmd:
        return cmd
    return "%s %s" % (base_cmd, cmd)


def _strip_aliases(cmd_term):
    return cmd_term.split(",", 1)[0].strip()


def _sync_command(cmd, data, preview, api):
    _retry(
        "sync command '%s'" % cmd,
        lambda: _sync_command_impl(cmd, data, preview, api),
        max_attempts=3,
        delay=5,
    )


def _sync_command_impl(cmd, data, preview, api):
    try:
        post = _get_command_topic_post(cmd, api)
    except DiscourseClientError:
        if preview:
            log.info("Topic for command '%s' does not exist - will create", cmd)
            return
        _create_command_post(cmd, data, api)
    else:
        _publish_command(cmd, data, post, api, print_topic=False, test_only=preview)


def _create_command_post(cmd, data, api, preview=False):
    category = _commands_category(api)
    content = _format_command_help_post(data)
    if preview:
        print(content)
        return
    log.info("Creating help topic post for '%s'", cmd)
    api.create_post(content, category, title="Command: %s" % cmd)


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


def publish_command(cmd, preview=False):
    api = init_api()
    log.info("Generating help topic for '%s'", cmd)
    try:
        help_data = _get_cmd_help_data(cmd)
    except NoSuchCommand:
        raise SystemExit("command '%s' does not exist" % cmd)
    else:
        try:
            post = _get_command_topic_post(cmd, api)
        except DiscourseClientError:
            _create_command_post(cmd, help_data, api, preview)
        else:
            _publish_command(
                cmd, help_data, post, api, print_topic=preview, test_only=preview
            )


def _get_command_topic_post(cmd, api):
    assert cmd
    log.info("Getting current help topic for '%s' from server", cmd)
    topic = api.topic(_command_slug(cmd))
    return api.post(topic["post_stream"]["posts"][0]["id"])


def _command_slug(cmd):
    return "command-%s" % cmd.replace(" ", "-")


def _publish_command(cmd, help_data, post, api, print_topic, test_only):
    formatted_help = _format_command_help_post(cmd, help_data)
    if print_topic:
        print(formatted_help)
    if post["raw"].strip() == formatted_help:
        log.info("Help topic post for '%s' (%s) unchanged", cmd, post["id"])
        return
    if test_only:
        log.info("Help topic post (%s) is out-of-date and will be updated", post["id"])
        return
    comment = _publish_command_comment(help_data)
    log.info("Updating help topic post (%s)", post["id"])
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
    return "|[`%s`](%s)|%s|" % (
        subcmd["term"],
        _cmd_url_path(_join_cmd(cmd, subcmd["term"])),
        subcmd["help"],
    )


def _cmd_url_path(cmd):
    # TODO: This is broken - we need a reliable path for these
    # commands.
    return "/t/%s" % _command_slug(_strip_aliases(cmd))


def _apply_command_refs(s):
    parts = re.split(r"(``guild .+ --help``)", s)
    return "".join([_try_command_ref(part) or part for part in parts])


def _try_command_ref(s):
    m = re.match(r"``guild (.+) --help``", s)
    if m:
        return "[`guild %s`](/t/%s)" % (m.group(1), _command_slug(m.group(1)))
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


def publish_index(preview=False, test=None):
    api = init_api()
    commands = sorted(_guild_commands(test))
    assert commands
    version = commands[0][1]["version"]
    log.info("Generating command index")
    formatted_index = _format_command_index(commands, version)
    if preview:
        print(formatted_index)
        return
    post = _commands_index_post(api)
    if test:
        log.info("Skipping update of commands index post (%s) due to tests", post["id"])
        return
    if post["raw"].strip() == formatted_index:
        log.info("Command index post (%s) is up-to-date", post["id"])
        return
    comment = _publish_index_comment(version)
    log.info("Updating command index post (%s)", post["id"])
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
    return "|[`%s`](/t/%s)|%s|" % (name, _command_slug(name), _cmd_summary(data))


def _cmd_summary(data):
    return data["help"].split("\n")[0]


def _commands_index_post(api):
    log.info("Getting commands index topic")
    try:
        topic = api.topic("guild-commands")
    except DiscourseClientError:
        raise SystemExit(
            "cannot find commands index 'guild-commands' topic - "
            "create this topic and run this command again"
        )
    else:
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
