import glob
import hashlib
import os

from . import docs
from . import util

from .api import init as init_api
from .api import DiscourseClientError
from .log_util import get_logger

log = get_logger()


class LocalTopicChanged(SystemExit):
    def __init__(self, topic, local_path):
        super(LocalTopicChanged, self).__init__(1)
        self.topic = topic
        self.local_path = local_path


class Topic(object):
    def __init__(self, topic_id, post_id, raw):
        self.topic_id = topic_id
        self.post_id = post_id
        self.raw = raw


###################################################################
# Edit
###################################################################


def edit(topic_link_or_id, save_dir=None, edit_cmd=None, force=False):
    topic, path = _ensure_topic(topic_link_or_id, save_dir, force)
    log.info("Editing %s" % os.path.relpath(path))
    util.edit(path, edit_cmd)


def _ensure_topic(topic_link_or_id, save_dir, force):
    try:
        return fetch_topic(topic_link_or_id, save_dir, force)
    except LocalTopicChanged as e:
        return e.topic, e.local_path


###################################################################
# Publish
###################################################################


def publish(
    topic_link_or_id,
    save_dir=None,
    comment=None,
    diff_cmd=None,
    edit_cmd=None,
    skip_diff=False,
    skip_prompt=False,
    force=False,
):
    api = init_api()
    topic = _get_topic(topic_link_or_id, api)
    local_topic = _local_topic(topic, save_dir)
    topic_raw = _topic_raw(topic)
    if not force and local_topic == topic_raw:
        log.info("Topic %i is up-to-date", topic["id"])
        raise SystemExit(0)
    if not skip_diff:
        _diff_topic(topic, local_topic, diff_cmd)
    if not skip_prompt:
        _verify_publish(topic)
    _publish_topic(topic, local_topic, comment, edit_cmd, api)


def _topic_raw(topic):
    # Discourse strips trailing LF so we add back support compare to
    # local topics.
    return topic["raw"] + "\n"


def _local_topic(topic, save_dir):
    save_dir = save_dir or default_save_dir()
    save_path = _save_path_for_topic(topic, save_dir)
    if not os.path.exists(save_path):
        raise SystemExit("Cannot find local topic '%s'" % save_path)
    return open(save_path).read()


def default_save_dir():
    project_dir = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(project_dir, "topics")


def _save_path_for_topic(topic, save_dir):
    return os.path.join(save_dir, "%s.md" % topic["id"])


def _diff_topic(topic, local_topic, diff_cmd):
    docs.diff_topic(topic["id"], _topic_raw(topic), local_topic, diff_cmd)


def _verify_publish(topic):
    if not util.confirm("Publish topic %i?" % topic["id"], True):
        raise SystemExit(1)


def _publish_topic(topic, local_topic, comment, edit_cmd, api):
    comment = comment or _get_comment(edit_cmd)
    log.action("Publishing %s", topic["id"])
    api.update_topic(topic["id"], local_topic, comment)
    sha_path = _sha_path_for_topic(topic, save_dir)
    with open(sha_path, "w") as f:
        f.write(topic_sha)


def _get_comment(editor):
    s = util.edit_msg("Enter a comment your changes.", editor)
    if not s:
        log.warning("Aborting publish due to empty comment.")
        raise SystemExit(1)
    return s


###################################################################
# Diff
###################################################################


def diff(topic_link_or_id, save_dir=None, diff_cmd=None):
    api = init_api()
    topic = _get_topic(topic_link_or_id, api)
    local_topic = _local_topic(topic, save_dir)
    if local_topic == _topic_raw(topic):
        log.info("Topic %i is up-to-date", topic["id"])
        raise SystemExit(0)
    _diff_topic(topic, local_topic, diff_cmd)


###################################################################
# Fetch
###################################################################


def fetch_topic(topic_link_or_id, save_dir=None, force=False):
    api = init_api()
    save_dir = save_dir or default_save_dir()
    topic = _get_topic(topic_link_or_id, api)
    save_path = _save_path_for_topic(topic, save_dir)
    sha_path = _sha_path_for_topic(topic, save_dir)
    if not force and _local_topic_changed(save_path, sha_path):
        log.warning(
            "Local topic %s changed since last fetch, skipping (use force to override)",
            topic["id"],
        )
        raise LocalTopicChanged(topic["id"], save_path)
    topic_raw = _topic_raw(topic)
    if not force and os.path.exists(save_path):
        if topic_raw == open(save_path).read():
            log.info("Topic %s is up-to-date", topic["id"])
            return topic, save_path
    topic_sha = hashlib.sha1(topic_raw).hexdigest()
    log.action("Saving fetched topic %s to %s", topic["id"], os.path.relpath(save_path))
    util.ensure_dir(save_dir)
    with open(sha_path, "w") as f:
        f.write(topic_sha)
    with open(save_path, "w") as f:
        f.write(topic_raw)
    return topic, save_path


def _sha_path_for_topic(topic, save_dir):
    return os.path.join(save_dir, "%s.sha" % topic["id"])


def _local_topic_changed(topic_path, sha_path):
    if not os.path.exists(topic_path) or not os.path.exists(sha_path):
        return False
    current_sha = hashlib.sha1(open(topic_path).read()).hexdigest()
    base_sha = open(sha_path).read()
    return current_sha != base_sha


def _get_topic(link_or_id, api):
    try:
        topic_id = int(link_or_id)
    except ValueError:
        link = link_or_id
        log.info("Fetching topic for '%s'", link)
        return _topic_for_link(link, api)
    else:
        log.info("Fetching topic %i", topic_id)
        return _topic_for_id(topic_id, api)


def _topic_for_id(topic_id, api):
    try:
        return api.topic(topic_id)
    except DiscourseClientError:
        raise SystemExit("No such topic: %i" % topic_id)


def _topic_for_link(link, api):
    try:
        topic = api._get(_ensure_abs_link(link))
    except DiscourseClientError:
        raise SystemExit("Cannot find topic for '%s'" % link)
    else:
        topic_id = topic["topic_stream"]["topics"][0]["id"]
        return _topic_for_id(topic_id, api)


def _ensure_abs_link(link):
    return link if link[:1] == "/" else "/" + link


###################################################################
# Fetch all
###################################################################


def fetch_all(index_path=None, save_dir=None, force=False):
    index_path = index_path or docs.default_index_path()
    for link in docs.iter_index_links(index_path):
        try:
            fetch_topic(link, save_dir=save_dir, force=force)
        except LocalTopicChanged as e:
            assert not force


###################################################################
# Log changed
###################################################################


def log_locally_changed(save_dir=None):
    save_dir = save_dir or default_save_dir()
    for topic_path in glob.glob(os.path.join(save_dir, "*.md")):
        sha_path = topic_path[:-3] + ".sha"
        if not os.path.exists(sha_path):
            log.warning("Topic %s missing sha", os.path.relpath(sha_path))
        base_sha = open(sha_path).read()
        cur_sha = hashlib.sha1(open(topic_path).read()).hexdigest()
        log.debug("testing %s: base=%s cur=%s", topic_path, base_sha, cur_sha)
        if base_sha != cur_sha:
            log.info(os.path.relpath(topic_path))
