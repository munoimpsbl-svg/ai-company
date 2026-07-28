from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.sns_analysis import build_sns_report, load_dummy_social_data, save_report


def main() -> int:
    project_root = Path(__file__).resolve().parent
    report_path = project_root / "REPORT.md"
    try:
        accounts = load_dummy_social_data()
        report = build_sns_report(accounts)
        save_report(report_path, report)
        print(f"P002 REPORT saved: {report_path}")
        return 0
    except Exception as exc:
        fallback_report = f"""# P002 SNS事業部 REPORT

## Executive Summary

エラーが発生したが、処理は停止せずREPORT.mdを生成した。

## Blocker

- {exc}

## 制約確認

- 投稿: 未実行
- 更新: 未実行
- 削除: 未実行
- 分析のみ: OK
"""
        save_report(report_path, fallback_report)
        print(f"P002 REPORT saved with error: {report_path}")
        print(f"Error: {exc}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
