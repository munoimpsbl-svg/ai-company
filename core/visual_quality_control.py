from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Iterable

from PIL import Image, ImageFilter, ImageStat


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
STATUSES = {"PASS", "REVIEW", "FAIL"}


@dataclass(frozen=True)
class VQCScores:
    person: int
    object: int
    background: int
    photo_quality: int
    character_consistency: int

    @property
    def average(self) -> float:
        return round(mean(asdict(self).values()), 1)

    @property
    def minimum(self) -> int:
        return min(asdict(self).values())


@dataclass(frozen=True)
class VQCMetrics:
    width: int
    height: int
    megapixels: float
    aspect_ratio: float
    file_size_bytes: int
    bytes_per_megapixel: int
    exif_cleaned: bool
    luminance_min: int
    luminance_max: int
    luminance_range: int
    luminance_mean: float
    luminance_stddev: float
    edge_mean: float
    context_chars: int
    problem_marker_lines: int
    person_problem_hits: int
    object_problem_hits: int
    background_problem_hits: int
    consistency_problem_hits: int
    resolution_component: int
    aspect_ratio_component: int
    file_size_component: int
    contrast_component: int
    edge_component: int
    exif_component: int


@dataclass(frozen=True)
class VQCReport:
    file_name: str
    source_path: str
    character: str
    status: str
    scores: VQCScores
    identity_review_required: bool = True
    identity_review_score: int | None = None
    identity_review_source: str = ""
    identity_review_items: dict[str, bool] = field(default_factory=dict)
    metrics: VQCMetrics | None = None
    critical_errors: tuple[str, ...] = ()
    person_findings: tuple[str, ...] = ()
    object_findings: tuple[str, ...] = ()
    background_findings: tuple[str, ...] = ()
    photo_quality_findings: tuple[str, ...] = ()
    character_consistency_findings: tuple[str, ...] = ()
    retry_required: bool = False
    retry_instruction: str = ""
    audited_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))


@dataclass(frozen=True)
class VQCBatchSummary:
    character: str
    output_date: str
    source_dir: str
    total_images: int
    pass_count: int
    review_count: int
    fail_count: int
    minimum_pass_required: int
    ready_for_post_preparation: bool
    reports: tuple[VQCReport, ...]
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))


def run_visual_quality_control(
    workspace_root: Path,
    output_date: str,
    character: str = "MIKU",
    slot: str | None = None,
    minimum_pass_required: int = 3,
    copy_images: bool = True,
) -> VQCBatchSummary:
    root = workspace_root.expanduser().resolve()
    character = character.upper()
    source_dir = root / "02_Daily_Output" / output_date / character
    if slot:
        source_dir = source_dir / slot
    if not source_dir.exists():
        raise FileNotFoundError(f"監査対象フォルダが見つかりません: {source_dir}")

    images = tuple(_iter_candidate_images(source_dir))
    reports = tuple(
        audit_image(
            workspace_root=root,
            image_path=image_path,
            character=character,
            source_dir=source_dir,
        )
        for image_path in images
    )

    _write_reports(source_dir, reports)
    if copy_images:
        _copy_images_by_status(root, source_dir, reports)

    summary = VQCBatchSummary(
        character=character,
        output_date=output_date,
        source_dir=_relative(root, source_dir),
        total_images=len(reports),
        pass_count=sum(1 for report in reports if report.status == "PASS"),
        review_count=sum(1 for report in reports if report.status == "REVIEW"),
        fail_count=sum(1 for report in reports if report.status == "FAIL"),
        minimum_pass_required=minimum_pass_required,
        ready_for_post_preparation=sum(1 for report in reports if report.status == "PASS")
        >= minimum_pass_required,
        reports=reports,
    )
    _write_batch_summary(source_dir, summary)
    return summary


def audit_image(
    workspace_root: Path,
    image_path: Path,
    character: str,
    source_dir: Path | None = None,
) -> VQCReport:
    root = workspace_root.expanduser().resolve()
    image_path = image_path.expanduser().resolve()
    source_dir = source_dir.expanduser().resolve() if source_dir else image_path.parent.parent
    context_text = _collect_context_text(source_dir, image_path)

    person_score = 92
    object_score = 92
    background_score = 92
    photo_quality_score = 92
    consistency_score = 90

    critical_errors: list[str] = []
    person_findings: list[str] = []
    object_findings: list[str] = []
    background_findings: list[str] = []
    photo_quality_findings: list[str] = []
    consistency_findings: list[str] = []

    try:
        with Image.open(image_path) as image:
            width, height = image.size
            file_size = image_path.stat().st_size
            exif_cleaned = not bool(image.getexif()) or _marker_path(image_path).exists()
            grayscale = image.convert("L")
            stat = ImageStat.Stat(grayscale)
            extrema = stat.extrema[0]
            luminance_mean = round(stat.mean[0], 2)
            luminance_stddev = round(stat.stddev[0], 2)
            edge_mean = round(ImageStat.Stat(grayscale.filter(ImageFilter.FIND_EDGES)).mean[0], 2)
    except Exception as exc:
        critical_errors.append(f"画像を開けません: {exc}")
        return _build_report(
            root,
            image_path,
            character,
            VQCScores(0, 0, 0, 0, 0),
            critical_errors,
            person_findings,
            object_findings,
            background_findings,
            photo_quality_findings,
            consistency_findings,
            None,
        )

    person_problem_hits = _count_problem_hits(context_text, _person_problem_keywords())
    object_problem_hits = _count_problem_hits(context_text, _object_problem_keywords())
    background_problem_hits = _count_problem_hits(context_text, _background_problem_keywords())
    consistency_problem_hits = _count_problem_hits(
        context_text,
        _consistency_problem_keywords(character),
    )
    identity_review = _load_identity_review(source_dir, image_path)
    identity_score, identity_items, identity_source = _identity_review_parts(identity_review)
    marker_lines = _count_problem_marker_lines(context_text)
    resolution_component = _resolution_component(width, height)
    aspect_ratio = width / height
    aspect_ratio_component = _aspect_ratio_component(aspect_ratio)
    file_size_component = _file_size_component(file_size, width, height)
    contrast_component = _contrast_component(extrema[1] - extrema[0], luminance_stddev)
    edge_component = _edge_component(edge_mean)
    exif_component = 100 if exif_cleaned else 65

    person_score += _apply_keyword_penalties(
        context_text,
        _person_problem_keywords(),
        person_findings,
        critical_errors,
    )
    object_score += _apply_keyword_penalties(
        context_text,
        _object_problem_keywords(),
        object_findings,
        critical_errors,
    )
    background_score += _apply_keyword_penalties(
        context_text,
        _background_problem_keywords(),
        background_findings,
        critical_errors,
    )
    consistency_score += _apply_keyword_penalties(
        context_text,
        _consistency_problem_keywords(character),
        consistency_findings,
        critical_errors,
    )

    if identity_score is None:
        person_score -= 22
        consistency_score -= 18
        person_findings.append("本人感の目視レビュー未記録: 自動PASS禁止")
        consistency_findings.append("identity_review.json または画像別_notes.jsonで本人感点数が未入力")
    else:
        person_score = min(person_score, identity_score)
        if identity_score < 65:
            critical_errors.append(f"本人感スコア重大NG: {identity_score}")
            person_findings.append(f"本人感スコア重大NG: {identity_score}")
        elif identity_score < 80:
            person_score -= 12
            person_findings.append(f"本人感スコア要再確認: {identity_score}")
        elif identity_score < 88:
            person_score -= 5
            person_findings.append(f"本人感スコア採用前確認: {identity_score}")
        else:
            person_findings.append(f"本人感スコアOK: {identity_score}")

    required_identity_checks = (
        "base_reference_used",
        "face_matches_base",
        "age_matches",
        "hair_matches",
        "body_matches",
        "outfit_reference_limited_to_clothes",
    )
    for key in required_identity_checks:
        if identity_items.get(key) is False:
            person_score -= 18
            consistency_score -= 12
            person_findings.append(f"本人感レビューNG: {key}=false")
            if key in {"base_reference_used", "face_matches_base"}:
                critical_errors.append(f"本人感レビュー重大NG: {key}=false")

    photo_quality_score = round(
        mean(
            (
                resolution_component,
                aspect_ratio_component,
                file_size_component,
                contrast_component,
                edge_component,
                exif_component,
            )
        )
    )

    if resolution_component < 80:
        photo_quality_score -= 14
        photo_quality_findings.append(f"解像度確認: {width}x{height}")
    else:
        photo_quality_findings.append(f"解像度OK: {width}x{height} / component={resolution_component}")

    if aspect_ratio_component < 80:
        photo_quality_score -= 6
        photo_quality_findings.append(
            f"SNS候補として画角確認: ratio={aspect_ratio:.3f} / component={aspect_ratio_component}"
        )

    if not exif_cleaned:
        photo_quality_score -= 12
        photo_quality_findings.append(f"EXIF削除状態またはマーカーを確認 / component={exif_component}")
    else:
        photo_quality_findings.append(f"EXIF削除済み / component={exif_component}")

    if file_size_component < 80:
        photo_quality_score -= 8
        photo_quality_findings.append(
            f"ファイルサイズ確認: {file_size} bytes / component={file_size_component}"
        )

    if contrast_component < 80:
        photo_quality_score -= 5
        photo_quality_findings.append(
            f"明暗差確認: range={extrema[1] - extrema[0]}, stddev={luminance_stddev} / component={contrast_component}"
        )

    if edge_component < 75:
        photo_quality_score -= 4
        photo_quality_findings.append(
            f"エッジ量確認: edge_mean={edge_mean} / component={edge_component}"
        )

    if not context_text.strip():
        consistency_score -= 8
        consistency_findings.append("prompt/report等の監査根拠テキストが未取得")

    if character == "MIKU" and "マスク" not in context_text:
        consistency_score -= 10
        consistency_findings.append("MIKU必須のマスク確認根拠が不足")

    manual_visual_checks = {
        "physical_integrity_ok": ("person", "身体・手足・首肩・膝足先の破綻チェック"),
        "hands_limbs_ok": ("person", "手指・腕・脚の接続チェック"),
        "selfie_logic_ok": ("object", "自撮り時のスマホ・腕・反射整合性チェック"),
        "outfit_continuity_ok": ("consistency", "同一シリーズ内の服装・髪型・小物連動チェック"),
        "background_text_logo_ok": ("background", "背景文字・ロゴ・固有名詞チェック"),
        "scene_physics_ok": ("background", "場所・器具・家具・床・鏡の物理整合性チェック"),
        "lighting_ok": ("photo_quality", "場面に対する明るさ・露出チェック"),
    }
    for key, (category, label) in manual_visual_checks.items():
        value = identity_items.get(key)
        if value is True:
            continue
        if value is None:
            finding = f"目視破綻レビュー未入力: {label}"
            penalty = 12
        else:
            finding = f"目視破綻レビューNG: {label}"
            penalty = 28
            if key in {"physical_integrity_ok", "hands_limbs_ok", "selfie_logic_ok", "scene_physics_ok"}:
                critical_errors.append(finding)
        if category == "person":
            person_score -= penalty
            person_findings.append(finding)
        elif category == "object":
            object_score -= penalty
            object_findings.append(finding)
        elif category == "background":
            background_score -= penalty
            background_findings.append(finding)
        elif category == "photo_quality":
            photo_quality_score -= penalty
            photo_quality_findings.append(finding)
        else:
            consistency_score -= penalty
            consistency_findings.append(finding)

    scores = VQCScores(
        person=_clamp(person_score),
        object=_clamp(object_score),
        background=_clamp(background_score),
        photo_quality=_clamp(photo_quality_score),
        character_consistency=_clamp(consistency_score),
    )
    metrics = VQCMetrics(
        width=width,
        height=height,
        megapixels=round((width * height) / 1_000_000, 2),
        aspect_ratio=round(aspect_ratio, 3),
        file_size_bytes=file_size,
        bytes_per_megapixel=round(file_size / max((width * height) / 1_000_000, 0.01)),
        exif_cleaned=exif_cleaned,
        luminance_min=extrema[0],
        luminance_max=extrema[1],
        luminance_range=extrema[1] - extrema[0],
        luminance_mean=luminance_mean,
        luminance_stddev=luminance_stddev,
        edge_mean=edge_mean,
        context_chars=len(context_text),
        problem_marker_lines=marker_lines,
        person_problem_hits=person_problem_hits,
        object_problem_hits=object_problem_hits,
        background_problem_hits=background_problem_hits,
        consistency_problem_hits=consistency_problem_hits,
        resolution_component=resolution_component,
        aspect_ratio_component=aspect_ratio_component,
        file_size_component=file_size_component,
        contrast_component=contrast_component,
        edge_component=edge_component,
        exif_component=exif_component,
    )
    return _build_report(
        root,
        image_path,
        character,
        scores,
        critical_errors,
        person_findings or ("人物領域の重大NG記録なし",),
        object_findings or ("物・小物領域の重大NG記録なし",),
        background_findings or ("背景・空間領域の重大NG記録なし",),
        photo_quality_findings,
        consistency_findings or ("本人感・固定ルールの重大NG記録なし",),
        metrics,
        identity_review_score=identity_score,
        identity_review_source=identity_source,
        identity_review_items=identity_items,
    )


def _build_report(
    root: Path,
    image_path: Path,
    character: str,
    scores: VQCScores,
    critical_errors: Iterable[str],
    person_findings: Iterable[str],
    object_findings: Iterable[str],
    background_findings: Iterable[str],
    photo_quality_findings: Iterable[str],
    consistency_findings: Iterable[str],
    metrics: VQCMetrics | None,
    identity_review_score: int | None = None,
    identity_review_source: str = "",
    identity_review_items: dict[str, bool] | None = None,
) -> VQCReport:
    critical = tuple(dict.fromkeys(filter(None, critical_errors)))
    status = _judge_status(scores, critical)
    retry_required = status != "PASS"
    retry_instruction = _retry_instruction(
        status=status,
        critical_errors=critical,
        person_findings=tuple(person_findings),
        object_findings=tuple(object_findings),
        background_findings=tuple(background_findings),
        photo_quality_findings=tuple(photo_quality_findings),
        consistency_findings=tuple(consistency_findings),
    )
    return VQCReport(
        file_name=image_path.name,
        source_path=_relative(root, image_path),
        character=character,
        status=status,
        scores=scores,
        identity_review_required=True,
        identity_review_score=identity_review_score,
        identity_review_source=identity_review_source,
        identity_review_items=identity_review_items or {},
        metrics=metrics,
        critical_errors=critical,
        person_findings=tuple(person_findings),
        object_findings=tuple(object_findings),
        background_findings=tuple(background_findings),
        photo_quality_findings=tuple(photo_quality_findings),
        character_consistency_findings=tuple(consistency_findings),
        retry_required=retry_required,
        retry_instruction=retry_instruction,
    )


def _judge_status(scores: VQCScores, critical_errors: tuple[str, ...]) -> str:
    if critical_errors or scores.minimum <= 64:
        return "FAIL"
    if scores.minimum >= 80 and scores.average >= 85:
        return "PASS"
    return "REVIEW"


def _retry_instruction(
    status: str,
    critical_errors: tuple[str, ...],
    person_findings: tuple[str, ...],
    object_findings: tuple[str, ...],
    background_findings: tuple[str, ...],
    photo_quality_findings: tuple[str, ...],
    consistency_findings: tuple[str, ...],
) -> str:
    if status == "PASS":
        return ""
    all_findings = "\n".join(
        critical_errors
        + person_findings
        + object_findings
        + background_findings
        + photo_quality_findings
        + consistency_findings
    )
    if any(word in all_findings for word in ("指", "手", "スマートフォン", "貫通")):
        return "手と小物の接触を単純化し、スマホやバッグを画角外または自然な位置へ移す。人物、服、場所、テーマは維持する。"
    if any(word in all_findings for word in ("背景", "家具", "窓", "鏡", "文字", "ロゴ")):
        return "背景を単純化し、読める文字やロゴを避ける。人物、服装、テーマは維持する。"
    if any(word in all_findings for word in ("本人", "別人", "年齢", "マスク")):
        return "本人固定リファレンスを最優先し、顔・年齢感・必須小物を維持する。構図資料や衣装資料に顔を引っ張られないようにする。"
    if any(word in all_findings for word in ("画質", "EXIF", "照明", "HDR", "シャープ")):
        return "スマートフォンの日常写真に寄せ、過度な補正を避ける。保存後はstrip_exif.pyを通す。"
    return "不合格理由だけを最小限補正し、人物、服、場所、テーマは維持する。"


def _write_reports(source_dir: Path, reports: tuple[VQCReport, ...]) -> None:
    report_dir = source_dir / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    for index, report in enumerate(reports, start=1):
        path = report_dir / f"image_{index:02d}_report.json"
        path.write_text(
            json.dumps(_report_to_json(report), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


def _write_batch_summary(source_dir: Path, summary: VQCBatchSummary) -> None:
    report_dir = source_dir / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    summary_json = {
        "character": summary.character,
        "output_date": summary.output_date,
        "source_dir": summary.source_dir,
        "total_images": summary.total_images,
        "pass_count": summary.pass_count,
        "review_count": summary.review_count,
        "fail_count": summary.fail_count,
        "minimum_pass_required": summary.minimum_pass_required,
        "ready_for_post_preparation": summary.ready_for_post_preparation,
        "generated_at": summary.generated_at,
        "reports": [_report_to_json(report) for report in summary.reports],
    }
    (report_dir / "batch_summary.json").write_text(
        json.dumps(summary_json, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (source_dir / "status.json").write_text(
        json.dumps(
            {
                "status": "ready"
                if summary.ready_for_post_preparation
                else "hold_for_ceo_review",
                "pass_count": summary.pass_count,
                "review_count": summary.review_count,
                "fail_count": summary.fail_count,
                "minimum_pass_required": summary.minimum_pass_required,
                "generated_at": summary.generated_at,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    _write_identity_review_template(source_dir, summary.reports)


def _copy_images_by_status(root: Path, source_dir: Path, reports: tuple[VQCReport, ...]) -> None:
    images_root = source_dir / "images"
    for status in ("pass", "review", "fail"):
        (images_root / status).mkdir(parents=True, exist_ok=True)

    for report in reports:
        for status in ("pass", "review", "fail"):
            stale = images_root / status / report.file_name
            if stale.exists():
                stale.unlink()
        source = root / report.source_path if not Path(report.source_path).is_absolute() else Path(report.source_path)
        if not source.exists():
            source = source_dir / "images" / report.file_name
        destination = images_root / report.status.lower() / report.file_name
        if source.resolve() == destination.resolve():
            continue
        shutil.copy2(source, destination)


def _report_to_json(report: VQCReport) -> dict:
    data = asdict(report)
    data["scores"] = asdict(report.scores)
    data["score_summary"] = {
        "average": report.scores.average,
        "minimum": report.scores.minimum,
        "pass_threshold_minimum": 80,
        "pass_threshold_average": 85,
        "fail_threshold_minimum": 64,
    }
    return data


def _iter_candidate_images(source_dir: Path) -> list[Path]:
    images_root = source_dir / "images"
    search_root = images_root if images_root.exists() else source_dir
    images = []
    for path in sorted(search_root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        if any(part in {"pass", "review", "fail"} for part in path.parts):
            continue
        if path.name.startswith("CONTACT_SHEET"):
            continue
        images.append(path)
    return images


def _collect_context_text(source_dir: Path, image_path: Path) -> str:
    date_dir = _find_date_dir(source_dir)
    candidates = [
        date_dir / "Daily_Brief.md" if date_dir else None,
        source_dir / "report.md",
        source_dir / "prompt.txt",
        source_dir / "status.json",
        source_dir / "reports" / f"{image_path.stem}.json",
        image_path.with_suffix(".json"),
        image_path.with_name(f"{image_path.stem}_notes.json"),
    ]
    pieces = []
    for path in candidates:
        if path and path.exists():
            try:
                pieces.append(path.read_text(encoding="utf-8"))
            except UnicodeDecodeError:
                pieces.append(path.read_text(encoding="utf-8", errors="ignore"))
    return "\n".join(pieces)


def _load_identity_review(source_dir: Path, image_path: Path) -> dict | None:
    image_note = image_path.with_name(f"{image_path.stem}_notes.json")
    candidates = (image_note, source_dir / "identity_review.json")
    for path in candidates:
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if path == image_note:
            review = data.get("identity_review", data)
        else:
            review = data.get("images", {}).get(image_path.name)
        if isinstance(review, dict):
            review = dict(review)
            review["_source"] = _relative(source_dir, path)
            return review
    return None


def _identity_review_parts(review: dict | None) -> tuple[int | None, dict[str, bool], str]:
    if not review:
        return None, {}, ""
    raw_score = review.get("identity_score")
    try:
        score = int(raw_score)
    except (TypeError, ValueError):
        score = None
    items: dict[str, bool] = {}
    for key, value in review.items():
        if isinstance(value, bool):
            items[key] = value
    return score, items, str(review.get("_source", ""))


def _write_identity_review_template(source_dir: Path, reports: tuple[VQCReport, ...]) -> None:
    path = source_dir / "identity_review_template.json"
    if path.exists():
        return
    template = {
        "instructions": [
            "生成後に必ず目視で入力する。未入力の画像はAI-VQCでPASSにしない。",
            "identity_scoreは0-100。90以上=本人感強い、80-89=採用前確認、65-79=再生成候補、64以下=FAIL。",
            "衣装資料・構図資料の顔に引っ張られている場合はface_matches_base=falseにする。",
            "身体破綻、自撮り矛盾、暗すぎる写真などがある場合は該当項目をfalseにする。",
        ],
        "images": {
            report.file_name: {
                "identity_score": None,
                "base_reference_used": False,
                "face_matches_base": False,
                "age_matches": False,
                "hair_matches": False,
                "body_matches": False,
                "outfit_reference_limited_to_clothes": False,
                "physical_integrity_ok": False,
                "hands_limbs_ok": False,
                "selfie_logic_ok": False,
                "outfit_continuity_ok": False,
                "background_text_logo_ok": False,
                "scene_physics_ok": False,
                "lighting_ok": False,
                "notes": "",
            }
            for report in reports
        },
    }
    path.write_text(json.dumps(template, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _find_date_dir(source_dir: Path) -> Path | None:
    for path in (source_dir, *source_dir.parents):
        if path.parent.name == "02_Daily_Output":
            return path
    return None


def _apply_keyword_penalties(
    text: str,
    rules: tuple[tuple[str, int, str, bool], ...],
    findings: list[str],
    critical_errors: list[str],
) -> int:
    penalty = 0
    for keyword, value, finding, critical in rules:
        if _has_problem_keyword(text, keyword):
            findings.append(finding)
            penalty += value
            if critical:
                critical_errors.append(finding)
    return penalty


def _count_problem_hits(text: str, rules: tuple[tuple[str, int, str, bool], ...]) -> int:
    return sum(
        1
        for keyword, _, _, _ in rules
        if _has_problem_keyword(text, keyword)
    )


def _count_problem_marker_lines(text: str) -> int:
    return sum(
        1
        for line in text.splitlines()
        if _is_problem_record_line(line) and not _is_negative_problem_line(line)
    )


def _resolution_component(width: int, height: int) -> int:
    short = min(width, height)
    long = max(width, height)
    megapixels = (width * height) / 1_000_000
    if short >= 1024 and long >= 1536 and megapixels >= 1.5:
        return 100
    if short >= 768 and long >= 1024 and megapixels >= 0.9:
        return 92
    if short >= 640 and long >= 900:
        return 78
    return 60


def _aspect_ratio_component(aspect_ratio: float) -> int:
    if 0.60 <= aspect_ratio <= 1.34:
        return 100
    if 0.45 <= aspect_ratio <= 1.85:
        return 90
    if 0.35 <= aspect_ratio <= 2.20:
        return 74
    return 55


def _file_size_component(file_size: int, width: int, height: int) -> int:
    megapixels = max((width * height) / 1_000_000, 0.01)
    bytes_per_megapixel = file_size / megapixels
    if file_size >= 700_000 and bytes_per_megapixel >= 450_000:
        return 100
    if file_size >= 250_000 and bytes_per_megapixel >= 200_000:
        return 90
    if file_size >= 150_000:
        return 74
    return 55


def _contrast_component(luminance_range: int, luminance_stddev: float) -> int:
    if luminance_range >= 160 and luminance_stddev >= 35:
        return 100
    if luminance_range >= 100 and luminance_stddev >= 24:
        return 90
    if luminance_range >= 60 and luminance_stddev >= 16:
        return 74
    return 58


def _edge_component(edge_mean: float) -> int:
    if 4.0 <= edge_mean <= 22.0:
        return 100
    if 2.5 <= edge_mean < 4.0 or 22.0 < edge_mean <= 30.0:
        return 88
    if 1.5 <= edge_mean < 2.5 or 30.0 < edge_mean <= 38.0:
        return 72
    return 58


def _person_problem_keywords() -> tuple[tuple[str, int, str, bool], ...]:
    return (
        ("別人", -45, "別人化の記録あり", True),
        ("顔が違", -35, "本人顔からのズレ記録あり", True),
        ("顔破綻", -45, "顔の重大破綻記録あり", True),
        ("目の重複", -45, "目の重複記録あり", True),
        ("歯", -20, "歯・口元の確認記録あり", False),
        ("首", -14, "首・顔接続の確認記録あり", False),
        ("指", -24, "手指の確認記録あり", False),
        ("手が", -18, "手の形状確認記録あり", False),
        ("体型ズレ", -32, "体型ズレの記録あり", False),
        ("体の厚み", -18, "体の厚み確認記録あり", False),
    )


def _object_problem_keywords() -> tuple[tuple[str, int, str, bool], ...]:
    return (
        ("携帯", -22, "スマホ位置・形状の確認記録あり", False),
        ("スマホ", -22, "スマホ位置・形状の確認記録あり", False),
        ("カバン", -18, "バッグ整合性の確認記録あり", False),
        ("バッグ", -18, "バッグ整合性の確認記録あり", False),
        ("ショルダー", -12, "ショルダーバッグ整合性の確認記録あり", False),
        ("貫通", -45, "物体貫通の記録あり", True),
        ("右ハンドル", -18, "車内ハンドル位置の確認記録あり", False),
        ("左ハンドル", -45, "車内ハンドル位置の重大NG記録あり", True),
        ("小物がおかしい", -24, "小物の不自然記録あり", False),
    )


def _background_problem_keywords() -> tuple[tuple[str, int, str, bool], ...]:
    return (
        ("文字破綻", -28, "背景文字破綻の記録あり", False),
        ("ロゴ", -16, "ロゴ・固有名詞の確認記録あり", False),
        ("背景", -8, "背景確認記録あり", False),
        ("鏡", -18, "鏡・反射整合性の確認記録あり", False),
        ("室内で靴", -35, "室内靴の記録あり", False),
        ("自部屋", -12, "自部屋設定確認記録あり", False),
        ("車内", -8, "車内空間確認記録あり", False),
        ("空間破綻", -35, "空間破綻の記録あり", True),
        ("背景破綻", -35, "背景破綻の記録あり", True),
        ("完全破綻", -45, "完全破綻の記録あり", True),
    )


def _consistency_problem_keywords(character: str) -> tuple[tuple[str, int, str, bool], ...]:
    rules = [
        ("服装が違", -20, "服装連動ズレの記録あり", False),
        ("服装違う", -20, "服装連動ズレの記録あり", False),
        ("髪型", -12, "髪型確認記録あり", False),
        ("年齢", -14, "年齢感確認記録あり", False),
    ]
    if character == "MIKU":
        rules.extend(
            [
                ("マスクなし", -50, "MIKUマスク未着用の記録あり", True),
                ("マスク", 0, "MIKUマスク確認記録あり", False),
            ]
        )
    return tuple(rules)


def _has_problem_keyword(text: str, keyword: str) -> bool:
    return any(
        keyword in line
        and not _is_negative_problem_line(line)
        and _is_problem_record_line(line)
        for line in text.splitlines()
    )


def _is_problem_record_line(line: str) -> bool:
    problem_markers = (
        "記録あり",
        "NG",
        "FAIL",
        "不合格",
        "問題",
        "ズレ",
        "ずれ",
        "違う",
        "別人",
        "おかしい",
        "ダメ",
        "やり直し",
        "再生成",
        "修正",
        "破綻",
        "崩壊",
        "貫通",
        "融合",
        "増殖",
        "反転",
        "未着用",
        "未完了",
        "未取得",
        "不足",
        "使えない",
        "消して",
        "復活",
    )
    return any(marker in line for marker in problem_markers)


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
        "重大NG記録なし",
        "以外",
        "確認",
        "チェック",
        "事項",
        "成立している",
        "見る",
        "注意",
        "ルール",
    )
    return any(marker in line for marker in negative_markers)


def _marker_path(path: Path) -> Path:
    return path.with_name(f"{path.name}.exifcleaned")


def _clamp(score: int) -> int:
    return max(0, min(100, score))


def _relative(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root))
    except ValueError:
        return str(path)
