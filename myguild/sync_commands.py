import json
import logging
import os
import subprocess

log = logging.getLogger()


def main():
    commands = sorted(_guild_commands())
    for name, data in commands:
        log.info("Syncing %s", name)


def _guild_commands():
    cmds = []
    _acc_guild_commands("", cmds)
    return cmds

def _acc_guild_commands(base_cmd, acc):
    (help_data, subcommands) = _cmd_help(base_cmd)
    acc.append((base_cmd, help_data))
    for cmd in subcommands:
        _acc_guild_commands(cmd, acc)


def _cmd_help(cmd):
    log.info("Getting help info for %s", cmd)
    help_data = _cmd_help_data(cmd)
    log.debug("Help data for %s: %r", cmd, help_data)
    subcommands = _subcommands_for_help_data(help_data, cmd)
    return help_data, subcommands


def _cmd_help_data(cmd):
    help_cmd = "guild %s --help" % cmd
    help_env = dict(os.environ)
    help_env["GUILD_HELP_JSON"] = "1"
    out = subprocess.check_output(help_cmd, env=help_env, shell=True)
    return json.loads(out)


def _subcommands_for_help_data(help_data, base_cmd):
    return [_join_cmd(base_cmd, cmd["term"]) for cmd in help_data.get("commands", [])]


def _join_cmd(base_cmd, cmd_term):
    return "%s %s" % (base_cmd, _strip_aliases(cmd_term))


def _strip_aliases(cmd_term):
    return cmd_term.split(",", 1)[0].strip()
