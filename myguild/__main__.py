from __future__ import print_function
from __future__ import absolute_import

import logging
import sys

import click

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
def main(debug):
    _init_logging(debug)


def _init_logging(debug):
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(levelname)s: [%(name)s] %(message)s",
    )


@main.command("sync-commands", help="Synchronize command help.")
def sync_commands():
    command_help.sync_commands()


@main.command("publish-command", help="Publish command help to a topic.")
@click.argument("command")
@click.option("--preview", is_flag=True, help="Show preview of generated help topic.")
def publish_command(command, **opts):
    command_help.publish_command(command, **opts)


if __name__ == "__main__":
    try:
        main(prog_name="my-guild")
    except SystemExit as e:
        if e.args[0] != 0:
            sys.stderr.write("error: %s\n" % e.message)
            sys.exit(1)
