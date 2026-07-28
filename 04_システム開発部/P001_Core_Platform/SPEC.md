# P001 SPEC

## 目的

Core Platformは、AI COMPANYの全AI社員が共通で使う運営基盤である。

Sprint1では、Google Drive上のAI COMPANY構成を壊さず読み込み、日次運用へ接続できる最小基盤を定義する。

## 対象

- AI_COMPANYフォルダ
- Daily_Brief.md
- 事業部フォルダ
- キャラクター設定フォルダ
- 日次レポート
- 改善履歴
- AI社長向け報告

## 非対象

- 投稿の自動実行
- WordPressの自動更新
- Drive構成の自動変更
- 画像生成の自動実行
- 承認なしの外部サービス操作

## 基本原則

- Google Driveを唯一の正とする。
- 既存構成を壊さない。
- 既存SNS事業部、特にMIKU運用を変更しない。
- AIは読み込み、分析、提案、報告を行う。
- 投稿、公開、削除、更新は承認後に行う。

## Sprint1機能

### Drive読み込み

- AI_COMPANYフォルダを確認する。
- 直下フォルダを一覧化する。
- Daily_Brief.mdを読み込む。
- 指定キャラクターまたは事業部フォルダを読み込む。
- 読み込み結果をログ表示する。

### 日次出力

- 事業部ごとにREPORT.mdを作成できる。
- 変更がある場合はCHANGELOG.mdに記録する。
- AI社長が読める形で日報を整理する。

### 安全制御

- Sprint1では投稿、公開、削除、移動をしない。
- Drive上にフォルダを勝手に追加しない。
- 必要な追加は編集長へ提案する。

## Sprint2機能

### Google Drive保存

REPORT.md / REVIEW.mdをGoogle Driveへ保存できる共通ライブラリを提供する。

実装関数:

- `create_folder_if_not_exists(folder_name, parent_id=None)`
- `save_markdown(filename, content, folder_id=None)`
- `load_markdown(file_id)`
- `save_report(project_id, filename, content)`
- `save_review(project_id, filename, content)`

### 認証

- OAuth認証に対応する。
- 認証情報はコードに直書きしない。
- `.env`または環境変数で管理する。
- `.env.example`に設定例を置く。

### ローカルフォールバック

Google Drive未接続時はエラーで停止しない。

以下へ保存する。

```text
output/reports/
```

## 標準プロジェクトファイル

各プロジェクトは以下を持つ。

- PROJECT.md
- SPEC.md
- TASK.md
- REPORT.md
- CHANGELOG.md

必要に応じて以下を追加する。

- REVIEW.md

## レポート標準

REPORT.mdには以下を含める。

- 実行日
- 今日の結論
- 読み込み元
- 実行結果
- 未接続または未取得の情報
- 改善候補
- 承認待ち事項
- 次回作業

## Sprint1完了条件

- P001の管理ドキュメントが作成されている。
- 現行のDrive読み込み処理が仕様として整理されている。
- 各事業部プロジェクトが標準ファイル構成で管理できる。
- 投稿や公開を行わない安全な運用範囲が明確になっている。
