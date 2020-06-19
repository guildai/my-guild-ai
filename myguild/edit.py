import os

from .api import DiscourseClientError
from .api import init as init_api
from .log_util import get_logger

from . import util

log = get_logger()


class Topic(object):
    def __init__(self, topic_id, post_id, post_raw):
        self.topic_id = topic_id
        self.post_id = post_id
        self.post_raw = post_raw

    def __str__(self):
        return "<myguild.Topic topic_id=%s post_id=%s>" % (self.topic_id, self.post_id)


###################################################################
# Fetch
###################################################################


def fetch(topic_id, save_dir=None, force=False):
    api = init_api()
    save_dir = save_dir or default_save_dir()
    log.action("Fetching topic %s", topic_id)
    topic = _topic_for_id(topic_id, api)
    if force or _check_save_conflict(topic, save_dir):
        _save_topic(topic, save_dir)


def default_save_dir():
    project_dir = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(project_dir, "topics")


def _topic_for_id(topic_id, api):
    try:
        topic = api.topic(topic_id)
    except DiscourseClientError:
        raise SystemExit("No such topic: %i", topic_id)
    else:
        post = api.post(topic["post_stream"]["posts"][0]["id"])
        return Topic(topic_id, post["id"], _post_raw(post))


def _post_raw(post):
    # Append newline, which Discourse strips.
    return post["raw"] + "\n"


def _check_save_conflict(topic, save_dir):
    topic_path = _topic_path(topic, save_dir)
    if not os.path.exists(topic_path):
        return True
    base_path = _topic_base_path(topic, save_dir)
    if not os.path.exists(base_path):
        log.error(
            "Topic %s already exists. Use --force to override this safeguard.",
            topic.topic_id,
        )
        raise SystemExit()
    if _files_differ(topic_path, base_path):
        raise SystemExit(
            "Topic %s has been modified locally. Use --force to override this "
            "safeguard." % topic.topic_id
        )
    return True


def _files_differ(path1, path2):
    return open(path1).read() != open(path2).read()


def _save_topic(topic, save_dir):
    util.ensure_dir(save_dir)
    _save_topic_main(topic, save_dir, topic.post_raw)
    _save_topic_base(topic, save_dir, topic.post_raw)


def _save_topic_main(topic, save_dir, raw):
    with open(_topic_path(topic, save_dir), "w") as f:
        f.write(raw)


def _save_topic_base(topic, save_dir, raw):
    with open(_topic_base_path(topic, save_dir), "w") as f:
        f.write(raw)


def _topic_path(topic, save_dir):
    return os.path.join(save_dir, "%s.md" % _topic_id(topic))


def _topic_id(topic):
    if isinstance(topic, int):
        return topic
    elif isinstance(topic, Topic):
        return topic.topic_id
    else:
        assert False, (type(topic), topic)


def _topic_base_path(topic, save_dir):
    return os.path.join(save_dir, "%s.base" % _topic_id(topic))


def _topic_latest_path(topic, save_dir):
    return os.path.join(save_dir, "%s.latest" % _topic_id(topic))


###################################################################
# Diff
###################################################################


def diff_base(topic_id, save_dir=None, diff_cmd=None):
    save_dir = save_dir or default_save_dir()
    topic_path = _topic_path(topic_id, save_dir)
    if not os.path.exists(topic_path):
        raise SystemExit("Topic %i not found in %s", topic_id, save_dir)
    base_path = _topic_base_path(topic_id, save_dir)
    if not os.path.exists(base_path):
        raise SystemExit(
            "Base version for topic %i not found in %s", topic_id, save_dir
        )
    util.diff_files(base_path, topic_path, diff_cmd)


def diff_latest(topic_id, save_dir=None, diff_cmd=None):
    save_dir = save_dir or default_save_dir()
    topic_path = _topic_path(topic_id, save_dir)
    if not os.path.exists(topic_path):
        raise SystemExit("Topic %i not found in %s", topic_id, save_dir)
    api = init_api()
    log.info("Getting latest version of topic %i", topic_id)
    latest_path = _fetch_topic_latest(topic_id, save_dir, api)
    util.diff_files(topic_path, latest_path, diff_cmd)


def _fetch_topic_latest(topic_id, save_dir, api):
    topic = _topic_for_id(topic_id, api)
    latest_path = _topic_latest_path(topic_id, save_dir)
    with open(latest_path, "w") as f:
        f.write(topic.post_raw)
    return latest_path


###################################################################
# Publish
###################################################################


def publish(
    topic_id,
    save_dir=None,
    comment=None,
    keep=False,
    force=False,
    skip_diff=False,
    yes=False,
    diff_cmd=None,
    edit_cmd=None,
):
    api = init_api()
    save_dir = save_dir or default_save_dir()
    topic_path = _topic_path(topic_id, save_dir)
    if not os.path.exists(topic_path):
        raise SystemExit("Topic %i not found in %s", topic_id, save_dir)
    if force or (
        _check_local_changed(topic_id, save_dir)
        and _check_latest_changed(topic_id, save_dir, api)
    ):
        if not skip_diff:
            base_path = _topic_base_path(topic_id, save_dir)
            if not os.path.exists(base_path):
                raise SystemExit(
                    "Original post for topic %i not available for diff. Use "
                    "--skip-diff to bypass this check."
                )
            log.info("Diffing topic %i changed.", topic_id)
            util.diff_files(base_path, topic_path, diff_cmd)
        if not yes and not _confirm_publish(topic_id):
            raise SystemExit(1)
        comment = comment or _get_comment(edit_cmd)
        log.action("Publishing %i", topic_id)
        topic = _topic_for_id(topic_id, api)
        local_raw = open(topic_path).read()
        if not force:
            _assert_latest_unchanged(topic_id, save_dir, topic.post_raw, api)
        api.update_post(topic.post_id, local_raw, comment)
        if keep:
            log.info("Keeping local files for topic %i (--keep specified)", topic_id)
            _save_topic_base(topic_id, save_dir, local_raw)
        else:
            if yes or _confirm_delete_local_files(topic_id):
                _delete_local_topic(topic_id, save_dir)


def _check_local_changed(topic_id, save_dir):
    topic_path = _topic_path(topic_id, save_dir)
    base_path = _topic_base_path(topic_id, save_dir)
    if not _files_differ(base_path, topic_path):
        raise SystemExit(
            "Topic has not been modified %i. Use --force to override this check.",
            topic_id,
        )
    return True


def _check_latest_changed(topic_id, save_dir, api):
    base_path = _topic_base_path(topic_id, save_dir)
    if not os.path.exists(base_path):
        raise SystemExit(
            "Cannot check if topic %i changed on the server (missing "
            "base version). Use --force to override this safeguard.",
            topic_id,
        )
    latest_path = _fetch_topic_latest(topic_id, save_dir, api)
    if _files_differ(base_path, latest_path):
        raise SystemExit(
            "Topic %i has changed on the server since it was fetched. "
            "Use --diff-latest to view differences. Use --force to override "
            "this safeguard.",
            topic_id,
        )
    return True


def _confirm_publish(topic_id):
    return util.confirm("Publish changes to topic %i?" % topic_id, default=True)


def _get_comment(editor):
    s = util.edit_msg("Enter a comment your changes.", editor)
    if not s:
        log.warning("Aborting publish due to empty comment.")
        raise SystemExit(1)
    return s


def _assert_latest_unchanged(topic_id, save_dir, latest_raw, api):
    latest_path = _fetch_topic_latest(topic_id, save_dir, api)
    if open(latest_path).read() != latest_raw:
        raise SystemExit(
            "Topic %i changed on the server since last check. Use --force to"
            "override this safeguard.",
            topic_id,
        )


def _confirm_delete_local_files(topic_id):
    return util.confirm("Remove local files for topic %i?" % topic_id, default=True)


def _delete_local_topic(topic_id, save_dir):
    log.action("Removing local files for topic %i", topic_id)
    util.ensure_deleted(_topic_latest_path(topic_id, save_dir))
    util.ensure_deleted(_topic_base_path(topic_id, save_dir))
    util.ensure_deleted(_topic_path(topic_id, save_dir))


###################################################################
# Edit
###################################################################


def edit(
    topic_id,
    save_dir=None,
    comment=None,
    keep=False,
    force=False,
    skip_diff=False,
    yes=False,
    edit_cmd=None,
    diff_cmd=None,
):
    api = init_api()
    save_dir = save_dir or default_save_dir()
    topic_path = _topic_path(topic_id, save_dir)
    if not os.path.exists(topic_path):
        log.action("Fetching topic %s", topic_id)
        topic = _topic_for_id(topic_id, api)
        _save_topic(topic, save_dir)
    util.edit(topic_path, edit_cmd)
    base_path = _topic_base_path(topic_id, save_dir)
    if not _files_differ(topic_path, base_path):
        log.info("Topic %i was not modified.", topic_id)
        if _confirm_delete_local_files(topic_id):
            _delete_local_topic(topic_id, save_dir)
        raise SystemExit(0)
    publish(
        topic_id,
        save_dir=save_dir,
        comment=comment,
        keep=keep,
        force=force,
        skip_diff=skip_diff,
        yes=yes,
        diff_cmd=diff_cmd,
        edit_cmd=edit_cmd,
    )
