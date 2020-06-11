from __future__ import print_function
from __future__ import absolute_import

import sys

import click

from . import log_util
from . import command_help

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


@main.command("publish-index", help="Publish command index.")
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
def publish_index(**opts):
    command_help.publish_index(**opts)


@main.command("check-command-permalinks")
@click.argument("commands", metavar="[COMMAND]...", nargs=-1)
def check_command_permalinks(commands):
    command_help.check_command_permalinks(commands)


if __name__ == "__main__":
    try:
        # pylint: disable=unexpected-keyword-arg
        main(prog_name="myguild")
    except SystemExit as e:
        if e.args[0] != 0:
            sys.stderr.write("error: %s\n" % e.message)
            sys.exit(1)
