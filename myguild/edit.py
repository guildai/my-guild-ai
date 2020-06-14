import os

from . import docs
from . import util

from .api import init as init_api
from .api import DiscourseClientError
from .log_util import get_logger

log = get_logger()


def edit(
    post_link_or_id,
    save_dir=None,
    edit_cmd=None,
    diff_cmd=None,
    skip_diff=False,
    skip_prompt=False,
):
    save_dir = save_dir or default_save_dir()
    assert False, (
        post_link_or_id,
        save_dir,
        edit_cmd,
        diff_cmd,
        skip_diff,
        skip_prompt,
    )


def default_save_dir():
    project_dir = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(project_dir, "posts")


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
    post = _get_post(post_link_or_id)
    local_post = _local_post(post, save_dir)
    if not force and local_post == post["raw"]:
        log.info("Post %i is up-to-date", post["id"])
        raise SystemExit(0)
    if not skip_diff:
        _diff_post(post, local_post, diff_cmd)
    if not skip_prompt:
        _verify_publish(post)
    _publish_post(post, local_post, comment, edit_cmd)


def _local_post(post, save_dir):
    save_dir = save_dir or default_save_dir()
    save_path = _save_path_for_post(post, save_dir)
    if not os.path.exists(save_path):
        raise SystemExit("Cannot find local post '%s'" % save_path)
    return open(save_path).read()


def _save_path_for_post(post, save_dir):
    return os.path.join(save_dir, "%s.md" % post["id"])


def _diff_post(post, local_post, diff_cmd):
    docs.diff_post(post["id"], post["raw"], local_post, diff_cmd)


def _verify_publish(post):
    if not util.confirm("Publish post %i?" % post["id"], True):
        raise SystemExit(1)


def _publish_post(post, local_post, comment, edit_cmd):
    comment = comment or _get_comment(edit_cmd)
    assert False, comment
    api.update_post(post["id"], local_post, comment)


def _get_comment(editor):
    s = util.edit_msg("Enter a comment your changes.", editor)
    if not s:
        log.warning("Aborting publish due to empty comment.")
        raise SystemExit(1)
    return s


def diff(post_link_or_id, save_dir=None, diff_cmd=None):
    post = _get_post(post_link_or_id)
    local_post = _local_post(post, save_dir)
    if local_post == post["raw"]:
        log.info("Post %i is up-to-date", post["id"])
        raise SystemExit(0)
    _diff_post(post, local_post, diff_cmd)


def fetch_post(post_link_or_id, save_dir=None):
    save_dir = save_dir or default_save_dir()
    post = _get_post(post_link_or_id)
    util.ensure_dir(save_dir)
    save_path = _save_dir_for_post(post, save_dir)
    log.action("Writing post %s to %s", post["id"], save_path)
    with open(save_path, "w") as f:
        f.write(post["raw"])


def _get_post(link_or_id):
    api = init_api()
    try:
        post_id = int(link_or_id)
    except ValueError:
        link = list_or_id
        log.info("Getting post for '%s'", link)
        return _post_for_link(link, api)
    else:
        log.info("Getting post %i", post_id)
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


def fetch_all(index_path=None, save_dir=None):
    index_path = index_path or docs.default_index_path()
    save_dir = save_dir or default_save_dir()
    assert False, (index_path, save_dir)
