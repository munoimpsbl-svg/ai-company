import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen

from core.config import load_config


def fetch():
    load_config()
    site_url = os.getenv("P003_WORDPRESS_URL", "").strip()
    if not site_url:
        return _empty()

    posts = _count_endpoint(site_url, "/wp-json/wp/v2/posts", {"status": "any"})
    published = _count_endpoint(
        site_url, "/wp-json/wp/v2/posts", {"status": "publish"}
    )
    if posts == 0:
        posts = _count_endpoint(site_url, "/wp-json/wp/v2/posts")

    return {
        "posts": posts,
        "published": published,
        "categories": _count_endpoint(site_url, "/wp-json/wp/v2/categories"),
        "tags": _count_endpoint(site_url, "/wp-json/wp/v2/tags"),
    }


def _count_endpoint(site_url, path, params=None):
    query = {"per_page": "1"}
    if params:
        query.update(params)

    url = urljoin(site_url.rstrip("/") + "/", path.lstrip("/"))
    url = f"{url}?{urlencode(query)}"
    request = Request(url, headers={"User-Agent": "AI-COMPANY-KPI/1.0"})

    try:
        with urlopen(request, timeout=20) as response:
            total = response.headers.get("X-WP-Total")
            if total is not None:
                return int(total)
            body = json.loads(response.read().decode("utf-8"))
            return len(body) if isinstance(body, list) else 0
    except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError):
        return 0


def _empty():
    return {
        "posts": 0,
        "published": 0,
        "categories": 0,
        "tags": 0,
    }
