import logging
import os
import pprint

from .api import DiscourseClientError
from .api import init as init_api
from .log_util import get_logger

from . import docs
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
        raise SystemExit(
            "Topic %s already exists but does not have a base version "
            "to check for changes. Use --force to override this safeguard.",
            topic.topic_id,
        )
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
    no_comment=False,
    comment=None,
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
        if not yes and not skip_diff:
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
        comment = comment or (not no_comment and _get_comment(edit_cmd)) or ""
        log.action("Publishing %i", topic_id)
        topic = _topic_for_id(topic_id, api)
        local_raw = open(topic_path).read()
        if not force:
            _assert_latest_unchanged(topic_id, save_dir, topic.post_raw, api)
        api.update_post(topic.post_id, local_raw, comment)
        _save_topic_base(topic_id, save_dir, local_raw)


def _check_local_changed(topic_id, save_dir):
    if not _topic_base_changed(topic_id, save_dir):
        raise SystemExit(
            "Topic %i has not been modified. Use --force to override this check.",
            topic_id,
        )
    return True


def _topic_base_changed(topic_id, save_dir):
    topic_path = _topic_path(topic_id, save_dir)
    base_path = _topic_base_path(topic_id, save_dir)
    return _files_differ(base_path, topic_path)


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


###################################################################
# Edit
###################################################################


def edit(
    topic_id,
    save_dir=None,
    no_comment=False,
    comment=None,
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
        raise SystemExit(0)
    publish(
        topic_id,
        save_dir=save_dir,
        no_comment=no_comment,
        comment=comment,
        force=force,
        skip_diff=skip_diff,
        yes=yes,
        diff_cmd=diff_cmd,
        edit_cmd=edit_cmd,
    )


###################################################################
# Delete
###################################################################


def delete(topic_id, save_dir=None, yes=False, force=False):
    save_dir = save_dir or default_save_dir()
    topic_path = _topic_path(topic_id, save_dir)
    if not force and not os.path.exists(topic_path):
        raise SystemExit("Topic %i not found.", topic_id)
    base_path = _topic_base_path(topic_id, save_dir)
    if not force and os.path.exists(base_path) and _files_differ(topic_path, base_path):
        raise SystemExit(
            "Topic %i has local changes. Use --diff-base to see changes. Use --force "
            "to bypass this safeguard.",
            topic_id,
        )
    if yes or _confirm_delete_local_files(topic_id):
        _delete_local_topic(topic_id, save_dir)


def _confirm_delete_local_files(topic_id):
    return util.confirm("Remove local files for topic %i?" % topic_id, default=True)


def _delete_local_topic(topic_id, save_dir):
    log.action("Removing local files for topic %i", topic_id)
    util.ensure_deleted(_topic_latest_path(topic_id, save_dir))
    util.ensure_deleted(_topic_base_path(topic_id, save_dir))
    util.ensure_deleted(_topic_path(topic_id, save_dir))


###################################################################
# Fetch docs
###################################################################


def fetch_docs(save_dir=None, index_path=None, force=None, stop_on_error=False):
    api = init_api()
    index_path = docs.default_index_path()
    errors = False
    for link in docs.iter_index_links(index_path):
        if link.startswith("commands/"):
            continue
        try:
            topic = api._get("/" + link)
        except Exception as e:
            if log.getEffectiveLevel() <= logging.DEBUG:
                log.exception("topic for link '%s'", link)
            log.error("Error reading topic for link '%s': %s", link, e)
        else:
            if (
                not isinstance(topic, dict)
                or "id" not in topic
                or "post_stream" not in topic
            ):
                if log.getEffectiveLevel() <= logging.DEBUG:
                    log.debug("Result for '%s':\n%s", link, pprint.pformat(topic))
                log.warning("Unxpected result for link '%s': not a topic.", link)
                continue
            try:
                util.retry(
                    "fetch topic %i" % topic["id"],
                    lambda: fetch(topic["id"], save_dir=save_dir, force=force),
                )
            except SystemExit as e:
                if stop_on_error:
                    raise
                if e.args and not isinstance(e.args[0], int):
                    log.error(*e.args)
                errors = True
    if errors:
        raise SystemExit(
            "One or more errors occurred while fetching docs. Refer to logs "
            "above for details."
        )


###################################################################
# Publish all
###################################################################


def publish_all(
    save_dir=None,
    no_comment=False,
    comment=None,
    force=False,
    stop_on_error=False,
    edit_cmd=None,
):
    init_api()  # Force early error if API creds not configured.
    save_dir = save_dir or default_save_dir()
    comment = comment or (not no_comment and _get_comment(edit_cmd)) or ""
    assert comment or no_comment
    warnings = False
    for topic_id in sorted(_iter_local_topic_ids(save_dir)):
        if not force and not _topic_base_changed(topic_id, save_dir):
            log.info("Topic %i has not been modified.", topic_id)
            continue
        try:
            util.retry(
                "publish topic %i" % topic_id,
                lambda: publish(
                    topic_id,
                    save_dir=save_dir,
                    no_comment=no_comment,
                    comment=comment,
                    force=force,
                    yes=True,
                ),
            )
        except SystemExit as e:
            if stop_on_error:
                raise
            if e.args and not isinstance(e.args[0], int):
                log.warning(*e.args)
            errors = True
    if warnings:
        raise SystemExit(
            "One or more warnings occurred while fetching docs. Refer to logs "
            "above for details."
        )


def _iter_local_topic_ids(save_dir):
    for name in os.listdir(save_dir):
        if name.endswith(".md"):
            try:
                yield int(name[:-3])
            except ValueError:
                pass


###################################################################
# Diff base all
###################################################################


def diff_base_all(save_dir=None, diff_cmd=None):
    save_dir = save_dir or default_save_dir()
    for topic_id in sorted(_iter_local_topic_ids(save_dir)):
        if not _topic_base_changed(topic_id, save_dir):
            continue
        diff_base(topic_id, save_dir=save_dir, diff_cmd=diff_cmd)
