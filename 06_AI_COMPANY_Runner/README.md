# P006 AI COMPANY Runner

## TASK-001

会社全体を順番に実行するRunner。

## 実行順

1. P002 SNS事業部
2. P003 グラビア事業部
3. KPI Dashboard生成
4. P004 アダルト事業部
5. P005 AI社長
6. ログ保存

## 実行

```bash
python3 06_AI_COMPANY_Runner/main.py
```

## 出力

- `06_AI_COMPANY_Runner/RUN_REPORT.md`
- `02_Daily_Output/YYYY-MM-DD/RUN_REPORT.md`
- `KPI_DASHBOARD.md`
- `02_Daily_Output/YYYY-MM-DD/KPI_DASHBOARD.md`

## 方針

エラーがあっても次の部署を実行する。

途中停止は禁止。

## Sprint7 承認同期

RunnerはP003実行前に`04_グラビア事業部/APPROVALS.md`を確認する。

`GO`の改善案件のみ、`01_グラビア事業部/P003_グラビア事業部/EXECUTION_BOARD.md`の`今日実行`へ移動し、状態を`実装待ち`にする。

`STOP`と`要確認`は実行対象にしない。

この同期ではWordPress更新、投稿、削除は行わない。

## Google Drive同期対象

Runnerは日次成果物のMarkdownをGoogle Driveへ保存する。

同期対象外:

- `.git/`
- `.secrets/`
- `.venv/`
- `dist/`
- `installer/`
- `output/`
- キャッシュ系ディレクトリ

## PLAN記事単位GO同期

RunnerはP003実行前に`06_AI_COMPANY_Runner/plan_approval_sync.py`も実行する。

この処理は`APPROVALS.md`のタスク単位GOを、以下の改善PLANの記事単位GOへ反映する。

- `CATEGORY_FIX_PLAN.md`
- `INTERNAL_LINK_PLAN.md`
- `TITLE_IMPROVEMENT_PLAN.md`

同期結果は以下に保存する。

- `01_グラビア事業部/P003_グラビア事業部/PLAN_APPROVAL_SYNC_RESULT.md`

この同期ではWordPress更新、投稿、削除は行わない。
