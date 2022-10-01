import datetime
import logging
import os
import time

from .api import DiscourseClientError
from .api import init as init_api
from .api import public_get_data
from .log_util import get_logger

from . import cache
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
    save_dir = save_dir or default_save_dir()
    log.action("Fetching topic %s", topic_id)
    try:
        topic = _topic_for_id(topic_id)
    except DiscourseClientError as e:
        _handle_fetch_topic_error(e, topic_id)
    else:
        if force or _check_save_conflict(topic, save_dir):
            _save_topic(topic, save_dir)


def _handle_fetch_topic_error(e, topic_id):
    if "not found" in str(e):
        raise SystemExit("Topic %i does not exit", topic_id)
    else:
        raise SystemExit("Error occurred fetching topic %i: %s", topic_id, e)


def default_save_dir():
    def try_path(path):
        return path if os.path.exists(path) else None
    try_paths = [
        os.path.join(os.getcwd(), "topics"),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "topics")
    ]
    try:
        return next((path for path in try_paths if path is not None))
    except StopIteration:
        raise SystemExit("Cannot find 'topics' directory - specify with --save-path")


def _topic_for_id(topic_id):
    post_id = _post_id_for_topic(topic_id)
    post = _get_post(post_id)
    assert post["id"] == post_id, (topic_id, post_id, post)
    return Topic(topic_id, post_id, _post_raw(post))


def _post_id_for_topic(topic_id):
    cached = cache.read(topic_post_cache_key(topic_id))
    if cached:
        return int(cached)
    try:
        topic = _get_topic(topic_id)
    except DiscourseClientError:
        raise SystemExit("No such topic: %i", topic_id)
    else:
        post_id = topic["post_stream"]["posts"][0]["id"]
        cache.write(topic_post_cache_key(topic_id), str(post_id))
        return post_id


def topic_post_cache_key(topic_id):
    return "topic-post:%i" % topic_id


def _get_topic(topic_id):
    return public_get_data("https://my.guild.ai/t/%i.json" % topic_id)


def _get_post(post_id):
    return public_get_data("https://my.guild.ai/posts/%i.json" % post_id)


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
    return util.read_utf(path1) != util.read_utf(path2)


def _save_topic(topic, save_dir):
    util.ensure_dir(save_dir)
    _save_topic_main(topic, save_dir, topic.post_raw)
    _save_topic_base(topic, save_dir, topic.post_raw)


def _save_topic_main(topic, save_dir, raw):
    util.write_utf(_topic_path(topic, save_dir), raw)


def _save_topic_base(topic, save_dir, raw):
    util.write_utf(_topic_base_path(topic, save_dir), raw)


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
    return os.path.join(save_dir, ".%s.base" % _topic_id(topic))


def _topic_latest_path(topic, save_dir):
    return os.path.join(save_dir, ".%s.latest" % _topic_id(topic))


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
    log.info("Getting latest version of topic %i", topic_id)
    latest_path = _fetch_topic_latest(topic_id, save_dir)
    util.diff_files(topic_path, latest_path, diff_cmd)


def _fetch_topic_latest(topic_id, save_dir):
    topic = _topic_for_id(topic_id)
    latest_path = _topic_latest_path(topic_id, save_dir)
    util.write_utf(latest_path, topic.post_raw)
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
        and _check_latest_changed(topic_id, save_dir)
    ):
        if not yes and not skip_diff:
            base_path = _topic_base_path(topic_id, save_dir)
            if not os.path.exists(base_path):
                raise SystemExit(
                    "Original post for topic %i not available for diff. Use "
                    "--skip-diff to bypass this check."
                )
            util.diff_files(base_path, topic_path, diff_cmd)
        if not yes and not skip_diff and not _confirm_publish(topic_id):
            raise SystemExit(1)
        comment = comment or (not no_comment and _get_comment(edit_cmd)) or ""
        log.action("Publishing %i", topic_id)
        topic = _topic_for_id(topic_id)
        local_raw = util.read_utf(topic_path)
        if not force:
            _assert_latest_unchanged(topic_id, save_dir, topic.post_raw)
        api.update_post(topic.post_id, local_raw, comment)
        _save_topic_base(topic_id, save_dir, local_raw)


def _check_local_changed(topic_id, save_dir):
    if not _local_topic_changed(topic_id, save_dir):
        raise SystemExit(
            "Topic %i has not been modified. Use --force to override this check.",
            topic_id,
        )
    return True


def _local_topic_changed(topic_id, save_dir):
    topic_path = _topic_path(topic_id, save_dir)
    base_path = _topic_base_path(topic_id, save_dir)
    return _files_differ(base_path, topic_path)


def _check_latest_changed(topic_id, save_dir):
    base_path = _topic_base_path(topic_id, save_dir)
    if not os.path.exists(base_path):
        raise SystemExit(
            "Cannot check if topic %i changed on the server (missing "
            "base version). Use --force to override this safeguard.",
            topic_id,
        )
    latest_path = _fetch_topic_latest(topic_id, save_dir)
    if _files_differ(base_path, latest_path):
        raise SystemExit(
            "Topic %i has changed on the server since it was fetched. "
            "Use 'my-guild diff --latest %i' to view differences. Use --force to "
            "override this safeguard.",
            topic_id,
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


def _assert_latest_unchanged(topic_id, save_dir, latest_raw):
    latest_path = _fetch_topic_latest(topic_id, save_dir)
    if util.read_utf(latest_path) != latest_raw:
        raise SystemExit(
            "Topic %i changed on the server since last check. Use --force to"
            "override this safeguard.",
            topic_id,
        )


###################################################################
# Watch
###################################################################


def watch(topic_id, save_dir=None):
    api = init_api()
    save_dir = save_dir or default_save_dir()
    topic_path = _topic_path(topic_id, save_dir)
    if not os.path.exists(topic_path):
        raise SystemExit("Topic %i not found in %s", topic_id, save_dir)
    base_path = _topic_base_path(topic_id, save_dir)
    if not os.path.exists(base_path):
        raise SystemExit(
            "Missing base version for topic %i - cannot run watch" % topic_id
        )
    topic = _topic_for_id(topic_id)
    log.info("Watching topic %i (%s)", topic_id, os.path.relpath(topic_path))
    loop = util.SafeLoop(
        limit_max=5,
        limit_interval=5.0,
        desc="topic %i (%s) modified" % (topic_id, topic_path),
    )
    last_mtime = 0  # Try to publish once at start.
    while loop:
        cur_mtime = util.mtime(topic_path)
        if cur_mtime > last_mtime:
            loop.incr()
            if _local_topic_changed(topic_id, save_dir):
                latest_path = _fetch_topic_latest(topic_id, save_dir)
                if _files_differ(base_path, latest_path):
                    _latest_changed_on_watch_error(topic_id)
                log.action(
                    "[%s] Publishing topic %i",
                    datetime.datetime.now().strftime("%D %T"),
                    topic_id,
                )
                local_raw = util.read_utf(topic_path)
                try:
                    api.update_post(topic.post_id, local_raw)
                except Exception as e:
                    _update_post_on_watch_error(topic_id, e)
                else:
                    _save_topic_base(topic_id, save_dir, local_raw)
            last_mtime = cur_mtime
        time.sleep(0.1)


def _latest_changed_on_watch_error(topic_id):
    msg = (
        "Topic %i has changed on the server since it was fetched. "
        "Resolve this conflict using 'my-guild diff --latest %i and "
        "publish the topic manually using --force."
    ) % (topic_id, topic_id)
    util.notify_send("ERROR during my-guild watch: %s" % msg, urgency="critical")
    raise SystemExit(msg)


def _update_post_on_watch_error(topic_id, e):
    msg = "error publishing topic %i: %s" % (topic_id, e)
    util.notify_send("ERROR during my-guild watch: %s" % msg, urgency="critical")
    raise SystemExit(msg)


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
    index_path = docs.default_index_path()
    warnings = False
    for link in docs.iter_index_links(index_path):
        if link.startswith("commands/"):
            continue
        try:
            topic_id = _topic_id_for_link(link)
        except Exception as e:
            if log.getEffectiveLevel() <= logging.DEBUG:
                log.exception("topic for link '%s'", link)
            log.error("Error reading topic for link '%s': %s", link, e)
            warnings = True
        else:
            try:
                util.retry(
                    "fetch topic %i" % topic_id,
                    # pylint: disable=cell-var-from-loop
                    lambda: fetch(topic_id, save_dir=save_dir, force=force),
                )
            except SystemExit as e:
                if stop_on_error:
                    raise
                if e.args and not isinstance(e.args[0], int):
                    log.warning(*e.args)
                warnings = True
    if warnings:
        raise SystemExit(
            "One or more warnings occurred while fetching docs. Refer to logs "
            "above for details."
        )


def _topic_id_for_link(link):
    return docs.get_link_topic(link)["id"]


###################################################################
# Publish all
###################################################################


def publish_all(
    comment=None,
    no_comment=False,
    skip_diff=False,
    yes=False,
    force=False,
    stop_on_error=False,
    save_dir=None,
    edit_cmd=None,
    diff_cmd=None,
):
    init_api()  # Force early error if API creds not configured.
    save_dir = save_dir or default_save_dir()
    if not yes and not skip_diff:
        topic_ids = diff_base_all(save_dir, diff_cmd)
    else:
        topic_ids = sorted(_iter_local_topic_ids(save_dir))
    if not topic_ids:
        log.info("Nothing to publish")
        raise SystemExit(1)
    if not yes and not skip_diff and not _confirm_publish_all():
        raise SystemExit(1)
    comment = comment or (not no_comment and _get_comment(edit_cmd)) or ""
    assert comment or no_comment
    warnings = False
    for topic_id in topic_ids:
        if not force and not _local_topic_changed(topic_id, save_dir):
            continue
        try:
            util.retry(
                "publish topic %i" % topic_id,
                # pylint: disable=cell-var-from-loop
                lambda: publish(
                    topic_id,
                    save_dir=save_dir,
                    comment=comment,
                    no_comment=True,
                    force=force,
                    skip_diff=True,
                    yes=True,
                ),
            )
        except SystemExit as e:
            if stop_on_error:
                raise
            if e.args and not isinstance(e.args[0], int):
                log.warning(*e.args)
            warnings = True
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


def _confirm_publish_all():
    return util.confirm("Publish these changes?", default=True)


###################################################################
# Diff base all
###################################################################


def diff_base_all(save_dir=None, diff_cmd=None):
    save_dir = save_dir or default_save_dir()
    diffed = []
    for topic_id in sorted(_iter_local_topic_ids(save_dir)):
        if not _local_topic_changed(topic_id, save_dir):
            continue
        diff_base(topic_id, save_dir=save_dir, diff_cmd=diff_cmd)
        diffed.append(topic_id)
    return diffed


###################################################################
# Diff latest all
###################################################################


def diff_latest_all(save_dir=None, diff_cmd=None):
    save_dir = save_dir or default_save_dir()
    latest = []
    for topic_id in sorted(_iter_local_topic_ids(save_dir)):
        log.action("Getting latest version of topic %i", topic_id)
        try:
            latest_path = _fetch_topic_latest(topic_id, save_dir)
        except DiscourseClientError as e:
            log.warning("Could not get latest for topic %i: %s", topic_id, e)
        else:
            latest.append((topic_id, latest_path))
    diffed = []
    for topic_id, latest_path in latest:
        topic_path = _topic_path(topic_id, save_dir)
        if not _files_differ(latest_path, topic_path):
            continue
        util.diff_files(topic_path, latest_path, diff_cmd)
        diffed.append(topic_id)
    return diffed
