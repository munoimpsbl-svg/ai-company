import base64
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen


class WordPressWriteError(RuntimeError):
    pass


@dataclass(frozen=True)
class CreatedPost:
    post_id: int
    title: str
    link: str
    status: str
    missing_categories: List[str]
    missing_tags: List[str]


class WordPressWriteClient:
    def __init__(self, site_url: str, username: str, app_password: str):
        self.site_url = site_url.rstrip("/")
        credentials = f"{username}:{app_password}".encode("utf-8")
        self.authorization = "Basic " + base64.b64encode(credentials).decode("ascii")

    @classmethod
    def from_env(cls, site_url_env: str, fallback_site_url_env: Optional[str] = None):
        site_url = os.getenv(site_url_env, "").strip()
        if not site_url and fallback_site_url_env:
            site_url = os.getenv(fallback_site_url_env, "").strip()
        username = os.getenv("WORDPRESS_USERNAME", "").strip()
        app_password = os.getenv("WORDPRESS_APP_PASSWORD", "").strip()
        missing = [
            name
            for name, value in {
                site_url_env: site_url,
                "WORDPRESS_USERNAME": username,
                "WORDPRESS_APP_PASSWORD": app_password,
            }.items()
            if not value
        ]
        if missing:
            raise WordPressWriteError("WordPress認証設定が未設定です: " + ", ".join(missing))
        return cls(site_url, username, app_password)

    def create_draft_post(
        self,
        title: str,
        content: str,
        excerpt: str = "",
        categories: Optional[Iterable[str]] = None,
        tags: Optional[Iterable[str]] = None,
    ) -> CreatedPost:
        category_ids, missing_categories = self._resolve_term_ids("categories", categories or [])
        tag_ids, missing_tags = self._resolve_term_ids("tags", tags or [])
        body = {
            "title": title,
            "content": content,
            "status": "draft",
        }
        if excerpt:
            body["excerpt"] = excerpt
        if category_ids:
            body["categories"] = category_ids
        if tag_ids:
            body["tags"] = tag_ids

        response = self._request_json("POST", "/wp-json/wp/v2/posts", body=body)
        return CreatedPost(
            post_id=int(response.get("id", 0)),
            title=_clean_rendered(response.get("title", {}).get("rendered", title)),
            link=response.get("link", ""),
            status=response.get("status", "draft"),
            missing_categories=missing_categories,
            missing_tags=missing_tags,
        )

    def verify_auth(self) -> Dict:
        return self._request_json("GET", "/wp-json/wp/v2/users/me", {"context": "edit"})

    def _resolve_term_ids(self, taxonomy: str, names: Iterable[str]):
        requested = [_clean_name(name) for name in names if _clean_name(name)]
        if not requested:
            return [], []
        terms = self._request_json(
            "GET",
            f"/wp-json/wp/v2/{taxonomy}",
            {"per_page": "100", "hide_empty": "false", "context": "edit"},
        )
        index = {_normalize(term.get("name", "")): int(term["id"]) for term in terms if "id" in term}
        ids = []
        missing = []
        for name in requested:
            term_id = index.get(_normalize(name))
            if term_id:
                ids.append(term_id)
            else:
                missing.append(name)
        return ids, missing

    def _request_json(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, str]] = None,
        body: Optional[Dict] = None,
    ):
        url = urljoin(self.site_url + "/", path.lstrip("/"))
        if params:
            url = f"{url}?{urlencode(params)}"

        data = None
        headers = {
            "Authorization": self.authorization,
            "Content-Type": "application/json",
            "User-Agent": "AI-COMPANY-WP-DRAFT-WRITER/1.0",
        }
        if body is not None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")

        request = Request(url, data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode(response.headers.get_content_charset() or "utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise WordPressWriteError(f"WordPress API HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise WordPressWriteError(f"WordPress API connection error: {exc.reason}") from exc
        except json.JSONDecodeError as exc:
            raise WordPressWriteError(f"WordPress API parse error: {exc}") from exc


def load_env(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _clean_name(value: str) -> str:
    return str(value).strip()


def _normalize(value: str) -> str:
    return _clean_name(value).casefold()


def _clean_rendered(value: str) -> str:
    return str(value).replace("&#8211;", "-").replace("&#038;", "&").strip()
