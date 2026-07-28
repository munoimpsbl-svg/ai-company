# P002 REVIEW

## TASK-001 Review

## 確認結果

- SNS運営フォルダ構成を作成済み。
- 管理ドキュメント一式を作成済み。
- 投稿、更新、削除は未実行。

## 残課題

- 既存Drive側の`03_SNS事業部/01_Characters`との同期確認。
- `03_Analytics`への分析結果保存。
- `04_Daily`へのDAILY_BRIEF.md生成。

---

## TASK-002 Review

## 確認結果

- SNS_REPORT.md生成機能を実装済み。
- 既存の日次出力のみを読み取り、SNS投稿や画像生成は未実行。
- エラー時は停止せず、Blockerへ理由を書き込む。

## 残課題

- SNS実投稿済みデータとの接続。
- `03_Analytics`への分析結果保存。

---

## TASK-003 Review

## 確認結果

- DAILY_BRIEF.md生成機能を実装済み。
- SNS_REPORT.mdのみを入力として使用。
- SNS投稿、画像生成は未実行。
- P005が読める命名規則へ統一済み。

## 残課題

- 実投稿データ接続後の優先順位ロジック改善。
## P002 + P007 SNS連動 Review

- 当日の日付フォルダからMIKU / RIOを取得できる。
- `prompt.txt`からテーマを取得できる。
- `report.md`の優先候補だけを採用画像一覧へ反映できる。
- Instagram / X / Threadsの存在する投稿文だけを投稿先へ反映できる。
- 欠損項目は`未取得`またはBlockerとして扱う。
- SNSへの通信、ログイン、投稿、削除処理は存在しない。

---
## 2026-07-28 CTOレビュー用メモ

- SNS分析入力をGoogle Drive基準に変更。
- `AI_COMPANY_INPUT/03_SNS事業部/03_Analytics/MIKU/X/`からCSVを同期する。
- 同期先はローカル分析ミラー`03_SNS事業部/03_Analytics/MIKU/X/`。
- 正データはGoogle Drive。分析対象は`DRIVE_INPUT_MANIFEST.json`に記録されたCSVのみ。
- ローカルに手動配置したCSVは分析対象外。
- CSV未取得でもエラー停止しない。
- SNS投稿、SNSログイン、削除は未実行。
