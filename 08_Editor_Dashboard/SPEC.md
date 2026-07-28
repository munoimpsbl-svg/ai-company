# Editor Dashboard SPEC

## 目的

編集長がAI COMPANYの当日状況を1画面で確認できる表示専用ダッシュボードを作成する。

## 技術

- Streamlit

## 入力

- `KPI_DASHBOARD.md`
- `CEO_REPORT.md`
- `RUN_REPORT.md`
- `P002 DAILY_BRIEF.md`
- `P003 DAILY_BRIEF.md`

## 表示

- Overview
- KPI
- CEO Report
- Run Report
- P002 Brief
- P003 Brief

## 制約

- ファイルは読み取りのみ。
- WordPress更新は禁止。
- WordPress投稿は禁止。
- SNS投稿は禁止。
- Google Drive変更は禁止。
- 入力ファイルの書き換えは禁止。

---

## Sprint2 経営ダッシュボードUI

## 目的

Markdownをそのまま表示せず、編集長が判断に必要な情報だけをカードとリストで確認できるUIへ変更する。

## UI

- システム状態カード
- KPIカード
- 今日やることTOP3
- Blocker
- AI社長コメント

## データ取得

- `KPI_DASHBOARD.md`
- `CEO_REPORT.md`
- `RUN_REPORT.md`
- P002 `DAILY_BRIEF.md`
- P003 `DAILY_BRIEF.md`

## 制約

- Markdownは内部で読み込む。
- 必要な情報だけ抽出して表示する。
- 更新は禁止。
- 投稿は禁止。
- 解析表示のみ。
