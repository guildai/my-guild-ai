from __future__ import print_function
from __future__ import absolute_import

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


@main.command("publish-commands", help=publish_commands_help)
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


@main.command("publish-commands-index", help=publish_commands_index_help)
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
# edit
###################################################################

edit_help = """
Edit a topic.

Specify a post link or ID.

A post is fetched from my.guild.ai and opened in the system editor
(defined by the EDITOR environent variable).

Make changes to the post and save as needed. Posts are saved to the
directory specified by '--save-dir', which defaults to the project
'posts'. To apply the changes, exit the editor, review the changed
present as a diff, and confirm that you want to publish the post.

Leave the post unchanged and exit to cancel the edit.

Use '--fetch' to fetch the post without editing.

Use '--publish' to publish a locally edited post.

Use '--fetch-all' to fetch all posts to the save dir.
"""


@main.command("edit", help=edit_help)
@click.argument("post", required=False)
@click.option("-f", "--fetch", is_flag=True, help="Fetch the post without editing it.")
@click.option(
    "-d",
    "--diff",
    is_flag=True,
    help="Show difference between local and published post",
)
@click.option("-p", "--publish", is_flag=True, help="Publish locally edited post.")
@click.option(
    "-m",
    "--comment",
    metavar="TEXT",
    help=(
        "Comment used when publishing posts. If omitted, editor "
        "is used to write comment."
    ),
)
@click.option(
    "-a",
    "--fetch-all",
    is_flag=True,
    help="Fetch all posts without editing. Uses docs index to enumerte posts.",
)
@click.option(
    "-d",
    "--save-dir",
    metavar="DIR",
    help=(
        "Location where posts are saved. Posts are saved as "
        "'<id>.md' in this directory."
    ),
)
@click.option(
    "index_path",
    "-i",
    "--index",
    metavar="FILE",
    help=(
        "Docs index used when fetching all posts (defaults "
        "to project 'docs-index.yml')"
    ),
)
@click.option("-E", "--edit-cmd", metavar="CMD", help="Command used to edit post.")
@click.option("-D", "--diff-cmd", metavar="CMD", help="Command used to diff changes.")
@click.option("--skip-diff", is_flag=True, help="Don't diff changes before publishing.")
@click.option("-y", "--yes", is_flag=True, help="Don't prompt before publishing.")
@click.option(
    "-f", "--force", is_flag=True, help="Publish even if published post is up-to-date."
)
def edit(
    post,
    fetch=False,
    diff=False,
    publish=False,
    comment=None,
    fetch_all=False,
    index_path=None,
    save_dir=None,
    edit_cmd=None,
    diff_cmd=None,
    skip_diff=False,
    yes=False,
    force=False,
):
    if fetch_all:
        if fetch:
            raise SystemExit("--fetch and --fetch-all cannot both be used")
        if post:
            raise SystemExit("--fetch-all cannot be used with POST")
        if publish:
            raise SystemExit("--fetch-all and --publish cannot both be used")
        if diff:
            raise SystemExit("--fetch-all and --diff cannot both be used")
        editlib.fetch_all(index_path=index_path, save_dir=save_dir)
    elif not post:
        raise SystemExit("missing required POST argument")
    else:
        if fetch:
            if publish:
                raise SystemExit("--fetch and --publish cannot both be used")
            if diff:
                raise SystemExit("--fetch and --diff cannot both be used")
            editlib.fetch_post(post, save_dir=save_dir)
        elif publish:
            editlib.publish(
                post,
                save_dir=save_dir,
                comment=comment,
                diff_cmd=diff_cmd,
                edit_cmd=edit_cmd,
                skip_diff=skip_diff,
                skip_prompt=yes,
                force=force,
            )
        elif diff:
            editlib.diff(
                post, save_dir=save_dir, diff_cmd=diff_cmd
            )
        else:
            editlib.edit(
                post,
                save_dir=save_dir,
                edit_cmd=edit_cmd,
                diff_cmd=diff_cmd,
                skip_diff=skip_diff,
                skip_prompt=yes,
            )


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
