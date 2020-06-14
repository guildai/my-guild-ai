import glob
import hashlib
import os

from . import docs
from . import util

from .api import init as init_api
from .api import DiscourseClientError
from .log_util import get_logger

log = get_logger()


class LocalPostChanged(SystemExit):
    def __init__(self, post, local_path):
        super(LocalPostChanged, self).__init__(1)
        self.post = post
        self.local_path = local_path


###################################################################
# Edit
###################################################################


def edit(post_link_or_id, save_dir=None, edit_cmd=None, force=False):
    post, path = _ensure_post(post_link_or_id, save_dir, force)
    log.info("Editing %s" % os.path.relpath(path))
    util.edit(path, edit_cmd)


def _ensure_post(post_link_or_id, save_dir, force):
    try:
        return fetch_post(post_link_or_id, save_dir, force)
    except LocalPostChanged as e:
        return e.post, e.local_path


###################################################################
# Publish
###################################################################


def publish(
    post_link_or_id,
    save_dir=None,
    comment=None,
    diff_cmd=None,
    edit_cmd=None,
    skip_diff=False,
    skip_prompt=False,
    force=False,
):
    api = init_api()
    post = _get_post(post_link_or_id, api)
    local_post = _local_post(post, save_dir)
    post_raw = _post_raw(post)
    if not force and local_post == post_raw:
        log.info("Post %i is up-to-date", post["id"])
        raise SystemExit(0)
    if not skip_diff:
        _diff_post(post, local_post, diff_cmd)
    if not skip_prompt:
        _verify_publish(post)
    _publish_post(post, local_post, comment, edit_cmd, api)

def _post_raw(post):
    # Discourse strips trailing LF so we add back support compare to
    # local posts.
    return post["raw"] + "\n"

def _local_post(post, save_dir):
    save_dir = save_dir or default_save_dir()
    save_path = _save_path_for_post(post, save_dir)
    if not os.path.exists(save_path):
        raise SystemExit("Cannot find local post '%s'" % save_path)
    return open(save_path).read()


def default_save_dir():
    project_dir = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(project_dir, "posts")


def _save_path_for_post(post, save_dir):
    return os.path.join(save_dir, "%s.md" % post["id"])


def _diff_post(post, local_post, diff_cmd):
    docs.diff_post(post["id"], _post_raw(post), local_post, diff_cmd)


def _verify_publish(post):
    if not util.confirm("Publish post %i?" % post["id"], True):
        raise SystemExit(1)


def _publish_post(post, local_post, comment, edit_cmd, api):
    comment = comment or _get_comment(edit_cmd)
    log.action("Publishing %s", post["id"])
    api.update_post(post["id"], local_post, comment)


def _get_comment(editor):
    s = util.edit_msg("Enter a comment your changes.", editor)
    if not s:
        log.warning("Aborting publish due to empty comment.")
        raise SystemExit(1)
    return s


###################################################################
# Diff
###################################################################


def diff(post_link_or_id, save_dir=None, diff_cmd=None):
    api = init_api()
    post = _get_post(post_link_or_id, api)
    local_post = _local_post(post, save_dir)
    if local_post == _post_raw(post):
        log.info("Post %i is up-to-date", post["id"])
        raise SystemExit(0)
    _diff_post(post, local_post, diff_cmd)


###################################################################
# Fetch
###################################################################


def fetch_post(post_link_or_id, save_dir=None, force=False):
    api = init_api()
    save_dir = save_dir or default_save_dir()
    post = _get_post(post_link_or_id, api)
    save_path = _save_path_for_post(post, save_dir)
    sha_path = _sha_path_for_post(post, save_dir)
    if not force and _local_post_changed(save_path, sha_path):
        log.warning(
            "Local post %s changed since last fetch, skipping (use force to override)",
            post["id"],
        )
        raise LocalPostChanged(post["id"], save_path)
    post_raw = _post_raw(post)
    if not force and os.path.exists(save_path):
        if post_raw == open(save_path).read():
            log.info("Post %s is up-to-date", post["id"])
            return post, save_path
    post_sha = hashlib.sha1(post_raw).hexdigest()
    log.action("Saving fetched post %s to %s", post["id"], os.path.relpath(save_path))
    util.ensure_dir(save_dir)
    with open(sha_path, "w") as f:
        f.write(post_sha)
    with open(save_path, "w") as f:
        f.write(post_raw)
    return post, save_path


def _sha_path_for_post(post, save_dir):
    return os.path.join(save_dir, "%s.sha" % post["id"])


def _local_post_changed(post_path, sha_path):
    if not os.path.exists(post_path) or not os.path.exists(sha_path):
        return False
    current_sha = hashlib.sha1(open(post_path).read()).hexdigest()
    base_sha = open(sha_path).read()
    return current_sha != base_sha


def _get_post(link_or_id, api):
    try:
        post_id = int(link_or_id)
    except ValueError:
        link = link_or_id
        log.info("Fetching post for '%s'", link)
        return _post_for_link(link, api)
    else:
        log.info("Fetching post %i", post_id)
        return _post_for_id(post_id, api)


def _post_for_id(post_id, api):
    try:
        return api.post(post_id)
    except DiscourseClientError:
        raise SystemExit("No such post: %i" % post_id)


def _post_for_link(link, api):
    try:
        topic = api._get(_ensure_abs_link(link))
    except DiscourseClientError:
        raise SystemExit("Cannot find topic for '%s'" % link)
    else:
        post_id = topic["post_stream"]["posts"][0]["id"]
        return _post_for_id(post_id, api)


def _ensure_abs_link(link):
    return link if link[:1] == "/" else "/" + link


###################################################################
# Fetch all
###################################################################


def fetch_all(index_path=None, save_dir=None, force=False):
    index_path = index_path or docs.default_index_path()
    for link in docs.iter_index_links(index_path):
        try:
            fetch_post(link, save_dir=save_dir, force=force)
        except LocalPostChanged as e:
            assert not force


###################################################################
# Log changed
###################################################################

def log_changed(save_dir=None):
    save_dir = save_dir or default_save_dir()
    for post_path in glob.glob(os.path.join(save_dir, "*.md")):
        sha_path = post_path[:-3] + ".sha"
        if not os.path.exists(sha_path):
            log.warning("Post %s missing sha", os.path.relpath(sha_path))
        base_sha = open(sha_path).read()
        cur_sha = hashlib.sha1(open(post_path).read()).hexdigest()
        if base_sha != cur_sha:
            log.info(os.path.relpath(post_path))
