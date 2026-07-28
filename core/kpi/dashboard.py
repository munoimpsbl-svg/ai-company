from core.kpi import ga4
from core.kpi import instagram
from core.kpi import sales
from core.kpi import search_console
from core.kpi import wordpress
from core.kpi import x


KPI_KEYS = (
    "followers",
    "impressions",
    "engagement",
    "ctr",
    "pv",
    "sales",
    "clicks",
    "position",
    "users",
    "sessions",
    "page_views",
    "engagement_time",
    "posts",
    "published",
    "categories",
    "tags",
)


def fetch():
    sources = {
        "instagram": _normalize(instagram.fetch()),
        "x": _normalize(x.fetch()),
        "wordpress": _normalize(wordpress.fetch()),
        "search_console": _normalize(search_console.fetch()),
        "ga4": _normalize(ga4.fetch()),
        "sales": _normalize(sales.fetch()),
    }
    return {
        "sources": sources,
        "total": _sum_sources(sources),
    }


def _normalize(values):
    return {key: _number(values.get(key, 0)) for key in KPI_KEYS}


def _sum_sources(sources):
    total = {key: 0 for key in KPI_KEYS}
    for values in sources.values():
        for key in KPI_KEYS:
            total[key] += _number(values.get(key, 0))
    return total


def _number(value):
    if isinstance(value, (int, float)):
        return value
    return 0
