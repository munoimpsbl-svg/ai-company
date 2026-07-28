from datetime import date
from pathlib import Path

from core.kpi import dashboard


def main() -> int:
    workspace_root = Path(__file__).resolve().parent
    dashboard = build_kpi_dashboard(workspace_root)
    root_path = workspace_root / "KPI_DASHBOARD.md"
    daily_path = (
        workspace_root
        / "02_Daily_Output"
        / date.today().isoformat()
        / "KPI_DASHBOARD.md"
    )
    root_path.write_text(dashboard, encoding="utf-8")
    daily_path.parent.mkdir(parents=True, exist_ok=True)
    daily_path.write_text(dashboard, encoding="utf-8")
    print(f"KPI_DASHBOARD saved: {root_path}")
    print(f"Daily KPI_DASHBOARD saved: {daily_path}")
    return 0


def build_kpi_dashboard(workspace_root: Path) -> str:
    kpi = dashboard.fetch()
    sources = kpi["sources"]
    total = kpi["total"]

    return f"""# KPI DASHBOARD

日付

{date.today().isoformat()}

---

## Executive Summary

- 取得方式: core/kpi/dashboard.py
- データソース: Instagram / X / WordPress / Search Console / GA4 / Sales
- X: MIKUのX CSV分析に対応
- 推測: なし

---

## Total KPI

| KPI | 数値 |
| --- | --- |
| followers | {total["followers"]} |
| impressions | {total["impressions"]} |
| engagement | {total["engagement"]} |
| ctr | {total["ctr"]} |
| pv | {total["pv"]} |
| sales | {total["sales"]} |
| clicks | {total["clicks"]} |
| position | {total["position"]} |
| users | {total["users"]} |
| sessions | {total["sessions"]} |
| page_views | {total["page_views"]} |
| engagement_time | {total["engagement_time"]} |
| posts | {total["posts"]} |
| published | {total["published"]} |
| categories | {total["categories"]} |
| tags | {total["tags"]} |

---

## Source KPI

{_format_sources(sources)}

---

## Blocker

- Instagram / Sales は未接続。
- XはGoogle Drive入力`AI_COMPANY_INPUT/03_SNS事業部/03_Analytics/MIKU/X/*.csv`を正とし、Drive同期manifestに記録されたCSVがある場合のみ取得。
- WordPressはREST APIから取得。
- Search Consoleは認証情報と対象プロパティが設定済みの場合のみ取得。
- GA4は認証情報とプロパティIDが設定済みの場合のみ取得。

---

## Notes

- KPI値は`core/kpi/dashboard.py`から取得。
- 各データソースは共通インターフェース`fetch()`を持つ。
- WordPress更新、SNS投稿、Google Drive変更は未実行。
"""


def _format_sources(sources):
    lines = [
        "| source | followers | impressions | engagement | ctr | pv | sales | clicks | position | users | sessions | page_views | engagement_time | posts | published | categories | tags |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, values in sources.items():
        lines.append(
            f"| {name} | {values['followers']} | {values['impressions']} | "
            f"{values['engagement']} | {values['ctr']} | {values['pv']} | {values['sales']} | "
            f"{values['clicks']} | {values['position']} | "
            f"{values['users']} | {values['sessions']} | {values['page_views']} | {values['engagement_time']} | "
            f"{values['posts']} | {values['published']} | {values['categories']} | {values['tags']} |"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
