from .api import init as init_api
from .log_util import get_logger

log = get_logger()

GROUP_PERM_COL = 20


def audit():
    api = init_api()
    for cat_id, cat_path in _all_categories(api):
        log.info(
            "Group permissions for category '%s' (%s):\n%s",
            cat_path,
            cat_id,
            _indent(_color_value(_format_category_group_permissions(cat_id, api))),
        )


def _all_categories(api):
    cats_lookup = {cat["id"]: cat for cat in api._get("/site.json")["categories"]}
    return sorted(
        [(id, _cat_path(id, cats_lookup)) for id, cat in cats_lookup.items()],
        key=lambda item: item[1],
    )


def _cat_path(id, cats):
    path = []
    while True:
        cat = cats[id]
        path.append(cat["slug"])
        try:
            id = cat["parent_category_id"]
        except KeyError:
            break
    return "/".join(reversed(path))


def _format_category_group_permissions(cat_id, api):
    info = api._get("/c/%s/show.json" % cat_id)
    return "\n".join(
        [
            _format_group_permission(gp, cat_id)
            for gp in info["category"]["group_permissions"]
        ]
    )


def _format_group_permission(gp, cat_id):
    padding = " " * (GROUP_PERM_COL - len(gp["group_name"]))
    return "%s: %s%s" % (
        gp["group_name"],
        padding,
        _format_permission(gp["permission_type"], cat_id),
    )


def _format_permission(val, cat_id):
    if val == 1:
        return "Create, Reply, See"
    elif val == 2:
        return "Reply, See"
    elif val == 3:
        return "See"
    else:
        log.error("Unexpected permission type value for category %s: %s", cat_id, val)
        return "UNKNOWN PERMISSION %s" % val


def _indent(s):
    return "\n".join(["  %s" % line for line in s.split("\n")])


def _color_value(s):
    return "\033[36m%s\033[0m" % s
