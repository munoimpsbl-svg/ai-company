from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import List, Optional

from core.project import ProjectStatus, discover_projects, format_project_statuses


@dataclass(frozen=True)
class PlatformSprintReport:
    title: str
    content: str
    project_statuses: List[ProjectStatus]


def build_p001_sprint1_report(
    workspace_root: Path,
    report_date: Optional[date] = None,
) -> PlatformSprintReport:
    root = workspace_root.expanduser().resolve()
    current_date = report_date or date.today()
    project_statuses = discover_projects(root)
    project_summary = format_project_statuses(project_statuses, root)

    content = f"""# REPORT

## 実行日

{current_date.isoformat()}

## 今日の結論

P001 Core Platform Sprint1を開始した。

ローカルワークスペース内の標準プロジェクトファイルを検出し、各プロジェクトがAI COMPANY標準のPROJECT / SPEC / TASK / REPORT / CHANGELOGを持つか確認できる状態にした。

## プロジェクト検出結果

{project_summary}

## Sprint1実装結果

- 標準プロジェクトファイルの検出を実装。
- プロジェクト単位の不足ファイル確認を実装。
- REPORT.md保存処理を実装。
- CHANGELOG.md追記処理を実装。
- P001 Sprint1レポート生成処理を実装。

## 安全確認

- WordPress自動公開: 未実行
- SNS自動投稿: 未実行
- Google Drive構成変更: 未実行
- 既存ファイル移動: 未実行
- 既存ファイル削除: 未実行
- 自動承認: 未実行

## 未接続

- Google Drive書き込み保存
- AI社長レポート自動集約
- 日次スケジューラー

## 次回作業

1. P001の日次実行時刻を確定する。
2. AI社長レポートの保存先を確定する。
3. Google Drive保存の承認範囲を確定する。
4. P003の日報をP001標準で継続更新する。
"""

    return PlatformSprintReport(
        title="Core Platform Sprint1 日報",
        content=content,
        project_statuses=project_statuses,
    )
