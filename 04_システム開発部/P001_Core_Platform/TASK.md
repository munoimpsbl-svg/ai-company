# P001 Tasks

## Sprint2 Tasks

### Drive Library

- [x] OAuth認証に対応
- [x] 認証情報をコードに直書きしない
- [x] `.env` 読み込みに対応
- [x] `create_folder_if_not_exists(folder_name, parent_id=None)` 実装
- [x] `save_markdown(filename, content, folder_id=None)` 実装
- [x] `load_markdown(file_id)` 実装
- [x] `save_report(project_id, filename, content)` 実装
- [x] `save_review(project_id, filename, content)` 実装
- [x] Google Drive未接続時のローカルフォールバック実装

### Fallback

- [x] `output/reports/` へ保存
- [x] REPORT.md保存確認
- [x] REVIEW.md保存確認
- [x] load_markdownのローカル読み込み確認

---

## Sprint1 Tasks

## Platform Manager AI

- [ ] AI_COMPANYフォルダ確認
- [ ] Daily_Brief.md読み込み確認
- [ ] 事業部フォルダ一覧確認
- [ ] 既存MIKU運用の保護確認
- [x] 標準プロジェクトファイル確認
- [x] 日報生成ルール確認
- [ ] Google Drive保存ルール確認

---

## Worker AI

### Drive

- [ ] Google Drive接続確認
- [ ] AI_COMPANYフォルダ検出確認
- [ ] 直下フォルダ一覧取得
- [ ] テキストファイル読み込み確認

### Project Docs

- [x] PROJECT.md形式確認
- [x] SPEC.md形式確認
- [x] TASK.md形式確認
- [x] REPORT.md形式確認
- [x] CHANGELOG.md形式確認

### Safety

- [x] 投稿処理が実行されないことを確認
- [x] Drive変更処理が実行されないことを確認
- [x] 既存ファイル移動が行われないことを確認
- [x] 未承認操作がないことを確認

---

## AI社長

- [ ] 各事業部日報の受信形式確認
- [ ] CEOレポート形式確認
- [ ] 優先順位決定ルール確認

---

## 編集長確認待ち

- [ ] P001の日次実行時刻
- [ ] Google Drive保存先の正式ルール
- [ ] AI社長レポートの保存先
- [ ] P003以外の事業部プロジェクトID
- [ ] 自動化してよい処理範囲

---

## Sprint1完了条件

- [x] Core PlatformのPROJECT / SPEC / TASK / REPORT / CHANGELOGがある。
- [x] Drive読み込み仕様が明文化されている。
- [x] 日次レポート標準が明文化されている。
- [x] 未承認の投稿、公開、削除、移動をしない方針が明文化されている。
- [ ] 次Sprintで自動化候補を検討できる。
