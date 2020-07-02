import errno
import logging
import os
import shlex
import subprocess
import textwrap
import time

import click

try:
    input = raw_input
except NameError:
    input = input

from .log_util import get_logger

log = get_logger()


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
    return os.getenv("DIFF") or "diff -u --color"


def ensure_deleted(path):
    try:
        os.remove(path)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise


def retry(desc, f, max_attempts=3, delay=3):
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
            log.error("Error running %s: %s", desc, e)
            log.info("Retrying %s after %0.1f seconds", desc, delay)
            time.sleep(delay)


def mtime(path):
    return os.stat(path).st_mtime


class SafeLoop(object):
    def __init__(self, limit_max=5, limit_interval=1.0, desc=None):
        self.limit_max = limit_max
        self.limit_interval = limit_interval
        self.desc = desc
        self._reset_count_time = None
        self._count = 0

    def check(self):
        self._update_count()
        if self._count > self.limit_max:
            raise SystemExit(
                "%s more than %i times within %0.1f seconds"
                % (self.desc or "loop ran", self.limit_max, self.limit_interval)
            )
        return True

    def __bool__(self):
        return self.check()

    def __nonzero__(self):
        return self.check()

    def incr(self):
        self._count += 1

    def _update_count(self):
        now = time.time()
        if self._reset_count_time is None or now > self._reset_count_time:
            self._reset_count_time = now + self.limit_interval
            self._count = 1


def notify_send(msg, urgency=None):
    cmd = ["notify-send", msg]
    if urgency:
        cmd.extend(["-u", urgency])
    _ = subprocess.check_output(cmd)
