# KPI DASHBOARD

日付

2026-07-08

---

## Executive Summary

- 取得方式: core/kpi/dashboard.py
- データソース: Instagram / X / WordPress / Search Console / GA4 / Sales
- Sprint4: Google Analytics 4 KPI連携
- 推測: なし

---

## Total KPI

| KPI | 数値 |
| --- | --- |
| followers | 0 |
| impressions | 2 |
| engagement | 0 |
| ctr | 0 |
| pv | 0 |
| sales | 0 |
| clicks | 0 |
| position | 37 |
| users | 0 |
| sessions | 0 |
| page_views | 0 |
| engagement_time | 0 |
| posts | 9 |
| published | 9 |
| categories | 8 |
| tags | 15 |

---

## Source KPI

| source | followers | impressions | engagement | ctr | pv | sales | clicks | position | users | sessions | page_views | engagement_time | posts | published | categories | tags |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| instagram | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| x | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| wordpress | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 9 | 9 | 8 | 15 |
| search_console | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 37 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| ga4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| sales | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

---

## Blocker

- Instagram / X / Sales は未接続。
- WordPressはREST APIから取得。
- Search Consoleは認証情報と対象プロパティが設定済みの場合のみ取得。
- GA4は認証情報とプロパティIDが設定済みの場合のみ取得。

---

## Notes

- KPI値は`core/kpi/dashboard.py`から取得。
- 各データソースは共通インターフェース`fetch()`を持つ。
- WordPress更新、SNS投稿、Google Drive変更は未実行。
