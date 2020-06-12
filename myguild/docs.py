import datetime
import json
import os
import pprint
import re
import socket

import requests
import yaml

from .api import init as init_api
from .api import DiscourseClientError
from .log_util import getLogger

from . import cache

log = getLogger()


DEFAULT_LINK_ICON = "far-file-alt"
COMMAND_LINK_ICON = "angle-right"
GUILD_DOCS_SECTION_CLASS = "guild-docs-section"
GUILD_COMMANDS_SECTION_CLASS = "guild-docs-commands-section"


class TopicLookupError(Exception):
    pass


###################################################################
# Publish docs index
###################################################################


def publish_index(preview=False, check=False):
    api = init_api()
    log.info("Generating docs index")
    formatted_index = _format_docs_index()
    if preview:
        print(formatted_index)
        if not check:
            return
    post = _docs_index_post(api)
    if post["raw"].strip() == formatted_index:
        log.info("Docs index post (%s) is up-to-date", post["id"])
        return
    if check:
        log.action("Docs index post (%s) is out-of-date", post["id"])
        return
    comment = _publish_index_comment()
    log.action("Updating docs index post (%s)", post["id"])
    assert False
    api.update_post(post["id"], formatted_index, comment)


def _format_docs_index():
    lines = []
    index = _load_index()
    _apply_index_header(lines)
    for item in index:
        _apply_index_item(item, lines)
    return "\n".join(lines)


def _load_index():
    index_path = os.path.join(os.path.dirname(__file__), "docs-index.yml")
    with open(index_path) as f:
        return yaml.safe_load(f)


def _apply_index_header(lines):
    lines.extend(['<div data-theme-toc="true"></div>', ""])


def _apply_index_item(item, lines):
    if "section" in item:
        _apply_section(item, lines)
    else:
        log.error("unexpected item in index: %s", pprint.pformat(item))
        raise SystemExit(1)


def _apply_section(section, lines):
    lines.extend(["## %s" % section["section"], ""])
    if "links" in section:
        _apply_section_links(section, lines)
    elif "commands" in section:
        _apply_commands(section, lines)


def _apply_section_links(section, lines):
    lines.extend([_section_div_open(GUILD_DOCS_SECTION_CLASS, DEFAULT_LINK_ICON), ""])
    lines.extend([_format_section_link(link) for link in section.get("links") or []])
    lines.extend(["", "</div>", ""])


def _section_div_open(section_class, link_icon_class):
    return '<div data-guild-class="%s" data-guild-li-icon="%s">' % (
        section_class,
        link_icon_class,
    )


def _format_section_link(link):
    try:
        topic = _get_link_topic(link)
    except TopicLookupError:
        return "- !!! error getting topic for %s - see logs for details !!!" % link
    else:
        return "- [%s](%s)" % (link, topic["title"])


def _get_link_topic(link):
    cached = cache.read(_link_cache_key(link))
    if cached:
        log.info("Reading cached link info for %s", link)
        return json.loads(cached)
    log.info("Getting topic info for %s", link)
    link_topic_json = _get_link_topic_json(link)
    cache.write(_link_cache_key(link), link_topic_json)
    return json.loads(link_topic_json)


def _link_cache_key(link):
    return "link:%s" % link


def _get_link_topic_json(link):
    resp = requests.get("https://my.guild.ai/%s" % link, allow_redirects=False)
    if resp.status_code == 404:
        log.error("No permalink or broken link for %s", link)
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
        location = resp.headers.get("location")
        assert location, (link, resp)
        m = re.match(r"https://my.guild.ai/(.+)", location)
        if not m:
            log.error("Unexpected redirect host for %s: %s", link, location)
            raise TopicLookupError(link)
        topic_info_url = "https://my.guild.ai/%s.json" % m.group(1)
        resp = requests.get(topic_info_url, allow_redirects=False)
        if not resp.ok:
            log.error(
                "Error reading link topic from %s: %s (%s)",
                topic_path,
                resp.reason,
                resp.status_code,
            )
            raise TopicLookupError(link)
        content_type = resp.headers.get("content-type")
        if content_type != "application/json; charset=utf-8":
            log.error("Unexpected content type for %s: %s", topic_url, content_type)
            raise TopicLookupError(link)
        return resp.content


def _apply_commands(section, lines):
    for command in section.get("commands") or []:
        lines.extend(["### %s" % _command_section_title(command), ""])
        _apply_command_links(command, lines)


def _command_section_title(command):
    try:
        return command["section"]
    except KeyError:
        log.error("missing 'section' in command item: %s", pprint.pformat(command))
        raise SystemExit(1)


def _apply_command_links(section, lines):
    section_class = "%s %s" % (GUILD_DOCS_SECTION_CLASS, GUILD_COMMANDS_SECTION_CLASS)
    lines.extend(
        [_section_div_open(section_class, COMMAND_LINK_ICON), "",]
    )
    lines.extend([_format_section_link(link) for link in section.get("links") or []])
    lines.extend(["", "</div>", ""])


def _docs_index_post(api):
    log.info("Getting docs index topic")
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
