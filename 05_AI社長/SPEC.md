## CEO_REPORT仕様

AI社長は DAILY_BRIEF.md を読み込み、
編集長が30秒以内で意思決定できるCEO_REPORT.mdを生成する。

CEO_REPORTは以下の構成とする。

# CEO REPORT

日付

## 本日の総評

## WordPress KPI

## Search Console KPI

## GA4 KPI

## 本日の最優先（Priority1）

担当

作業時間

期待ROI

理由

承認（GO / STOP）

## 優先順位2

（同様）

## 優先順位3

（同様）

## Blocker

## 本日の経営判断

新規記事作成

既存記事改善

CTR改善

SEO改善

各項目をGO / STOPで表示する。

## 明日の予定

## CTOコメント

AI社長は分析を行わず、
各部署のDAILY_BRIEF.mdを要約し、
経営判断のみを出力する。

## 入力

AI社長は以下のファイルのみを入力として使用する。

- 03_SNS事業部/04_Daily/DAILY_BRIEF.md
- 04_グラビア事業部/DAILY_BRIEF.md
- 04_アダルト事業部/DAILY_BRIEF.md
- KPI_DASHBOARD.md

不足しているファイルがある場合は推測せず、
DAILY_BRIEF.mdは「未提出」、KPIは「未取得」として扱う。

---

## 出力

CEO_REPORT.md

保存先

02_Daily_Output/YYYY-MM-DD/CEO_REPORT.md

---

## AI社長の制約

AI社長は以下の操作を実行してはならない。

- WordPressへの投稿
- WordPressの更新
- WordPressの記事削除
- SNSへの投稿
- Google Drive内のファイル更新・削除
- REPORT.md や DAILY_BRIEF.md の書き換え

AI社長は各部署から提出された DAILY_BRIEF.md を読み込み、
CEO_REPORT.md を生成する意思決定専用AIとする。

不足している情報がある場合は推測せず、
「未提出」または「情報不足」と明記する。

## KPI Dashboard統合仕様

AI社長は`KPI_DASHBOARD.md`を読み込み、CEO_REPORTへ以下を表示する。

- WordPress KPI
- Search Console KPI
- GA4 KPI

KPI値は`KPI_DASHBOARD.md`の`Source KPI`表から取得する。

取得できない項目は推測せず「未取得」と表示する。
