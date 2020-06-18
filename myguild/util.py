import errno
import os
import shlex
import subprocess
import textwrap

import click

try:
    input = raw_input
except NameError:
    input = input


def ensure_dir(dir):
    try:
        os.makedirs(dir)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


def confirm(prompt, default=False):
    click.echo(prompt, nl=False, err=True)
    click.echo(" %s " % ("(Y/n)" if default else "(y/N)"), nl=False, err=True)
    c = input()
    yes_vals = ["y", "yes"]
    if default:
        yes_vals.append("")
    return c.lower().strip() in yes_vals


def edit_msg(prompt, editor=None):
    s = click.edit(_edit_msg_text(prompt), editor)
    return s and _strip_comments(s).strip()


def _edit_msg_text(prompt):
    full_prompt = (
        "%s Lines starting with '#' ignored, and an empty message cancels the action."
        % prompt
    )
    prompt_lines = [""] + ["# %s" % s for s in textwrap.wrap(full_prompt)]
    return "\n".join(prompt_lines)


def _strip_comments(s):
    return "\n".join([s for s in s.split("\n") if s[:1] != "#"])


def edit(path, editor=None):
    return click.edit(filename=path, editor=editor)


def diff_files(path1, path2, diff_cmd=None):
    diff_cmd = shlex.split(diff_cmd or default_diff_cmd()) + [path1, path2]
    subprocess.call(diff_cmd)


def default_diff_cmd():
    return os.getenv("DIFF") or "diff -u"


def ensure_deleted(path):
    try:
        os.remove(path)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise
