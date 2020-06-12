from __future__ import print_function
from __future__ import absolute_import

import sys

import click
import yaml

from . import cache
from . import command_help
from . import docs
from . import log_util
from . import security


###################################################################
# Main
###################################################################

main_help = """
Support for managing my.guild.ai.

Commands that access my.guild.ai (publishing, etc.) require the
environment variable MY_GUILD_API_KEY. If this variable is not set,
the commands exits with an error.

Refer to help for the commands below for more information.
"""


@click.group(help=main_help)
@click.option("--debug", is_flag=True, help="Enable debug logging")
def main(debug=False):
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


@main.command("publish-docs-index", help=publish_docs_index_help)
@click.option("--preview", is_flag=True, help="Preview generated index.")
@click.option("--check", is_flag=True, help="Check published index status.")
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


@main.command("publish-commands", help=publish_commands_help)
@click.argument("commands", metavar="[COMMAND]...", nargs=-1)
@click.option("--check", is_flag=True, help="Check published topics.")
@click.option("--preview", is_flag=True, help="Preview published topics.")
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


@main.command("publish-commands-index", help=publish_commands_index_help)
@click.option("--preview", is_flag=True, help="Preview generated index.")
@click.option("--check", is_flag=True, help="Check published index status.")
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


@main.command("check-command-permalinks", help=check_command_permalinks_help)
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


@main.command("clear-cache", help=clear_cache_help)
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

@main.command("audit", help=audit_help)
def audit():
    security.audit()


###################################################################
# __main__
###################################################################


def _main():
    try:
        # pylint: disable=unexpected-keyword-arg
        main(prog_name="my-guild")
    except SystemExit as e:
        if e.args and e.args[0] != 0:
            if isinstance(e.args[0], int):
                sys.exit(e.args[0])
            else:
                sys.stderr.write("error: %s\n" % e.message)
                sys.exit(1)


if __name__ == "__main__":
    _main()
