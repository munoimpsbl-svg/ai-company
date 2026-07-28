from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PIL import Image


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
DEFAULT_DB_PATH = Path("03_SNS事業部") / "03_Analytics" / "generation_quality.sqlite3"
DEFAULT_REPORT_PATH = (
    Path("03_SNS事業部") / "03_Analytics" / "GENERATION_QUALITY_REPORT.md"
)
GENERATION_ENGINE = "gpt_image"


@dataclass(frozen=True)
class QualityAsset:
    path: Path
    experiment_path: Path
    engine: str
    output_date: str
    character: str
    slot: str
    width: int
    height: int
    score: int
    status: str
    warnings: tuple[str, ...]
    exif_cleaned: bool
    has_report: bool
    has_prompt: bool
    adopted_hint: bool


@dataclass(frozen=True)
class QualitySummary:
    status: str
    db_path: Path
    report_path: Path
    scanned_assets: int
    experiments: int
    average_score: float
    blockers: tuple[str, ...]
    top_assets: tuple[QualityAsset, ...]
    warning_assets: tuple[QualityAsset, ...]


def update_generation_quality(
    workspace_root: Path,
    output_date: str | None = None,
    db_path: Path | None = None,
    report_path: Path | None = None,
) -> QualitySummary:
    root = workspace_root.resolve()
    absolute_db_path = _absolute(root, db_path or DEFAULT_DB_PATH)
    absolute_report_path = _absolute(root, report_path or DEFAULT_REPORT_PATH)
    assets = tuple(_scan_assets(root, output_date))

    absolute_db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(absolute_db_path) as connection:
        connection.row_factory = sqlite3.Row
        _ensure_schema(connection)
        _replace_assets(connection, root, assets, output_date)
        rows = connection.execute(
            """
            SELECT * FROM generation_assets
            ORDER BY output_date DESC, character ASC, slot ASC, score DESC
            """
        ).fetchall()

    db_assets = tuple(_asset_from_row(root, row) for row in rows)
    summary = _build_summary(root, absolute_db_path, absolute_report_path, db_assets)
    absolute_report_path.parent.mkdir(parents=True, exist_ok=True)
    absolute_report_path.write_text(_format_report(root, summary), encoding="utf-8")
    return summary


def load_generation_quality(
    workspace_root: Path,
    db_path: Path | None = None,
) -> QualitySummary:
    root = workspace_root.resolve()
    absolute_db_path = _absolute(root, db_path or DEFAULT_DB_PATH)
    absolute_report_path = _absolute(root, DEFAULT_REPORT_PATH)
    if not absolute_db_path.exists():
        return QualitySummary(
            status="未取得",
            db_path=absolute_db_path,
            report_path=absolute_report_path,
            scanned_assets=0,
            experiments=0,
            average_score=0.0,
            blockers=(f"品質DBがありません: {absolute_db_path}",),
            top_assets=(),
            warning_assets=(),
        )

    with sqlite3.connect(absolute_db_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT * FROM generation_assets
            ORDER BY output_date DESC, character ASC, slot ASC, score DESC
            """
        ).fetchall()

    assets = tuple(_asset_from_row(root, row) for row in rows)
    return _build_summary(root, absolute_db_path, absolute_report_path, assets)


def _scan_assets(root: Path, output_date: str | None) -> list[QualityAsset]:
    output_root = root / "02_Daily_Output"
    if not output_root.exists():
        return []

    date_dirs = [
        path
        for path in output_root.iterdir()
        if path.is_dir() and (output_date is None or path.name == output_date)
    ]
    assets = []
    for date_dir in sorted(date_dirs):
        for image_path in sorted(date_dir.rglob("*")):
            if not image_path.is_file() or image_path.suffix.lower() not in IMAGE_EXTENSIONS:
                continue
            if image_path.name.startswith(".") or image_path.name.startswith("CONTACT_SHEET"):
                continue
            parsed = _parse_output_path(root, image_path)
            if not parsed:
                continue
            character, slot, experiment_path = parsed
            assets.append(
                _evaluate_asset(
                    root=root,
                    image_path=image_path,
                    experiment_path=experiment_path,
                    output_date=date_dir.name,
                    character=character,
                    slot=slot,
                )
            )
    return assets


def _parse_output_path(root: Path, image_path: Path):
    relative = image_path.relative_to(root)
    parts = relative.parts
    if len(parts) < 4 or parts[0] != "02_Daily_Output":
        return None
    character = parts[2]
    if character not in {"MIKU", "RIO"}:
        return None
    if len(parts) >= 6 and parts[-2] == "images":
        slot = parts[3]
        experiment_path = root.joinpath(*parts[:-2])
    elif len(parts) >= 5 and parts[3] == "images":
        slot = "default"
        experiment_path = root.joinpath(*parts[:3])
    else:
        slot = parts[3] if len(parts) >= 5 else "default"
        experiment_path = image_path.parent
    return character, slot, experiment_path


def _evaluate_asset(
    root: Path,
    image_path: Path,
    experiment_path: Path,
    output_date: str,
    character: str,
    slot: str,
) -> QualityAsset:
    report_text = _read_optional(experiment_path / "report.md")
    prompt_text = _read_optional(experiment_path / "prompt.txt")
    warnings: list[str] = []
    score = 50
    width = 0
    height = 0
    exif_cleaned = False

    try:
        with Image.open(image_path) as image:
            width, height = image.size
            exif_cleaned = not bool(image.getexif()) or _marker_path(image_path).exists()
        score += 15
    except Exception as exc:
        warnings.append(f"画像を開けません: {exc}")
        score -= 40

    if min(width, height) >= 768 and max(width, height) >= 1024:
        score += 10
    elif width and height:
        warnings.append(f"解像度が低い可能性: {width}x{height}")
        score -= 8

    if width and height:
        ratio = width / height
        if 0.55 <= ratio <= 1.35:
            score += 5
        else:
            warnings.append(f"SNS候補として画角確認: {width}x{height}")

    if report_text:
        score += 8
    else:
        warnings.append("report.md未取得")
        score -= 8

    if prompt_text:
        score += 6
    else:
        warnings.append("prompt.txt未取得")
        score -= 6

    if _has_post_text(experiment_path):
        score += 4

    adopted_hint = _has_adopted_hint(report_text, image_path.name)
    if adopted_hint:
        score += 8

    if exif_cleaned:
        score += 6
    else:
        warnings.append("EXIF削除マーカーまたはEXIF削除状態を確認")
        score -= 10

    score += _report_penalty(report_text, warnings)

    score = max(0, min(100, score))
    status = "review" if warnings or score < 70 else "ok"
    if score < 45:
        status = "ng"

    return QualityAsset(
        path=image_path,
        experiment_path=experiment_path,
        engine=GENERATION_ENGINE,
        output_date=output_date,
        character=character,
        slot=slot,
        width=width,
        height=height,
        score=score,
        status=status,
        warnings=tuple(warnings),
        exif_cleaned=exif_cleaned,
        has_report=bool(report_text),
        has_prompt=bool(prompt_text),
        adopted_hint=adopted_hint,
    )


def _report_penalty(report_text: str, warnings: list[str]) -> int:
    if not report_text:
        return 0
    normalized = report_text.replace("物理破綻なし", "").replace("破綻なし", "")
    checks = (
        ("完全破綻", -40, "完全破綻の記録あり"),
        ("別人感", -20, "別人感の記録あり"),
        ("顔が違", -20, "本人感ズレの記録あり"),
        ("不自然", -12, "不自然表現の記録あり"),
        ("室内で靴", -15, "室内靴の記録あり"),
        ("左ハンドル", -18, "車内ハンドル位置の記録あり"),
        ("ImageOptim: 実行予定", -10, "ImageOptim未完了の記録あり"),
        ("EXIF削除: 未", -15, "EXIF削除未完了の記録あり"),
    )
    penalty = 0
    for keyword, value, warning in checks:
        if _has_problem_keyword(normalized, keyword):
            warnings.append(warning)
            penalty += value
    if _has_problem_pair(normalized, "文字", "破綻"):
        warnings.append("背景文字破綻の記録あり")
        penalty -= 15
    return penalty


def _has_problem_keyword(text: str, keyword: str) -> bool:
    return any(
        keyword in line and not _is_negative_problem_line(line)
        for line in text.splitlines()
    )


def _has_problem_pair(text: str, first: str, second: str) -> bool:
    return any(
        first in line and second in line and not _is_negative_problem_line(line)
        for line in text.splitlines()
    )


def _is_negative_problem_line(line: str) -> bool:
    negative_markers = (
        "なし",
        "ない",
        "避ける",
        "しない",
        "禁止",
        "済み",
        "OK",
        "ok",
        "No ",
        "no ",
    )
    return any(marker in line for marker in negative_markers)


def _ensure_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS generation_assets (
            path TEXT PRIMARY KEY,
            experiment_path TEXT NOT NULL,
            engine TEXT NOT NULL DEFAULT 'gpt_image',
            output_date TEXT NOT NULL,
            character TEXT NOT NULL,
            slot TEXT NOT NULL,
            width INTEGER NOT NULL,
            height INTEGER NOT NULL,
            score INTEGER NOT NULL,
            status TEXT NOT NULL,
            warnings TEXT NOT NULL,
            exif_cleaned INTEGER NOT NULL,
            has_report INTEGER NOT NULL,
            has_prompt INTEGER NOT NULL,
            adopted_hint INTEGER NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_generation_assets_date
        ON generation_assets(output_date, character, slot);

        CREATE TABLE IF NOT EXISTS generation_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_path TEXT NOT NULL,
            decision TEXT NOT NULL,
            memo TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """
    )
    _ensure_column(
        connection,
        "generation_assets",
        "engine",
        "TEXT NOT NULL DEFAULT 'gpt_image'",
    )


def _replace_assets(
    connection: sqlite3.Connection,
    root: Path,
    assets: tuple[QualityAsset, ...],
    output_date: str | None,
) -> None:
    if output_date:
        connection.execute(
            "DELETE FROM generation_assets WHERE output_date = ?",
            (output_date,),
        )
    else:
        connection.execute("DELETE FROM generation_assets")
    now = datetime.now().isoformat(timespec="seconds")
    rows = [
        (
            _relative(root, asset.path),
            _relative(root, asset.experiment_path),
            asset.engine,
            asset.output_date,
            asset.character,
            asset.slot,
            asset.width,
            asset.height,
            asset.score,
            asset.status,
            "\n".join(asset.warnings),
            int(asset.exif_cleaned),
            int(asset.has_report),
            int(asset.has_prompt),
            int(asset.adopted_hint),
            now,
        )
        for asset in assets
    ]
    connection.executemany(
        """
        INSERT INTO generation_assets (
            path, experiment_path, engine, output_date, character, slot,
            width, height, score, status, warnings,
            exif_cleaned, has_report, has_prompt, adopted_hint, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )


def _build_summary(
    root: Path,
    db_path: Path,
    report_path: Path,
    assets: tuple[QualityAsset, ...],
) -> QualitySummary:
    blockers = []
    if not assets:
        blockers.append("画像候補が未取得です。")
    warning_assets = tuple(
        sorted(
            (asset for asset in assets if asset.status != "ok"),
            key=lambda asset: (asset.score, str(asset.path)),
        )[:20]
    )
    top_assets = tuple(
        sorted(assets, key=lambda asset: (asset.score, str(asset.path)), reverse=True)[:20]
    )
    if warning_assets:
        blockers.append(f"要確認候補: {len(warning_assets)}件")
    average = round(sum(asset.score for asset in assets) / len(assets), 1) if assets else 0.0
    return QualitySummary(
        status="正常" if assets else "未取得",
        db_path=db_path,
        report_path=report_path,
        scanned_assets=len(assets),
        experiments=len({asset.experiment_path for asset in assets}),
        average_score=average,
        blockers=tuple(blockers),
        top_assets=top_assets,
        warning_assets=warning_assets,
    )


def _format_report(root: Path, summary: QualitySummary) -> str:
    return "\n".join(
        [
            "# GENERATION QUALITY REPORT",
            "",
            f"更新日時: {datetime.now().isoformat(timespec='seconds')}",
            "",
            "## Summary",
            "",
            f"- Status: {summary.status}",
            f"- Scanned assets: {summary.scanned_assets}",
            f"- Experiments: {summary.experiments}",
            f"- Average score: {summary.average_score}",
            f"- DB: `{_relative(root, summary.db_path)}`",
            f"- Generation engine: `{GENERATION_ENGINE}`",
            "",
            "## Blocker",
            "",
            _format_blockers(summary.blockers),
            "",
            "## Top Candidates",
            "",
            _format_assets(root, summary.top_assets),
            "",
            "## Review Required",
            "",
            _format_assets(root, summary.warning_assets),
            "",
            "## Notes",
            "",
            "- スコアは自動採用判定ではない。",
            "- 本人感、体型、構図、最終安全判定は社長判断を優先する。",
            "- 評価対象はGPT画像生成の候補。画像寸法、EXIF、report.md、prompt.txt、既知NG記録を評価する。",
            "",
        ]
    )


def _format_blockers(blockers: tuple[str, ...]) -> str:
    if not blockers:
        return "- なし"
    return "\n".join(f"- {blocker}" for blocker in blockers)


def _format_assets(root: Path, assets: tuple[QualityAsset, ...]) -> str:
    if not assets:
        return "- なし"
    lines = [
        "| score | status | date | character | slot | image | warnings |",
        "| ---: | --- | --- | --- | --- | --- | --- |",
    ]
    for asset in assets:
        warnings = "<br>".join(_clean_cell(warning) for warning in asset.warnings) or "-"
        lines.append(
            "| {score} | {status} | {date} | {character} | {slot} | `{path}` | {warnings} |".format(
                score=asset.score,
                status=asset.status,
                date=asset.output_date,
                character=asset.character,
                slot=asset.slot,
                path=_relative(root, asset.path),
                warnings=warnings,
            )
        )
    return "\n".join(lines)


def _asset_from_row(root: Path, row: sqlite3.Row) -> QualityAsset:
    return QualityAsset(
        path=root / row["path"],
        experiment_path=root / row["experiment_path"],
        engine=row["engine"] if "engine" in row.keys() else GENERATION_ENGINE,
        output_date=row["output_date"],
        character=row["character"],
        slot=row["slot"],
        width=row["width"],
        height=row["height"],
        score=row["score"],
        status=row["status"],
        warnings=tuple(filter(None, row["warnings"].splitlines())),
        exif_cleaned=bool(row["exif_cleaned"]),
        has_report=bool(row["has_report"]),
        has_prompt=bool(row["has_prompt"]),
        adopted_hint=bool(row["adopted_hint"]),
    )


def _has_adopted_hint(report_text: str, filename: str) -> bool:
    if not report_text:
        return False
    stem = Path(filename).stem
    return ("採用候補" in report_text or "優先候補" in report_text) and (
        filename in report_text or stem[-2:] in report_text
    )


def _has_post_text(path: Path) -> bool:
    return any((path / filename).exists() for filename in ("instagram.txt", "x.txt", "threads.txt"))


def _ensure_column(
    connection: sqlite3.Connection,
    table_name: str,
    column_name: str,
    definition: str,
) -> None:
    columns = {
        row[1]
        for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    }
    if column_name not in columns:
        connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")


def _read_optional(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8") if path.exists() else ""
    except OSError:
        return ""


def _marker_path(path: Path) -> Path:
    return path.with_name(f"{path.name}.exifcleaned")


def _absolute(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def _relative(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root))
    except (OSError, ValueError):
        return str(path)


def _clean_cell(value: str) -> str:
    return value.replace("|", "/").replace("\n", " ").strip()
