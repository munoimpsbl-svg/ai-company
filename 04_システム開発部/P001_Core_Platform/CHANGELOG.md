# P001 CHANGELOG

Current Version: v0.1.0
Project: P001 Core Platform

---
## 2026-07-05

### Added

- P001 Core Platformのプロジェクト管理フォルダを作成
- PROJECT.mdを作成
- SPEC.mdを作成
- TASK.mdを作成
- REPORT.mdを作成
- CHANGELOG.mdを作成

### Changed

- P001 Sprint1を開始
- 標準プロジェクトファイル検出、日報生成、CHANGELOG追記を実装
- 投稿、公開、削除、移動、自動承認は未実行

### Notes

- Sprint1はGoogle Drive読み込み、日次レポート標準化、安全な運用範囲の明文化を対象とする
- 既存SNS事業部、特にMIKU運用を壊さないことを最優先とする

---

## 2026-07-06

### Added

- Core Platform基本構成を追加
- REPORT.md出力ルールを追加
- REVIEW.md出力ルールを追加

### Changed

- P001をGoogle Drive単体ではなくCore Platformとして定義

### Fixed

- なし

### Impact

Affected Projects

- P003 グラビア事業部
- P004 アダルト事業部
- P002 SNS事業部

---

## 2026-07-05

### Added

- P001 Core Platform Sprint2を実装
- `.env`読み込みを追加
- `.env.example`を追加
- `core.drive.create_folder_if_not_exists()`を追加
- `core.drive.save_markdown()`を追加
- `core.drive.load_markdown()`を追加
- `core.drive.save_report()`を追加
- `core.drive.save_review()`を追加
- Google Drive未接続時の`output/reports/`フォールバック保存を追加

### Changed

- `.gitignore`に`.env`、`.env.*`、`output/`を追加
- Google Drive保存処理を、未接続時に停止しない設計へ変更

### Verification

- `python3 -m compileall core`
- `save_report("P001", "REPORT.md", ...)`
- `save_review("P001", "REVIEW.md", ...)`
- `load_markdown()`によるローカル保存ファイル読み込み
