import logging
import logging.config

import sys

_isatty = sys.stderr.isatty()

ACTION = 25


class Formatter(logging.Formatter):
    def format(self, record):
        return self._color(super(Formatter, self).format(record), record.levelno)

    @staticmethod
    def _color(s, level):
        if not _isatty:
            return s
        if level >= logging.ERROR:
            return "\033[31m%s\033[0m" % s
        elif level >= logging.WARNING:
            return "\033[35m%s\033[0m" % s
        elif level >= ACTION:
            return "\033[33m%s\033[0m" % s
        else:
            return s


class ConsoleLogHandler(logging.StreamHandler):
    def __init__(self):
        super(ConsoleLogHandler, self).__init__()
        self._action = Formatter("ACTION: [%(name)s] %(message)s")
        self._default = Formatter("%(levelname)s: [%(name)s] %(message)s")

    def format(self, record):
        if record.levelno == ACTION:
            return self._action.format(record)
        return self._default.format(record)


def init(debug=False):
    level = logging.DEBUG if debug else logging.INFO
    console_handler = {"class": "myguild.log_util.ConsoleLogHandler"}
    logging.config.dictConfig(
        {
            "version": 1,
            "handlers": {"console": console_handler},
            "root": {"level": level, "handlers": ["console"]},
            "disable_existing_loggers": False,
        }
    )

def getLogger():
    log = logging.getLogger()
    log.action = lambda *args: log.log(ACTION, *args)
    return log
