import base64
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
PLAN_PATH = PROJECT_DIR / "CATEGORY_FIX_PLAN.md"
RESULT_PATH = PROJECT_DIR / "CATEGORY_FIX_RESULT.md"


@dataclass(frozen=True)
class CategoryFixTarget:
    priority: str
    post_id: int
    title: str
    url: str
    current_category: str
    recommended_category: str
    approval: str


def main() -> int:
    _load_env(WORKSPACE_ROOT / ".env")
    started_at = datetime.now()
    targets = _load_go_targets(PLAN_PATH)
    result_rows = []

    client = WordPressClient.from_env()
    categories = client.list_categories()
    category_name_to_id = {item["name"]: int(item["id"]) for item in categories}

    for target in targets:
        before_categories: List[str] = []
        after_categories: List[str] = []
        success = False
        error = ""
        recommended_id = category_name_to_id.get(target.recommended_category)

        try:
            post_before = client.get_post(target.post_id)
            before_categories = _category_names(
                post_before.get("categories", []), categories
            )
            if not recommended_id:
                raise RuntimeError(
                    f"推奨カテゴリがWordPressに存在しません: {target.recommended_category}"
                )

            if target.approval != "GO":
                raise RuntimeError("GO以外のため未実行")

            post_after = client.update_post_categories(
                target.post_id, [recommended_id]
            )
            after_categories = _category_names(
                post_after.get("categories", []), categories
            )
            success = target.recommended_category in after_categories
            if not success:
                error = "更新後カテゴリに推奨カテゴリが含まれていません"
        except Exception as exc:
            error = str(exc)

        result_rows.append(
            {
                "優先順位": target.priority,
                "記事ID": str(target.post_id),
                "記事名": target.title,
                "変更前": ", ".join(before_categories) or target.current_category or "未取得",
                "変更後": ", ".join(after_categories)
                or target.recommended_category
                or "未取得",
                "更新成功": "はい" if success else "いいえ",
                "更新失敗": "" if success else error or "未取得",
            }
        )

    RESULT_PATH.write_text(
        _format_result(started_at, targets, result_rows), encoding="utf-8"
    )
    print(f"CATEGORY_FIX_RESULT saved: {RESULT_PATH}")
    print(f"GO targets: {len(targets)}")
    print(f"success: {sum(1 for row in result_rows if row['更新成功'] == 'はい')}")
    print(f"failed: {sum(1 for row in result_rows if row['更新成功'] != 'はい')}")
    return 0 if all(row["更新成功"] == "はい" for row in result_rows) else 1


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

    def list_categories(self) -> List[Dict]:
        return self._request_json(
            "GET",
            "/wp-json/wp/v2/categories",
            {"per_page": "100", "hide_empty": "false"},
        )

    def get_post(self, post_id: int) -> Dict:
        return self._request_json(
            "GET",
            f"/wp-json/wp/v2/posts/{post_id}",
            {"context": "edit"},
        )

    def update_post_categories(self, post_id: int, category_ids: List[int]) -> Dict:
        return self._request_json(
            "POST",
            f"/wp-json/wp/v2/posts/{post_id}",
            body={"categories": category_ids},
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
            "User-Agent": "AI-COMPANY-P003-CATEGORY-FIX/1.0",
        }
        if body is not None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")

        request = Request(url, data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=30) as response:
                return json.loads(
                    response.read().decode(
                        response.headers.get_content_charset() or "utf-8"
                    )
                )
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"WordPress API HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise RuntimeError(f"WordPress API connection error: {exc.reason}") from exc


def _load_go_targets(path: Path) -> List[CategoryFixTarget]:
    rows = _parse_target_table(path.read_text(encoding="utf-8"))
    targets = []
    for row in rows:
        if row.get("編集長確認欄", "").strip() != "GO":
            continue
        targets.append(
            CategoryFixTarget(
                priority=row.get("優先順位", "").strip(),
                post_id=int(row.get("記事ID", "0").strip()),
                title=row.get("対象記事", "").strip(),
                url=row.get("URL", "").strip(),
                current_category=row.get("現在カテゴリ", "").strip(),
                recommended_category=row.get("推奨カテゴリ", "").strip(),
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
        if clean == "## 対象記事一覧":
            in_section = True
            continue
        if in_section and clean.startswith("## ") and clean != "## 対象記事一覧":
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


def _category_names(category_ids, categories: List[Dict]) -> List[str]:
    id_to_name = {int(item["id"]): item["name"] for item in categories}
    return [id_to_name.get(int(category_id), f"未取得:{category_id}") for category_id in category_ids]


def _format_result(started_at: datetime, targets, rows: List[Dict[str, str]]) -> str:
    success_count = sum(1 for row in rows if row["更新成功"] == "はい")
    failed_count = len(rows) - success_count
    lines = [
        "# CATEGORY FIX RESULT",
        "",
        "## 実行日時",
        "",
        started_at.isoformat(timespec="seconds"),
        "",
        "## 入力",
        "",
        "- `CATEGORY_FIX_PLAN.md`",
        "- `04_グラビア事業部/APPROVALS.md`",
        "",
        "## 判定ルール",
        "",
        "- 編集長確認欄が単独で`GO`の記事のみWordPressカテゴリ更新対象とする。",
        "- `STOP`、`要確認`、承認未確定の記事は更新しない。",
        "- タイトル、本文、タグ、投稿状態、削除操作は変更しない。",
        "",
        "## Executive Summary",
        "",
        f"- GO対象記事: {len(targets)}件",
        f"- 更新成功: {success_count}件",
        f"- 更新失敗: {failed_count}件",
        "- WordPressカテゴリ更新: 実行",
        "- タイトル変更: 未実行",
        "- 本文変更: 未実行",
        "- 投稿: 未実行",
        "- 削除: 未実行",
        "",
        "## 更新結果",
        "",
        "| 優先順位 | 記事ID | 記事名 | 変更前 | 変更後 | 更新成功 | 更新失敗 |",
        "|---:|---:|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| {優先順位} | {記事ID} | {記事名} | {変更前} | {変更後} | {更新成功} | {更新失敗} |".format(
                **{key: _clean_cell(value) for key, value in row.items()}
            )
        )

    lines.extend(
        [
            "",
            "## 制約確認",
            "",
            "- GO以外の更新: 未実行",
            "- WordPressカテゴリ更新: GO記事のみ実行",
            "- タイトル変更: 未実行",
            "- 本文変更: 未実行",
            "- 投稿: 未実行",
            "- 削除: 未実行",
            "",
            "## 次アクション",
            "",
            "- 変更後のカテゴリ傾向を次回P003 REPORTで確認する。",
            "- Search Console / GA4の取得が可能になり次第、カテゴリ整理後の効果測定へ進む。",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _clean_cell(value: str) -> str:
    return str(value or "").replace("|", "/").replace("\n", " ").strip()


def _load_env(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


if __name__ == "__main__":
    raise SystemExit(main())
