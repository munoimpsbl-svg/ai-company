# P005 TASK

## TASK-002 CEO_REPORT生成

Status
DONE

Priority
★★★★★

成果物

- `02_Daily_Output/YYYY-MM-DD/CEO_REPORT.md`

完了条件

- [x] DAILY_BRIEF.mdを読める
- [x] CEO_REPORT.mdを生成できる
- [x] 未提出部署は「未提出」と表示する
- [x] 推測しない
- [x] エラーで停止しない
- [x] REPORT.mdやDAILY_BRIEF.mdを書き換えない

---

## TASK-003 実データ接続テスト

Status
DONE

Priority
★★★★★

目的

AI社長が各部署の実際のDAILY_BRIEF.mdを読み込み、CEO_REPORT.mdを生成できることを確認する。

確認項目

- [x] P003 DAILY_BRIEF.mdを読み込めること
- [x] P002 DAILY_BRIEF.mdが無ければ「未提出」と表示すること
- [x] P004 DAILY_BRIEF.mdが無ければ「未提出」と表示すること
- [x] P003の内容をCEO_REPORTへ反映すること

完了条件

- [x] P003のDaily BriefがCEO_REPORTへ反映される
- [x] 未提出部署は「未提出」と表示される
- [x] 推測は禁止
- [x] エラー停止なし

---

## P002・P005 インターフェース統一

Status
DONE

完了条件

- [x] P002 Daily Briefの命名規則を`DAILY_BRIEF.md`へ統一
- [x] P005が`03_SNS事業部/04_Daily/DAILY_BRIEF.md`を読み込む
- [x] P005実行時に`P002 SNS事業部: 提出済み`と表示される

---

## TASK KPI Dashboard統合

Status
DONE

Priority
★★★★★

目的

KPI DashboardをCEO_REPORTへ統合する。

入力

- `KPI_DASHBOARD.md`
- `03_SNS事業部/04_Daily/DAILY_BRIEF.md`
- `04_グラビア事業部/DAILY_BRIEF.md`

出力

- `02_Daily_Output/YYYY-MM-DD/CEO_REPORT.md`

完了条件

- [x] WordPress KPIをCEO_REPORTへ表示
- [x] Search Console KPIをCEO_REPORTへ表示
- [x] GA4 KPIをCEO_REPORTへ表示
- [x] KPI未取得時は「未取得」と表示
- [x] 推測しない
- [x] DAILY_BRIEF.mdを書き換えない
- [x] KPI_DASHBOARD.mdを書き換えない
## 2026-07-28 Priority抽出改善

- [x] P002だけでPriorityが埋まる状態を修正
- [x] P003 グラビア事業部のSEO優先事項をCEO_REPORTへ反映
- [x] P004 アダルト事業部のBlocker / 優先事項をCEO_REPORTへ反映
- [x] `CEO_REPORT.md`を再生成
