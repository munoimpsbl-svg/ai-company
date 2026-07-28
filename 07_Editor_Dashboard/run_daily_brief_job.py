from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys
from typing import List, Optional


@dataclass(frozen=True)
class BriefStep:
    name: str
    employee: str
    commands: List[List[str]]


@dataclass(frozen=True)
class BriefResult:
    name: str
    employee: str
    start_time: datetime
    end_time: datetime
    success: bool
    error: Optional[str]


STEPS = (
    BriefStep(
        name="SNS Daily Brief",
        employee="SNS分析AI",
        commands=[
            [sys.executable, "03_SNS事業部/main.py"],
            [sys.executable, "03_SNS事業部/generate_daily_brief.py"],
        ],
    ),
    BriefStep(
        name="Gravure Daily Brief",
        employee="グラビア事業部長AI",
        commands=[
            [sys.executable, "run_p003_sprint2.py"],
            [sys.executable, "04_グラビア事業部/generate_daily_brief.py"],
        ],
    ),
    BriefStep(
        name="Adult Daily Brief",
        employee="アダルト事業部長AI",
        commands=[
            [sys.executable, "04_アダルト事業部/main.py"],
            [sys.executable, "04_アダルト事業部/generate_daily_brief.py"],
        ],
    ),
    BriefStep(
        name="CEO Report",
        employee="AI社長",
        commands=[
            [sys.executable, "generate_kpi_dashboard.py"],
            [sys.executable, "05_AI社長/main.py"],
        ],
    ),
)


def main() -> int:
    workspace_root = Path(__file__).resolve().parents[1]
    run_start = datetime.now()
    results = []
    _write_progress(workspace_root, "running", run_start, "入力確認", results)

    for step in STEPS:
        _write_progress(workspace_root, "running", run_start, step.name, results)
        results.append(_run_step(step, workspace_root))
        _write_progress(workspace_root, "running", run_start, step.name, results)

    status = "completed" if all(result.success for result in results) else "failed"
    _write_progress(workspace_root, status, run_start, "完了", results)
    print(f"DAILY_BRIEF_JOB {status}")
    return 0


def _run_step(step: BriefStep, cwd: Path) -> BriefResult:
    start_time = datetime.now()
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
            if completed.returncode != 0:
                errors.append(f"{' '.join(command)} exited with {completed.returncode}")
        except Exception as exc:
            errors.append(f"{' '.join(command)} failed: {exc}")
    end_time = datetime.now()
    return BriefResult(
        name=step.name,
        employee=step.employee,
        start_time=start_time,
        end_time=end_time,
        success=not errors,
        error="\n".join(errors) if errors else None,
    )


def _write_progress(
    workspace_root: Path,
    status: str,
    run_start: datetime,
    current_step: str,
    results: List[BriefResult],
) -> None:
    progress_dir = workspace_root / ".dashboard_jobs"
    progress_dir.mkdir(parents=True, exist_ok=True)
    completed = {result.name: result for result in results}
    steps = []
    for step in STEPS:
        result = completed.get(step.name)
        if result:
            step_status = "success" if result.success else "failed"
        elif step.name == current_step:
            step_status = "running"
        else:
            step_status = "pending"
        steps.append(
            {
                "name": step.name,
                "employee": step.employee,
                "status": step_status,
            }
        )

    payload = {
        "status": status,
        "started_at": run_start.isoformat(timespec="seconds"),
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "current_step": current_step,
        "steps": steps,
    }
    (progress_dir / "daily_brief_progress.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
