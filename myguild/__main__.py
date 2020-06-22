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

Either '--all' must be specified or specific '--link-topic',
'--command', or '--topic-post' options must be specified otherwise the
command exits with an error.
"""


@myguild.command("clear-cache", help=clear_cache_help)
@click.option("--all", is_flag=True, help="Clears the entire cache.")
@click.option(
    "link_topics",
    "-l",
    "--link-topic",
    metavar="LINK",
    multiple=True,
    help="Clear cached link topic.",
)
@click.option(
    "commands",
    "-c",
    "--command",
    metavar="LINK",
    multiple=True,
    help="Clear cached command.",
)
@click.option(
    "topic_posts",
    "-t",
    "--topic-post",
    metavar="TOPIC",
    type=int,
    multiple=True,
    help="Clear topic post.",
)
@click.option(
    "--cache-info",
    is_flag=True,
    help="Show cache information and exit. Does not clear anything.",
)
def clear_cache(
    all=False, link_topics=None, commands=None, topic_posts=None, cache_info=False,
):
    if cache_info:
        _print_cache_info()
        raise SystemExit()
    if not (all or link_topics or commands or topic_posts):
        raise SystemExit("specify an option: --all, --link-topic, --command")
    if all:
        cache.clear_all()
    for link in link_topics or []:
        cache.delete(docs.link_topic_cache_key(link))
    for cmd in commands or []:
        cache.delete(command_help.cmd_cache_key(cmd))
    for topic_id in topic_posts or []:
        cache.delete(editlib.topic_post_cache_key(topic_id))


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


def _autocomplete_topics(ctx, args, incomplete):
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
"""


@myguild.command("edit", help=edit_help)
@click.argument("topic", type=int, required=False, autocompletion=_autocomplete_topics)
@click.option("-m", "--comment", help="Comment used when publishing.")
@click.option(
    "-n", "--no-comment", is_flag=True, help="Don't provide a comment when publishing."
)
@click.option("--skip-diff", is_flag=True, help="Skip diff when publishing.")
@click.option(
    "-y", "--yes", is_flag=True, help="Publish changes without asking for confirmation."
)
@click.option("--force", is_flag=True, help="Ignore conflicts.")
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
def edit(
    topic,
    fetch=False,
    fetch_docs=False,
    index_path=None,
    delete=False,
    comment=None,
    no_comment=False,
    skip_diff=False,
    yes=False,
    save_dir=None,
    force=False,
    diff_cmd=None,
    edit_cmd=None,
    stop_on_error=False,
):
    editlib.edit(
        topic,
        save_dir=save_dir,
        no_comment=no_comment,
        comment=comment,
        skip_diff=skip_diff,
        yes=yes,
        force=force,
        edit_cmd=edit_cmd,
        diff_cmd=diff_cmd,
    )

###################################################################
# fetch
###################################################################


fetch_help = """
Fetch a topic.
"""


@myguild.command("fetch", help=fetch_help)
@click.argument("topic", required=False, type=int, autocompletion=_autocomplete_topics)
@click.option("--all-docs", is_flag=True, help="Fetch all docs.")
@click.option(
    "index_path",
    "-i",
    "--index",
    metavar="FILE",
    help=(
        "Docs index used when fetching all docs (defaults to project 'docs-index.yml')"
    ),
)
@click.option("-f", "--force", is_flag=True, help="Ignore conflicts.")
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
def fetch(
    topic,
    all_docs=False,
    index_path=None,
    force=False,
    save_dir=None,
    stop_on_error=False,
):
    if all_docs:
        editlib.fetch_docs(
            save_dir=save_dir,
            index_path=index_path,
            force=force,
            stop_on_error=stop_on_error,
        )
    else:
        _require_topic(topic)
        editlib.fetch(topic, save_dir=save_dir, force=force)


###################################################################
# publish
###################################################################


publish_help = """
Publish a topic.

To publish all modified topics, use --all.
"""


@myguild.command("publish", help=edit_help)
@click.argument("topic", type=int, required=False, autocompletion=_autocomplete_topics)
@click.option("-a", "--all", is_flag=True, help="Publish all locally modified topics.")
@click.option("-m", "--comment", help="Comment used when publishing.")
@click.option(
    "-n", "--no-comment", is_flag=True, help="Don't provide a comment when publishing."
)
@click.option("--skip-diff", is_flag=True, help="Skip diff when publishing.")
@click.option(
    "-y", "--yes", is_flag=True, help="Publish changes without asking for confirmation."
)
@click.option("-f", "--force", is_flag=True, help="Ignore conflicts.")
@click.option(
    "--stop-on-error",
    is_flag=True,
    help="Stop when an error occurs. Applies only to --fetch-docs.",
)
@click.option("--diff-cmd", metavar="CMD", help="Command used to diff changes.")
@click.option("--edit-cmd", metavar="CMD", help="Command used to specify comment.")
@click.option(
    "--save-dir",
    metavar="DIR",
    help=(
        "Location where topics are saved. Topics are saved as "
        "'<id>.md' in this directory."
    ),
)
def publish(
    topic,
    all=False,
    comment=None,
    no_comment=False,
    skip_diff=False,
    yes=False,
    save_dir=None,
    force=False,
    stop_on_error=False,
    diff_cmd=None,
    edit_cmd=None,
):
    if all:
        editlib.publish_all(
            comment=comment,
            no_comment=no_comment,
            skip_diff=skip_diff,
            yes=yes,
            force=force,
            stop_on_error=stop_on_error,
            save_dir=save_dir,
            edit_cmd=edit_cmd,
            diff_cmd=diff_cmd,
        )
    else:
        _require_topic(topic)
        editlib.publish(
            topic,
            comment=comment,
            no_comment=no_comment,
            skip_diff=skip_diff,
            yes=yes,
            force=force,
            save_dir=save_dir,
            edit_cmd=edit_cmd,
            diff_cmd=diff_cmd,
        )


def _require_topic(topic):
    if not topic:
        raise SystemExit("TOPIC is required for this operation.")


###################################################################
# delete
###################################################################


delete_help = """
Delete a local topic.

Note this does not delete the server topic.
"""


@myguild.command("delete", help=delete_help)
@click.argument("topic", type=int, autocompletion=_autocomplete_topics)
@click.option(
    "-y", "--yes", is_flag=True, help="Publish changes without asking for confirmation."
)
@click.option("-f", "--force", is_flag=True, help="Ignore conflicts.")
@click.option(
    "--save-dir",
    metavar="DIR",
    help=(
        "Location where topics are saved. Topics are saved as "
        "'<id>.md' in this directory."
    ),
)
def delete(topic, yes=False, save_dir=None, force=False):
    editlib.delete(topic, save_dir=save_dir, yes=yes, force=force)


###################################################################
# diff
###################################################################


diff_help = """
Diff changes to topics.
"""


@myguild.command("diff", help=diff_help)
@click.argument("topic", type=int, required=False, autocompletion=_autocomplete_topics)
@click.option(
    "-l", "--latest", is_flag=True, help="Compare local topic to latest on server."
)
@click.option(
    "--save-dir",
    metavar="DIR",
    help=(
        "Location where topics are saved. Topics are saved as "
        "'<id>.md' in this directory."
    ),
)
@click.option(
    "-D", "--diff-cmd", metavar="CMD", help="Command used when diffing index."
)
def diff(
    topic, latest=False, save_dir=None, diff_cmd=None,
):
    if not topic:
        if latest:
            editlib.diff_latest_all(save_dir=save_dir, diff_cmd=diff_cmd)
        else:
            editlib.diff_base_all(save_dir=save_dir, diff_cmd=diff_cmd)
    else:
        if latest:
            editlib.diff_latest(topic, save_dir=save_dir, diff_cmd=diff_cmd)
        else:
            editlib.diff_base(topic, save_dir=save_dir, diff_cmd=diff_cmd)


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
