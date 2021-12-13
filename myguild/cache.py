import errno
import hashlib
import os
import shutil

from .log_util import get_logger

from . import util

log = get_logger()

cache_dir = os.path.abspath(os.path.expanduser("~/.cache/myguild"))


def clear_all():
    assert os.path.isabs(cache_dir) and cache_dir.endswith(".cache/myguild"), cache_dir
    log.action("Clearing cache (%s)", cache_dir)
    shutil.rmtree(cache_dir)


def delete(key):
    path = _key_path(key)
    try:
        os.remove(path)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise


def read(key):
    path = _key_path(key)
    try:
        return open(path).read()
    except IOError as e:
        if e.errno != errno.ENOENT:
            raise
        return None


def _key_path(key):
    encoded_key = key.encode("utf-8")
    digest = hashlib.sha1(encoded_key).hexdigest()
    return os.path.join(cache_dir, digest)


def write(key, value):
    path = _key_path(key)
    util.ensure_dir(os.path.dirname(path))
    with open(path, "w") as f:
        f.write(value)


def get_info():
    return {
        "cache-dir": cache_dir,
        "cache-entries": len(os.listdir(cache_dir)),
    }
