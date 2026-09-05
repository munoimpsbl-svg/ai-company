import base64
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence
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


@dataclass(frozen=True)
class ExactReplacement:
    old: str
    new: str
    expected_count: int = 1


@dataclass(frozen=True)
class PageUpdatePlan:
    page_id: int
    source_modified: str
    original_content: str
    updated_content: str
    original_sha256: str
    updated_sha256: str


@dataclass(frozen=True)
class UpdatedPage:
    page_id: int
    link: str
    status: str
    modified: str
    before_sha256: str
    after_sha256: str
    before_length: int
    after_length: int


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
        credential_prefixes = [_wordpress_env_prefix(site_url_env)]
        if fallback_site_url_env:
            credential_prefixes.append(_wordpress_env_prefix(fallback_site_url_env))
        username_envs = [f"{prefix}_WORDPRESS_USERNAME" for prefix in credential_prefixes]
        password_envs = [f"{prefix}_WORDPRESS_APP_PASSWORD" for prefix in credential_prefixes]
        username = _first_env(*username_envs, "WORDPRESS_USERNAME")
        app_password = _first_env(*password_envs, "WORDPRESS_APP_PASSWORD")

        missing = []
        if not site_url:
            missing.append(site_url_env)
        if not username:
            missing.append(" / ".join([*username_envs, "WORDPRESS_USERNAME"]))
        if not app_password:
            missing.append(" / ".join([*password_envs, "WORDPRESS_APP_PASSWORD"]))
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

    def get_page(self, page_id: int) -> Dict:
        return self._request_json(
            "GET",
            f"/wp-json/wp/v2/pages/{int(page_id)}",
            {"context": "edit"},
        )

    def plan_page_update(
        self,
        page_id: int,
        replacements: Sequence[ExactReplacement],
        *,
        forbidden_markers: Sequence[str] = ("[Truncated]",),
        max_shrink_ratio: float = 0.02,
    ) -> PageUpdatePlan:
        if not replacements:
            raise WordPressWriteError("置換内容が空のため、更新を中止しました")
        if not 0 <= max_shrink_ratio < 1:
            raise WordPressWriteError("max_shrink_ratioは0以上1未満で指定してください")

        page = self.get_page(page_id)
        original = _raw_content(page)
        if not original.strip():
            raise WordPressWriteError("現行本文が空のため、更新を中止しました")
        _reject_forbidden_markers(original, forbidden_markers, "現行本文")

        updated = original
        for index, replacement in enumerate(replacements, start=1):
            if not replacement.old:
                raise WordPressWriteError(f"置換{index}の検索文字列が空です")
            actual_count = updated.count(replacement.old)
            if actual_count != replacement.expected_count:
                raise WordPressWriteError(
                    f"置換{index}の一致件数が想定外です: "
                    f"expected={replacement.expected_count}, actual={actual_count}"
                )
            updated = updated.replace(replacement.old, replacement.new)

        if updated == original:
            raise WordPressWriteError("本文に差分がないため、更新を中止しました")
        _reject_forbidden_markers(updated, forbidden_markers, "更新後本文")
        minimum_length = int(len(original) * (1 - max_shrink_ratio))
        if len(updated) < minimum_length:
            raise WordPressWriteError(
                "本文が許容範囲を超えて減少するため、更新を中止しました: "
                f"before={len(original)}, after={len(updated)}"
            )

        return PageUpdatePlan(
            page_id=int(page_id),
            source_modified=_modified_value(page),
            original_content=original,
            updated_content=updated,
            original_sha256=_sha256(original),
            updated_sha256=_sha256(updated),
        )

    def publish_page_update(self, plan: PageUpdatePlan) -> UpdatedPage:
        latest = self.get_page(plan.page_id)
        latest_content = _raw_content(latest)
        if _sha256(latest_content) != plan.original_sha256:
            raise WordPressWriteError("計画作成後に本文が変更されたため、保存を中止しました")
        latest_modified = _modified_value(latest)
        if plan.source_modified and latest_modified != plan.source_modified:
            raise WordPressWriteError("計画作成後に更新日時が変わったため、保存を中止しました")

        response = self._request_json(
            "POST",
            f"/wp-json/wp/v2/pages/{plan.page_id}",
            body={"content": plan.updated_content},
        )
        verified = self.get_page(plan.page_id)
        verified_content = _raw_content(verified)
        if _sha256(verified_content) != plan.updated_sha256:
            rollback_state = "未実行"
            if _modified_value(verified) == _modified_value(response):
                self._request_json(
                    "POST",
                    f"/wp-json/wp/v2/pages/{plan.page_id}",
                    body={"content": plan.original_content},
                )
                restored = self.get_page(plan.page_id)
                rollback_state = (
                    "成功"
                    if _sha256(_raw_content(restored)) == plan.original_sha256
                    else "失敗"
                )
            raise WordPressWriteError(
                "保存後の本文が計画と一致しません。"
                f"ロールバック: {rollback_state}"
            )

        return UpdatedPage(
            page_id=plan.page_id,
            link=str(verified.get("link", response.get("link", ""))),
            status=str(verified.get("status", response.get("status", ""))),
            modified=_modified_value(verified),
            before_sha256=plan.original_sha256,
            after_sha256=plan.updated_sha256,
            before_length=len(plan.original_content),
            after_length=len(plan.updated_content),
        )

    def update_page_exact(
        self,
        page_id: int,
        replacements: Sequence[ExactReplacement],
        *,
        forbidden_markers: Sequence[str] = ("[Truncated]",),
        max_shrink_ratio: float = 0.02,
    ) -> UpdatedPage:
        plan = self.plan_page_update(
            page_id,
            replacements,
            forbidden_markers=forbidden_markers,
            max_shrink_ratio=max_shrink_ratio,
        )
        return self.publish_page_update(plan)

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
            "User-Agent": "AI-COMPANY-WP-WRITER/2.0",
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


def _wordpress_env_prefix(env_name: str) -> str:
    suffix = "_WORDPRESS_URL"
    if env_name.endswith(suffix):
        return env_name[: -len(suffix)]
    return env_name


def _first_env(*names: str) -> str:
    for name in names:
        value = os.getenv(name, "").strip()
        if value:
            return value
    return ""


def _raw_content(page: Dict) -> str:
    content = page.get("content", {})
    raw = content.get("raw") if isinstance(content, dict) else None
    if not isinstance(raw, str):
        raise WordPressWriteError(
            "WordPress REST APIから編集用の本文を取得できません。context=editの権限を確認してください"
        )
    return raw


def _modified_value(page: Dict) -> str:
    return str(page.get("modified_gmt") or page.get("modified") or "")


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _reject_forbidden_markers(content: str, markers: Sequence[str], label: str) -> None:
    found = [marker for marker in markers if marker and marker in content]
    if found:
        raise WordPressWriteError(f"{label}に禁止マーカーがあります: {', '.join(found)}")
