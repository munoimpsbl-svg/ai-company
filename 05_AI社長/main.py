from pathlib import Path

from core.ceo_report import (
    build_ceo_report,
    read_department_briefs,
    read_kpi_dashboard,
    save_ceo_report,
)


def main() -> int:
    workspace_root = Path(__file__).resolve().parents[1]
    try:
        briefs = read_department_briefs(workspace_root)
        kpi_dashboard = read_kpi_dashboard(workspace_root)
        report = build_ceo_report(briefs, kpi_dashboard)
        output_path = save_ceo_report(workspace_root, report)
        print(f"CEO_REPORT saved: {output_path}")
        print(f"KPI Dashboard: {kpi_dashboard.status}")
        if kpi_dashboard.error:
            print(f"KPI Dashboard Error: {kpi_dashboard.error}")
        for brief in briefs:
            if brief.status != "提出済み":
                print(f"{brief.department}: {brief.status} ({brief.error})")
            else:
                print(f"{brief.department}: {brief.status}")
        return 0
    except Exception as exc:
        fallback_report = _build_error_report(exc)
        output_path = save_ceo_report(workspace_root, fallback_report)
        print(f"CEO_REPORT saved with error: {output_path}")
        print(f"Error: {exc}")
        return 0


def _build_error_report(exc: Exception) -> str:
    return f"""# CEO REPORT

日付

未取得

---

## 本日の総評

- エラー発生。ただし処理は停止せずCEO_REPORT.mdを生成した。
- 理由: {exc}

---

## Priority 1

担当

未提出

理由

未提出

期待ROI

未提出

作業時間

未提出

承認（GO / STOP）

STOP

---

## Priority 2

担当

未提出

理由

未提出

期待ROI

未提出

作業時間

未提出

承認（GO / STOP）

STOP

---

## Priority 3

担当

未提出

理由

未提出

期待ROI

未提出

作業時間

未提出

承認（GO / STOP）

STOP

---

## Blocker

- {exc}

---

## 本日の経営判断

新規記事作成

STOP

既存記事改善

STOP

CTR改善

STOP

SEO改善

STOP

---

## 明日の予定

- エラー内容を確認する。

---

## CTOコメント

AI社長は分析を行わず、エラー理由のみを記録した。
"""


if __name__ == "__main__":
    raise SystemExit(main())
