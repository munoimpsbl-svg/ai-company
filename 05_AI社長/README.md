# P005 AI社長

## TASK-002 CEO_REPORT生成

各部署の`DAILY_BRIEF.md`を読み取り、`CEO_REPORT.md`を生成する。

## 入力

- `03_SNS事業部/04_Daily/DAILY_BRIEF.md`
- `04_グラビア事業部/DAILY_BRIEF.md`
- `04_アダルト事業部/DAILY_BRIEF.md`
- `KPI_DASHBOARD.md`

存在しない場合は「未提出」として扱う。
KPIが取得できない場合は「未取得」として扱う。

## 出力

```text
02_Daily_Output/YYYY-MM-DD/CEO_REPORT.md
```

## 実行

```bash
python3 05_AI社長/main.py
```

## 制約

- WordPress更新は禁止。
- WordPress投稿は禁止。
- WordPress削除は禁止。
- SNS投稿は禁止。
- Google Drive変更は禁止。
- Google Drive削除は禁止。
- REPORT.md書き換えは禁止。
- DAILY_BRIEF.md書き換えは禁止。

AI社長は意思決定のみ担当する。

## KPI Dashboard統合

CEO_REPORTへ以下を追加する。

- WordPress KPI
- Search Console KPI
- GA4 KPI

KPI Dashboardの値のみを使用し、推測は行わない。
## 2026-07-28 Priority表示

CEO_REPORTは、P002 / P003 / P004のDaily Briefから部署横断でPriorityを抽出する。
これにより、SNSだけでなくグラビア・アダルトのSEO課題も経営判断に表示される。
