import base64
import html
import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
PROJECT_DIR = Path(__file__).resolve().parent
PLAN_PATH = PROJECT_DIR / "TITLE_IMPROVEMENT_PLAN.md"
RESULT_PATH = PROJECT_DIR / "TITLE_IMPROVEMENT_RESULT.md"
BACKLOG_PATH = PROJECT_DIR / "IMPROVEMENT_BACKLOG.md"


@dataclass(frozen=True)
class TitleTarget:
    priority: str
    current_title: str
    improved_title: str
    reason: str
    search_intent: str
    expected_ctr: str
    approval: str


def main() -> int:
    _load_env(WORKSPACE_ROOT / ".env")
    started_at = datetime.now()
    targets = _load_go_targets(PLAN_PATH)
    result_rows = []

    try:
        client = WordPressClient.from_env()
        posts = client.list_posts()
        title_index = _build_title_index(posts)
    except Exception as exc:
        result_rows = [
            {
                "優先順位": "-",
                "記事ID": "未取得",
                "変更前": "未取得",
                "変更後": "未変更",
                "更新成功": "いいえ",
                "更新失敗": str(exc),
            }
        ]
        _write_result(started_at, targets, result_rows)
        return 1

    for target in targets:
        post = title_index.get(_normalize_title(target.current_title))
        already_updated = False
        if post is None:
            post = title_index.get(_normalize_title(target.improved_title))
            already_updated = post is not None

        success = False
        error = ""
        post_id = "未取得"
        before_title = target.current_title
        after_title = "未変更"

        try:
            if target.approval != "GO":
                raise RuntimeError("GO以外のため未実行")
            if not target.improved_title or target.improved_title == "現状維持":
                raise RuntimeError("改善タイトル案が現状維持または未取得")
            if post is None:
                raise RuntimeError("WordPress記事を現在タイトルで特定できません")

            post_id = str(post["id"])
            before_title = _rendered_title(post)
            if already_updated:
                after_title = before_title
                success = _normalize_title(before_title) == _normalize_title(target.improved_title)
            else:
                updated = client.update_post_title(int(post["id"]), target.improved_title)
                after_title = _rendered_title(updated)
                success = _normalize_title(after_title) == _normalize_title(target.improved_title)
                if not success:
                    error = "更新後タイトルが改善タイトル案と一致しません"
        except Exception as exc:
            error = str(exc)

        result_rows.append(
            {
                "優先順位": target.priority,
                "記事ID": post_id,
                "変更前": before_title,
                "変更後": after_title,
                "更新成功": "はい" if success else "いいえ",
                "更新失敗": "" if success else error or "未取得",
            }
        )

    _write_result(started_at, targets, result_rows)
    if result_rows and all(row["更新成功"] == "はい" for row in result_rows):
        _mark_backlog_measuring()

    print(f"TITLE_IMPROVEMENT_RESULT saved: {RESULT_PATH}")
    print(f"GO targets: {len(targets)}")
    print(f"success: {sum(1 for row in result_rows if row['更新成功'] == 'はい')}")
    print(f"failed: {sum(1 for row in result_rows if row['更新成功'] != 'はい')}")
    return 0 if result_rows and all(row["更新成功"] == "はい" for row in result_rows) else 1


class WordPressClient:
    def __init__(self, site_url: str, username: str, app_password: str):
        self.site_url = site_url.rstrip("/")
        credentials = f"{username}:{app_password}".encode("utf-8")
        self.authorization = "Basic " + base64.b64encode(credentials).decode("ascii")

    @classmethod
    def from_env(cls):
        site_url = os.getenv("P003_WORDPRESS_URL", "").strip()
        username = os.getenv("WORDPRESS_USERNAME", "").strip()
        app_password = os.getenv("WORDPRESS_APP_PASSWORD", "").strip()
        missing = [
            name
            for name, value in {
                "P003_WORDPRESS_URL": site_url,
                "WORDPRESS_USERNAME": username,
                "WORDPRESS_APP_PASSWORD": app_password,
            }.items()
            if not value
        ]
        if missing:
            raise RuntimeError("WordPress認証設定が未設定です: " + ", ".join(missing))
        return cls(site_url, username, app_password)

    def list_posts(self) -> List[Dict]:
        return self._request_json(
            "GET",
            "/wp-json/wp/v2/posts",
            {"per_page": "100", "orderby": "date", "order": "desc", "status": "publish", "context": "edit"},
        )

    def update_post_title(self, post_id: int, title: str) -> Dict:
        return self._request_json(
            "POST",
            f"/wp-json/wp/v2/posts/{post_id}",
            body={"title": title},
        )

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
            "User-Agent": "AI-COMPANY-P003-TITLE-IMPROVEMENT/1.0",
        }
        if body is not None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")

        request = Request(url, data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode(response.headers.get_content_charset() or "utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"WordPress API HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise RuntimeError(f"WordPress API connection error: {exc.reason}") from exc


def _load_go_targets(path: Path) -> List[TitleTarget]:
    rows = _parse_target_table(path.read_text(encoding="utf-8"))
    targets = []
    for row in rows:
        if row.get("編集長確認欄", "").strip() != "GO":
            continue
        targets.append(
            TitleTarget(
                priority=row.get("優先順位", "").strip(),
                current_title=row.get("現在タイトル", "").strip(),
                improved_title=row.get("改善タイトル案", "").strip(),
                reason=row.get("改善理由", "").strip(),
                search_intent=row.get("想定検索意図", "").strip(),
                expected_ctr=row.get("想定CTR改善", "").strip(),
                approval=row.get("編集長確認欄", "").strip(),
            )
        )
    return targets


def _parse_target_table(content: str) -> List[Dict[str, str]]:
    rows = []
    headers = []
    in_section = False
    for line in content.splitlines():
        clean = line.strip()
        if clean == "## タイトル改善案一覧":
            in_section = True
            continue
        if in_section and clean.startswith("## ") and clean != "## タイトル改善案一覧":
            break
        if not in_section or not clean.startswith("|"):
            continue
        cells = [cell.strip() for cell in clean.strip("|").split("|")]
        if not cells or all(set(cell) <= {"-", ":"} for cell in cells):
            continue
        if cells[0] == "優先順位":
            headers = cells
            continue
        if headers and len(cells) == len(headers):
            rows.append({headers[index]: cells[index] for index in range(len(headers))})
    return rows


def _build_title_index(posts: List[Dict]) -> Dict[str, Dict]:
    index = {}
    for post in posts:
        title = _rendered_title(post)
        if title:
            index[_normalize_title(title)] = post
    return index


def _rendered_title(post: Dict) -> str:
    title = post.get("title", {})
    if isinstance(title, dict):
        return _clean_text(title.get("raw") or title.get("rendered") or "")
    return _clean_text(str(title))


def _normalize_title(value: str) -> str:
    return " ".join(_clean_text(value).split())


def _clean_text(value: str) -> str:
    return html.unescape(value or "").replace("\xa0", " ").strip()


def _write_result(started_at: datetime, targets: List[TitleTarget], rows: List[Dict[str, str]]) -> None:
    success_count = sum(1 for row in rows if row["更新成功"] == "はい")
    failed_count = len(rows) - success_count
    lines = [
        "# TITLE IMPROVEMENT RESULT",
        "",
        "## 実行日時",
        "",
        started_at.isoformat(timespec="seconds"),
        "",
        "## 入力",
        "",
        "- `TITLE_IMPROVEMENT_PLAN.md`",
        "- `04_グラビア事業部/APPROVALS.md`",
        "",
        "## 判定ルール",
        "",
        "- 編集長確認欄が単独で`GO`の記事のみWordPressタイトル更新対象とする。",
        "- `STOP`、`要確認`、承認未確定の記事は更新しない。",
        "- 本文、カテゴリ、タグ、投稿状態、削除操作は変更しない。",
        "",
        "## Executive Summary",
        "",
        f"- GO対象記事: {len(targets)}件",
        f"- 更新成功: {success_count}件",
        f"- 更新失敗: {failed_count}件",
        "- WordPressタイトル更新: 実行" if targets else "- WordPressタイトル更新: 未実行",
        "- 本文変更: 未実行",
        "- カテゴリ変更: 未実行",
        "- タグ変更: 未実行",
        "- 投稿: 未実行",
        "- 削除: 未実行",
        "",
        "## 更新結果",
        "",
        "| 優先順位 | 記事ID | 変更前 | 変更後 | 更新成功 | 更新失敗 |",
        "|---:|---:|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| {優先順位} | {記事ID} | {変更前} | {変更後} | {更新成功} | {更新失敗} |".format(
                **{key: _clean_cell(value) for key, value in row.items()}
            )
        )
    lines.extend(
        [
            "",
            "## 制約確認",
            "",
            "- GO以外の更新: 未実行",
            "- WordPressタイトル更新: GO記事のみ実行",
            "- 本文変更: 未実行",
            "- カテゴリ変更: 未実行",
            "- タグ変更: 未実行",
            "- 投稿: 未実行",
            "- 削除: 未実行",
        ]
    )
    RESULT_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _mark_backlog_measuring() -> None:
    if not BACKLOG_PATH.exists():
        return
    content = BACKLOG_PATH.read_text(encoding="utf-8")
    lines = []
    for line in content.splitlines():
        if line.startswith("| 103 |"):
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if len(cells) >= 6:
                cells[3] = "効果測定中"
                cells[5] = "`TITLE_IMPROVEMENT_PLAN.md`のGO対象をWordPressタイトルへ反映済み。"
                line = "| " + " | ".join(cells) + " |"
        lines.append(line)
    BACKLOG_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _clean_cell(value: str) -> str:
    return str(value).replace("|", "｜").replace("\n", " ").strip() or "未取得"


def _load_env(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


if __name__ == "__main__":
    raise SystemExit(main())
