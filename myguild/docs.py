from __future__ import print_function

import datetime
import json
import os
import pprint
import re
import shutil
import socket
import tempfile

import requests
import six
import yaml

from .api import init as init_api
from .api import DiscourseClientError
from .log_util import get_logger

from . import cache
from . import util

log = get_logger()


DEFAULT_LINK_ICON = "far-file-alt"
COMMAND_LINK_ICON = "angle-right"
GUILD_DOCS_SECTION_CLASS = "guild-docs-section"
GUILD_COMMANDS_SECTION_CLASS = "guild-docs-commands-section"


class TopicLookupError(Exception):
    pass


###################################################################
# Publish docs index
###################################################################


def publish_index(
    preview=False,
    check=False,
    diff=False,
    check_links=None,
    force=False,
    index_path=None,
    diff_cmd=None,
):
    check = check or diff
    api = init_api()
    if check_links:
        _check_publish_links(check_links)
    else:
        _publish_index(preview, check, diff, index_path, force, diff_cmd, api)


def _check_publish_links(check_links):
    for link in check_links:
        try:
            topic = _get_link_topic(link)
        except TopicLookupError:
            raise SystemExit(1)
        else:
            log.info(
                "Got topic %s '%s' for link '%s'", topic["id"], topic["title"], link
            )


def _publish_index(preview, check, diff, index_path, force, diff_cmd, api):
    log.info("Generating docs index")
    formatted_index = _format_docs_index(index_path, force)
    if preview:
        print(formatted_index, end="")
        if not check:
            return
    post = _docs_index_post(api)
    post_raw = _post_raw(post)
    if post_raw == formatted_index:
        log.info("Docs index post (%s) is up-to-date", post["id"])
        return
    if check:
        log.action("Docs index post (%s) is out-of-date", post["id"])
        if diff:
            _diff_post(post["id"], post_raw, formatted_index, diff_cmd)
        return
    comment = _publish_index_comment()
    log.action("Updating docs index post (%s)", post["id"])
    api.update_post(post["id"], formatted_index, comment)


def _post_raw(post):
    return post["raw"] + "\n"


def _diff_post(post_id, published, generated, diff_cmd):
    tmp = tempfile.mkdtemp(prefix="myguild-diff-")
    published_path = os.path.join(tmp, "post-%s.md" % post_id)
    generated_path = os.path.join(tmp, "generated.md")
    with open(published_path, "w") as f:
        f.write(published)
    with open(generated_path, "w") as f:
        f.write(generated)
    util.diff_files(published_path, generated_path, diff_cmd)
    # Sanity check that we're deleting what we expect to delete.
    assert sorted(os.listdir(tmp)) == ["generated.md", "post-%s.md" % post_id], tmp
    shutil.rmtree(tmp)


def _format_docs_index(index_path, force):
    lines = []
    index = _load_index(index_path)
    _apply_index_header(lines)
    for item in index:
        _apply_index_item(item, force, lines)
    _check_lines(lines)
    return "\n".join(lines)


def iter_index_links(index_path):
    index = _load_index(index_path)
    seen = set()
    for item in index:
        if "section" in item:
            for link in _iter_section_links(item):
                if link not in seen:
                    yield link
                seen.add(link)


def _iter_section_links(section):
    for link in section.get("links") or []:
        yield link
    for command_section in section.get("commands") or []:
        for link in _iter_section_links(command_section):
            yield link


def _check_lines(lines):
    errors = False
    for line in lines:
        if not isinstance(line, six.string_types):
            log.info("Lines: %s", pprint.pformat(lines))
            log.error(
                "ASSERTION ERROR - got a non-string line: %r (see "
                "lines above for context)",
                line,
            )
            errors = True
    if errors:
        raise SystemExit(1)


def _load_index(index_path):
    index_path = index_path or default_index_path()
    if not os.path.exists(index_path):
        raise SystemExit("doc index '%s' does not exist" % index_path)
    with open(index_path) as f:
        return yaml.safe_load(f)


def default_index_path():
    project_dir = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(project_dir, "docs-index.yml")


def _apply_index_header(lines):
    lines.extend(["<div data-theme-toc=\"true\"></div>", ""])


def _apply_index_item(item, force, lines):
    if "section" in item:
        _apply_section(item, force, lines)
    else:
        log.error("unexpected item in index: %s", pprint.pformat(item))
        raise SystemExit(1)


def _apply_section(section, force, lines):
    lines.extend(["## %s" % section["section"], ""])
    _apply_section_description(section, lines)
    if "links" in section:
        _apply_section_links(section, force, lines)
    elif "commands" in section:
        _apply_commands(section, force, lines)


def _apply_section_description(section, lines):
    desc = section.get("description")
    if desc:
        lines.extend([desc, ""])


def _apply_section_links(section, force, lines):
    lines.extend([_section_div_open(GUILD_DOCS_SECTION_CLASS, DEFAULT_LINK_ICON), ""])
    lines.extend(
        [
            _format_section_link(link, force, section)
            for link in section.get("links") or []
        ]
    )
    lines.extend(["", "</div>", ""])


def _section_div_open(section_class, link_icon_class):
    return "<div data-guild-class=\"%s\" data-guild-li-icon=\"%s\">" % (
        section_class,
        link_icon_class,
    )


def _format_section_link(link, force, section):
    try:
        topic = _get_link_topic(link)
    except TopicLookupError:
        if force:
            return (
                "<!-- !!! ERROR formatting link '%s' - see log for details !!! -->"
                % link
            )
        raise SystemExit(1)
    else:
        title = _format_link_title(topic["title"], section)
        return "- [%s](/%s)" % (title, link)


def _format_link_title(title, section):
    while section:
        for repl in section.get("link-title-repl") or []:
            title = re.sub(_required("pattern", repl), _required("repl", repl), title)
        section = section.get("_parent")
    return title


def _required(name, mapping):
    try:
        return mapping[name]
    except KeyError:
        log.error("Missing required '%s' in %s", name, pprint.pformat(mapping))
        raise SystemExit(1)


def _get_link_topic(link):
    cached = cache.read(_link_cache_key(link))
    if cached:
        log.info("Reading cached link info for %s", link)
        return json.loads(cached)
    log.info("Fetching topic info for %s", link)
    link_topic_json = _get_link_topic_json(link)
    cache.write(_link_cache_key(link), link_topic_json)
    return json.loads(link_topic_json)


def _link_cache_key(link):
    return "link:%s" % link


def _get_link_topic_json(link):
    resp = requests.get("https://my.guild.ai/%s" % link, allow_redirects=False)
    if resp.status_code == 404:
        log.error("Topic or permalink for '%s' does not exist", link)
        raise TopicLookupError(link)
    elif resp.status_code != 301:
        log.error(
            "Unexpected non-redirect for %s: %s (%s)",
            link,
            resp.reason,
            resp.status_code,
        )
        raise TopicLookupError(link)
    else:
        return _link_topic_json_for_redirect(resp.headers.get("location"), link)


def _link_topic_json_for_redirect(location, link):
    assert location, link
    m = re.match(r"https://my.guild.ai/(.+)", location)
    if not m:
        log.error("Unexpected redirect host for %s: %s", link, location)
        raise TopicLookupError(link)
    topic_info_url = "https://my.guild.ai/%s.json" % m.group(1)
    resp = requests.get(topic_info_url, allow_redirects=False)
    if not resp.ok:
        log.error(
            "Error reading link topic from %s: %s (%s)",
            location,
            resp.reason,
            resp.status_code,
        )
        raise TopicLookupError(link)
    content_type = resp.headers.get("content-type")
    if content_type != "application/json; charset=utf-8":
        log.error("Unexpected content type for %s: %s", location, content_type)
        raise TopicLookupError(link)
    return resp.content


def _apply_commands(section, force, lines):
    for command_section in section.get("commands") or []:
        command_section["_parent"] = section
        lines.extend(["### %s" % _command_section_title(command_section), ""])
        _apply_command_links(command_section, force, lines)


def _command_section_title(command):
    try:
        return command["section"]
    except KeyError:
        log.error("missing 'section' in command item: %s", pprint.pformat(command))
        raise SystemExit(1)


def _apply_command_links(section, force, lines):
    section_class = "%s %s" % (GUILD_DOCS_SECTION_CLASS, GUILD_COMMANDS_SECTION_CLASS)
    lines.extend(
        [_section_div_open(section_class, COMMAND_LINK_ICON), "",]
    )
    lines.extend(
        [
            _format_section_link(link, force, section)
            for link in section.get("links") or []
        ]
    )
    lines.extend(["", "</div>", ""])


def _docs_index_post(api):
    log.info("Fetching docs index topic")
    try:
        topic = api._get("/docs")
    except DiscourseClientError:
        log.error(
            "Cannot find docs index topic for '/docs' permalink - "
            "create a valid permalink and run this command again"
        )
        raise SystemExit(1)
    else:
        if "post_stream" not in topic:
            log.error(
                "unexpected result for /docs permalink: %s", pprint.pformat(topic)
            )
            raise SystemExit(1)
        return api.post(topic["post_stream"]["posts"][0]["id"])


def _publish_index_comment():
    return "Docs index published from {host} on {utc_date}Z".format(
        host=socket.gethostname(), utc_date=datetime.datetime.utcnow().isoformat(),
    )
