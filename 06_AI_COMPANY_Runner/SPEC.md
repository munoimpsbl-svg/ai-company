# P006 SPEC

## TASK-001 AI COMPANY Runner

## 目的

会社全体を決められた順番で実行し、成功、失敗、エラー内容をRUN_REPORT.mdへ記録する。

## 実行順

1. P002 SNS事業部
2. P003 グラビア事業部
3. P005 AI社長
4. KPI Dashboard生成
5. ログ保存

## 出力

- RUN_REPORT.md
- KPI_DASHBOARD.md

## RUN_REPORT項目

- 開始時間
- 終了時間
- 成功
- 失敗
- エラー内容

## Failure Handling

- 各部署でエラーが発生しても次の部署を実行する。
- Runner全体は途中停止しない。
- エラー内容はRUN_REPORT.mdへ記録する。

## TASK-002 Google Drive完全対応

## 目的

Runnerが生成する全成果物をGoogle Driveへ保存する。

## 対象

- REPORT.md
- DAILY_BRIEF.md
- CEO_REPORT.md
- RUN_REPORT.md
- KPI_DASHBOARD.md
- SNS_DAILY_BRIEF.md
- SNS_REPORT.md

## 方針

- ローカル保存は維持する。
- Google Drive保存に失敗しても処理は継続する。
- 保存結果はRUN_REPORT.mdへ記録する。

## TASK-003 APPROVALS GO同期

## 目的

編集長がダッシュボードで承認した改善案件を、Runnerが実行対象として認識できる状態にする。

## 入力

- `04_グラビア事業部/APPROVALS.md`
- `01_グラビア事業部/P003_グラビア事業部/IMPROVEMENT_BACKLOG.md`

## 出力

- `01_グラビア事業部/P003_グラビア事業部/EXECUTION_BOARD.md`

## 状態遷移

`APPROVALS.md`で`GO`の案件のみ、`EXECUTION_BOARD.md`の`今日実行`へ移動し、状態を`実装待ち`にする。

`STOP`と`要確認`は実行対象にしない。

## 制約

- WordPress更新は禁止。
- 投稿は禁止。
- 削除は禁止。
- 今回は状態遷移のみ。
