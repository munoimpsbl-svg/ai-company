from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys
from typing import List, Optional

from artifact_sync import format_sync_results, sync_runner_artifacts


@dataclass(frozen=True)
class RunnerStep:
    name: str
    commands: List[List[str]]


@dataclass(frozen=True)
class StepResult:
    name: str
    start_time: datetime
    end_time: datetime
    success: bool
    stdout: str
    stderr: str
    error: Optional[str]


STEPS = (
    RunnerStep(
        name="P002 SNS事業部",
        commands=[
            [sys.executable, "03_SNS事業部/main.py"],
            [sys.executable, "03_SNS事業部/generate_daily_brief.py"],
        ],
    ),
    RunnerStep(
        name="P003 グラビア事業部",
        commands=[
            [sys.executable, "06_AI_COMPANY_Runner/approval_sync.py"],
            [sys.executable, "06_AI_COMPANY_Runner/plan_approval_sync.py"],
            [sys.executable, "run_p003_sprint2.py"],
            [sys.executable, "04_グラビア事業部/generate_daily_brief.py"],
        ],
    ),
    RunnerStep(
        name="KPI Dashboard",
        commands=[[sys.executable, "generate_kpi_dashboard.py"]],
    ),
    RunnerStep(
        name="P004 アダルト事業部",
        commands=[
            [sys.executable, "04_アダルト事業部/main.py"],
            [sys.executable, "04_アダルト事業部/generate_daily_brief.py"],
        ],
    ),
    RunnerStep(
        name="GPT Image Quality",
        commands=[[sys.executable, "scripts/update_generation_quality.py"]],
    ),
    RunnerStep(
        name="P005 AI社長",
        commands=[[sys.executable, "05_AI社長/main.py"]],
    ),
)


def main() -> int:
    workspace_root = Path(__file__).resolve().parents[1]
    run_start = datetime.now()
    results = []

    for step in STEPS:
        _write_progress(workspace_root, "running", run_start, step.name, results)
        results.append(_run_step(step, workspace_root))
        _write_progress(workspace_root, "running", run_start, step.name, results)

    run_end = datetime.now()
    report = _build_run_report(run_start, run_end, results, [])
    report_path = _save_report(workspace_root, report)
    log_path = _save_daily_log(workspace_root, report, run_start)
    _write_progress(workspace_root, "syncing", run_start, "Google Drive保存", results)
    sync_results = sync_runner_artifacts(workspace_root)
    final_report = _build_run_report(run_start, run_end, results, sync_results)
    report_path = _save_report(workspace_root, final_report)
    log_path = _save_daily_log(workspace_root, final_report, run_start)
    _write_progress(workspace_root, "completed", run_start, "完了", results)

    print(f"RUN_REPORT saved: {report_path}")
    print(f"RUN_LOG saved: {log_path}")
    return 0


def _write_progress(
    workspace_root: Path,
    status: str,
    run_start: datetime,
    current_step: str,
    results: List[StepResult],
) -> None:
    progress_dir = workspace_root / ".dashboard_jobs"
    progress_dir.mkdir(parents=True, exist_ok=True)
    completed = {result.name: result for result in results}
    steps = []
    for step in STEPS:
        result = completed.get(step.name)
        if result:
            step_status = "success" if result.success else "failed"
        elif step.name == current_step and status == "running":
            step_status = "running"
        else:
            step_status = "pending"
        steps.append({"name": step.name, "status": step_status})

    payload = {
        "status": status,
        "started_at": run_start.isoformat(timespec="seconds"),
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "current_step": current_step,
        "steps": steps,
    }
    (progress_dir / "runner_progress.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _run_step(step: RunnerStep, cwd: Path) -> StepResult:
    start_time = datetime.now()
    stdout_parts = []
    stderr_parts = []
    errors = []

    for command in step.commands:
        try:
            completed = subprocess.run(
                command,
                cwd=str(cwd),
                text=True,
                capture_output=True,
                timeout=300,
            )
            stdout_parts.append(_format_command_output(command, completed.stdout))
            stderr_parts.append(_format_command_output(command, completed.stderr))
            if completed.returncode != 0:
                errors.append(
                    f"{' '.join(command)} exited with {completed.returncode}"
                )
        except Exception as exc:
            errors.append(f"{' '.join(command)} failed: {exc}")

    end_time = datetime.now()
    return StepResult(
        name=step.name,
        start_time=start_time,
        end_time=end_time,
        success=not errors,
        stdout="\n".join(part for part in stdout_parts if part.strip()),
        stderr="\n".join(part for part in stderr_parts if part.strip()),
        error="\n".join(errors) if errors else None,
    )


def _build_run_report(
    run_start: datetime,
    run_end: datetime,
    results: List[StepResult],
    sync_results,
) -> str:
    success = [result for result in results if result.success]
    failed = [result for result in results if not result.success]

    return f"""# RUN REPORT

## 開始時間

{run_start.isoformat(timespec="seconds")}

## 終了時間

{run_end.isoformat(timespec="seconds")}

## 成功

{_format_result_names(success)}

## 失敗

{_format_result_names(failed)}

## エラー内容

{_format_errors(failed)}

## Google Drive保存

{format_sync_results(sync_results)}

## 実行詳細

{_format_details(results)}

## 制約確認

- エラーがあっても次の部署を実行する: OK
- 途中停止禁止: OK
- Runnerによる承認GO同期: 実装待ちへの状態遷移のみ
- RunnerによるWordPress更新: 未実行
- RunnerによるSNS投稿: 未実行
- Runnerによる画像自動採用: 未実行
- RunnerによるGoogle Drive削除: 未実行
- Google Drive保存に失敗しても処理継続: OK
"""


def _save_report(workspace_root: Path, content: str) -> Path:
    path = workspace_root / "06_AI_COMPANY_Runner" / "RUN_REPORT.md"
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    return path


def _save_daily_log(workspace_root: Path, content: str, run_start: datetime) -> Path:
    output_dir = workspace_root / "02_Daily_Output" / run_start.date().isoformat()
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "RUN_REPORT.md"
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    return path


def _format_result_names(results: List[StepResult]) -> str:
    if not results:
        return "- なし"
    return "\n".join(f"- {result.name}" for result in results)


def _format_errors(results: List[StepResult]) -> str:
    if not results:
        return "- なし"
    return "\n".join(
        f"- {result.name}: {result.error or '未取得'}" for result in results
    )


def _format_details(results: List[StepResult]) -> str:
    lines = []
    for result in results:
        lines.extend(
            [
                f"### {result.name}",
                "",
                f"- 開始時間: {result.start_time.isoformat(timespec='seconds')}",
                f"- 終了時間: {result.end_time.isoformat(timespec='seconds')}",
                f"- Status: {'SUCCESS' if result.success else 'FAILED'}",
                f"- Error: {result.error or 'なし'}",
                "",
                "Stdout:",
                "",
                "```text",
                result.stdout or "なし",
                "```",
                "",
                "Stderr:",
                "",
                "```text",
                result.stderr or "なし",
                "```",
                "",
            ]
        )
    return "\n".join(lines).rstrip()


def _format_command_output(command: List[str], output: str) -> str:
    return f"$ {' '.join(command)}\n{output.strip()}" if output.strip() else ""


if __name__ == "__main__":
    raise SystemExit(main())
