from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from core.wordpress_writer import WordPressWriteClient


@dataclass(frozen=True)
class ArticleQueueItem:
    article_id: str
    title: str
    content_file: str
    excerpt: str
    categories: List[str]
    tags: List[str]
    approval: str


def load_go_items(queue_path: Path) -> List[ArticleQueueItem]:
    rows = _parse_table(queue_path.read_text(encoding="utf-8") if queue_path.exists() else "")
    items = []
    for row in rows:
        approval = row.get("編集長確認欄", "").strip()
        if approval != "GO":
            continue
        items.append(
            ArticleQueueItem(
                article_id=row.get("ID", "").strip(),
                title=row.get("タイトル", "").strip(),
                content_file=row.get("本文ファイル", "").strip(),
                excerpt=row.get("抜粋", "").strip(),
                categories=_split_terms(row.get("カテゴリ", "")),
                tags=_split_terms(row.get("タグ", "")),
                approval=approval,
            )
        )
    return items


def create_drafts_from_queue(
    project_name: str,
    project_dir: Path,
    client: WordPressWriteClient,
    dry_run: bool = False,
) -> str:
    started_at = datetime.now()
    queue_path = project_dir / "ARTICLE_QUEUE.md"
    result_path = project_dir / "ARTICLE_DRAFT_RESULT.md"
    items = load_go_items(queue_path)
    rows = []

    for item in items:
        content_path = (project_dir / item.content_file).resolve()
        status = "DRY_RUN" if dry_run else "FAILED"
        post_id = "未作成"
        link = ""
        error = ""
        missing_categories: List[str] = []
        missing_tags: List[str] = []

        try:
            if not item.title:
                raise RuntimeError("タイトルが未入力です。")
            if not item.content_file:
                raise RuntimeError("本文ファイルが未入力です。")
            if not content_path.exists():
                raise RuntimeError(f"本文ファイルが見つかりません: {item.content_file}")
            content = content_path.read_text(encoding="utf-8").strip()
            if not content:
                raise RuntimeError(f"本文ファイルが空です: {item.content_file}")

            if dry_run:
                status = "DRY_RUN_OK"
            else:
                created = client.create_draft_post(
                    title=item.title,
                    content=content,
                    excerpt=item.excerpt,
                    categories=item.categories,
                    tags=item.tags,
                )
                post_id = str(created.post_id)
                link = created.link
                status = "SUCCESS" if created.status == "draft" else f"CREATED_{created.status}"
                missing_categories = created.missing_categories
                missing_tags = created.missing_tags
        except Exception as exc:
            error = str(exc)

        rows.append(
            {
                "ID": item.article_id or "未取得",
                "タイトル": item.title or "未取得",
                "本文ファイル": item.content_file or "未取得",
                "Post ID": post_id,
                "Status": status,
                "URL": link or "未取得",
                "未設定カテゴリ": ", ".join(missing_categories) if missing_categories else "なし",
                "未設定タグ": ", ".join(missing_tags) if missing_tags else "なし",
                "Error": error or "なし",
            }
        )

    result_path.write_text(_format_result(project_name, started_at, dry_run, rows), encoding="utf-8")
    return str(result_path)


def _parse_table(content: str) -> List[Dict[str, str]]:
    rows = []
    headers = []
    for line in content.splitlines():
        clean = line.strip()
        if not clean.startswith("|"):
            continue
        cells = [cell.strip() for cell in clean.strip("|").split("|")]
        if not cells or all(set(cell) <= {"-", ":"} for cell in cells):
            continue
        if cells[0] == "ID":
            headers = cells
            continue
        if headers and len(cells) == len(headers):
            rows.append(dict(zip(headers, cells)))
    return rows


def _split_terms(value: str) -> List[str]:
    return [item.strip() for item in str(value).replace("、", ",").split(",") if item.strip()]


def _format_result(project_name: str, started_at: datetime, dry_run: bool, rows: List[Dict[str, str]]) -> str:
    lines = [
        "# ARTICLE DRAFT RESULT",
        "",
        f"- Project: {project_name}",
        f"- Started At: {started_at.isoformat(timespec='seconds')}",
        f"- Mode: {'DRY_RUN' if dry_run else 'CREATE_DRAFT'}",
        f"- GO対象: {len(rows)}件",
        "",
        "## Result",
        "",
        "| ID | タイトル | 本文ファイル | Post ID | Status | URL | 未設定カテゴリ | 未設定タグ | Error |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    if not rows:
        lines.append("| 未取得 | 未取得 | 未取得 | 未作成 | NO_GO_TARGET | 未取得 | なし | なし | GO対象なし |")
    for row in rows:
        lines.append(
            "| {ID} | {タイトル} | {本文ファイル} | {Post ID} | {Status} | {URL} | {未設定カテゴリ} | {未設定タグ} | {Error} |".format(
                **{key: _clean(value) for key, value in row.items()}
            )
        )
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- WordPress作成ステータスは`draft`のみ。",
            "- 公開は行わない。",
            "- 既存記事の更新は行わない。",
            "- 削除は行わない。",
            "- カテゴリ・タグの新規作成は行わない。",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _clean(value: str) -> str:
    return str(value).replace("|", "｜").replace("\n", " ").strip() or "なし"
