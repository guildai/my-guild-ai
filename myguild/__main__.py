from __future__ import print_function
from __future__ import absolute_import

import sys

import click

from . import cache
from . import command_help
from . import log_util


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

publish_index_help = """
Publish command index.

Generates a Markdown formatted document containing links to all Guild
commands and publishes it to the topic with the slug
`guild-commands`. If this topic does not al
"""


@main.command("publish-commands-index", help=publish_index_help)
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
"""


@main.command("clear-cache", help=clear_cache_help)
def clear_cache():
    cache.clear()


###################################################################
# __main__
###################################################################


if __name__ == "__main__":
    try:
        # pylint: disable=unexpected-keyword-arg
        main(prog_name="myguild")
    except SystemExit as e:
        if e.args[0] != 0:
            sys.stderr.write("error: %s\n" % e.message)
            sys.exit(1)
