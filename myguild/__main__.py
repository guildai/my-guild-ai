from __future__ import print_function
from __future__ import absolute_import

import os
import sys

import click
import yaml

from . import cache
from . import command_help
from . import docs
from . import edit as editlib
from . import log_util
from . import security


###################################################################
# myguild base
###################################################################

base_help = """
Support for managing my.guild.ai.

Commands that access my.guild.ai (publishing, etc.) require the
environment variable MY_GUILD_API_KEY. If this variable is not set,
the commands exits with an error.

Refer to help for the commands below for more information.
"""


@click.group(help=base_help)
@click.option("--debug", is_flag=True, help="Enable debug logging")
def myguild(debug=False):
    log_util.init(debug)


###################################################################
# publish-index
###################################################################

publish_docs_index_help = """
Publish docs index.

Generates a Markdown formatted document index and publishes it to the
topic resolved by the '/docs' permalink. If this link does not resolve
to a topic, the command exits with an error.
"""


@myguild.command("publish-docs-index", help=publish_docs_index_help)
@click.option("-p", "--preview", is_flag=True, help="Preview generated index.")
@click.option("-c", "--check", is_flag=True, help="Check published index status.")
@click.option(
    "-d", "--diff", is_flag=True, help="Show a diff of generated and published index."
)
@click.option(
    "check_links",
    "-l",
    "--check-link",
    metavar="LINK",
    multiple=True,
    help="Check a docs link.",
)
@click.option("-f", "--force", is_flag=True, help="Continue even when errors occur.")
@click.option(
    "index_path",
    "-i",
    "--index",
    metavar="FILE",
    help="Docs index used to publish (defaults to project 'docs-index.yml')",
)
@click.option(
    "-D", "--diff-cmd", metavar="CMD", help="Command used when diffing index."
)
def publish_docs_index(**opts):
    docs.publish_index(**opts)


###################################################################
# publish-commands
###################################################################

publish_commands_help = """
Publish commands.

By default publishes all commands. To publish specific commands,
specify one or more arguments for COMMAND.
"""


@myguild.command("publish-commands", help=publish_commands_help)
@click.argument("commands", metavar="[COMMAND]...", nargs=-1)
@click.option("-p", "--preview", is_flag=True, help="Preview published topics.")
@click.option("-c", "--check", is_flag=True, help="Check published topics.")
def publish_commands(commands, **opts):
    command_help.publish_commands(commands, **opts)


###################################################################
# publish-index
###################################################################

publish_commands_index_help = """
Publish command index.

Generates a Markdown formatted document containing links to all Guild
commands and publishes it to the topic resolved by the '/commands'
permalink. If this link does not resolve to a topic, the command exits
with an error.
"""


@myguild.command("publish-commands-index", help=publish_commands_index_help)
@click.option("-p", "--preview", is_flag=True, help="Preview generated index.")
@click.option("-c", "--check", is_flag=True, help="Check published index status.")
@click.option(
    "-t",
    "--test",
    multiple=True,
    metavar="COMMAND",
    help=(
        "Test index using COMMAND. Implies --preview. "
        "Maybe be specified multiple times."
    ),
)
def publish_commands_index(**opts):
    command_help.publish_index(**opts)


###################################################################
# check-command-permalinks
###################################################################

check_command_permalinks_help = """
Verify that each Guild command has a valid permalink.

Valid permalinks are in the format `/commands/<command-slug>` and must
resolve to a topic with a title matching 'Command: <command>' that is
owner by 'guildai'.

Guild logs error message for any commands that don't have valid
permalinks.
"""


@myguild.command("check-command-permalinks", help=check_command_permalinks_help)
@click.argument("commands", metavar="[COMMAND]...", nargs=-1)
def check_command_permalinks(commands):
    command_help.check_command_permalinks(commands)


###################################################################
# clear-cache
###################################################################

clear_cache_help = """
Clears the program cache.

Use this command to ensure that command help info is refreshed on
subsequent commands.

Either '--all' must be specified or specific '--link' or '--command'
options must be specified otherwise the command exits with an error.
"""


@myguild.command("clear-cache", help=clear_cache_help)
@click.option("--all", is_flag=True, help="Clears the entire cache.")
@click.option(
    "links", "-l", "--link", metavar="LINK", multiple=True, help="Clear cached link."
)
@click.option(
    "commands",
    "-c",
    "--commands",
    metavar="LINK",
    multiple=True,
    help="Clear cached command.",
)
@click.option(
    "--cache-info",
    is_flag=True,
    help="Show cache information and exit. Does not clear anything.",
)
def clear_cache(all=False, links=None, commands=None, cache_info=False):
    if cache_info:
        _print_cache_info()
        raise SystemExit()
    if not (all or links or commands):
        raise SystemExit("specify an option: --all, --link, --command")
    if all:
        if links:
            raise SystemExit("--link cannot be used with --all")
        if commands:
            raise SystemExit("--command cannot be used with --all")
        cache.clear_all()
    for link in links or []:
        cache.delete(docs._link_cache_key(link))
    for cmd in commands or []:
        cache.delete(command_help._cmd_cache_key(cmd))


def _print_cache_info():
    info = cache.get_info()
    print(yaml.safe_dump(info, default_flow_style=False, indent=2).strip())


###################################################################
# audit
###################################################################

audit_help = """
Show audit information.
"""


@myguild.command("audit", help=audit_help)
def audit():
    security.audit()


###################################################################
# edit
###################################################################


def _edit_topics(ctx, args, incomplete):
    if "--help" in args:
        return []
    params = ctx.params
    save_dir = params.get("save_dir") or editlib.default_save_dir()
    topics = [name[:-3] for name in os.listdir(save_dir) if name.endswith(".md")]
    return [id for id in sorted(topics, key=_int_sort_key) if id.startswith(incomplete)]


def _int_sort_key(s):
    try:
        return int(s)
    except ValueError:
        return 0


edit_help = """
Edit a topic.

TOPIC is required unless --fetch-docs is used.
"""


@myguild.command("edit", help=edit_help)
@click.argument("topic", type=int, required=False, autocompletion=_edit_topics)
@click.option(
    "-f", "--fetch", is_flag=True, help="Fetch the latest topic without editing."
)
@click.option("--fetch-docs", is_flag=True, help="Fetch all docs in docs index.")
@click.option(
    "index_path",
    "-i",
    "--index",
    metavar="FILE",
    help=(
        "Docs index used when fetching docs (defaults to " "project 'docs-index.yml')"
    ),
)
@click.option(
    "-p",
    "--publish",
    is_flag=True,
    help="Publish a locally edited topic to my.guild.ai.",
)
@click.option("--delete", is_flag=True, help="Delete local files associatd with topic.")
@click.option("-m", "--comment", help="Comment used when publishing.")
@click.option("--skip-diff", is_flag=True, help="Skip diff when publishing.")
@click.option(
    "--yes", is_flag=True, help="Publish changes without asking for confirmation."
)
@click.option("--force", is_flag=True, help="Ignore conflicts.")
@click.option("--diff-base", is_flag=True, help="Compare topic to its base version.")
@click.option(
    "--diff-latest", is_flag=True, help="Compare topic to the latest published version."
)
@click.option("--diff-cmd", metavar="CMD", help="Command used to diff changes.")
@click.option("--edit-cmd", metavar="CMD", help="Command used to edit topic.")
@click.option(
    "--save-dir",
    metavar="DIR",
    help=(
        "Location where topics are saved. Topics are saved as "
        "'<id>.md' in this directory."
    ),
)
@click.option(
    "--stop-on-error",
    is_flag=True,
    help="Stop when an error occurs. Applies only to --fetch-docs.",
)
def edit(
    topic,
    fetch=False,
    fetch_docs=False,
    index_path=None,
    delete=False,
    publish=False,
    comment=None,
    skip_diff=False,
    yes=False,
    save_dir=None,
    force=False,
    diff_base=False,
    diff_latest=False,
    diff_cmd=None,
    edit_cmd=None,
    stop_on_error=False,
):
    if fetch_docs:
        editlib.fetch_docs(
            save_dir=save_dir,
            index_path=index_path,
            force=force,
            stop_on_error=stop_on_error,
        )
    else:
        if not topic:
            raise SystemExit(
                "TOPIC is required for this operation.\nTry 'my-guild "
                "--help' for details."
            )
        if fetch:
            editlib.fetch(topic, save_dir=save_dir, force=force)
        elif delete:
            editlib.delete(topic, save_dir=save_dir, yes=yes, force=force)
        elif publish:
            editlib.publish(
                topic,
                save_dir=save_dir,
                comment=comment,
                skip_diff=skip_diff,
                force=force,
                edit_cmd=edit_cmd,
            )
        elif diff_base:
            editlib.diff_base(topic, save_dir=save_dir, diff_cmd=diff_cmd)
        elif diff_latest:
            editlib.diff_latest(topic, save_dir=save_dir, diff_cmd=diff_cmd)
        else:
            editlib.edit(
                topic,
                save_dir=save_dir,
                comment=comment,
                skip_diff=skip_diff,
                yes=yes,
                force=force,
                edit_cmd=edit_cmd,
                diff_cmd=diff_cmd,
            )


###################################################################
# main
###################################################################


def main():
    try:
        # pylint: disable=unexpected-keyword-arg
        myguild(prog_name="my-guild")
    except SystemExit as e:
        if e.args and e.args[0] != 0:
            if isinstance(e.args[0], int):
                sys.exit(e.args[0])
            else:
                log = log_util.get_logger()
                log.error(*e.args)
                sys.exit(1)


if __name__ == "__main__":
    main()
