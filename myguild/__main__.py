from __future__ import print_function

import logging

import click


@click.group()
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
    from . import sync_commands

    sync_commands.main()


if __name__ == "__main__":
    main(prog_name="my-guild")
