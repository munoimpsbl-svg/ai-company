# P002 CHANGELOG

## 2026-07-05

### Added

- `03_SNS事業部/`を作成。
- `01_Characters`を作成。
- `02_Posts`を作成。
- `03_Analytics`を作成。
- `04_Daily`を作成。
- `05_Schedule`を作成。
- README.mdを作成。
- SPEC.mdを作成。
- TASK.mdを作成。
- REPORT.mdを作成。
- REVIEW.mdを作成。

### Notes

- 投稿、更新、削除は未実行。
- 既存キャラクター運用を壊さない方針でフォルダのみ作成。

---

## 2026-07-28

### Added

- Google Drive入力同期を追加。
- `sync_drive_inputs.py`を追加。
- Drive入力フォルダ`AI_COMPANY_INPUT/03_SNS事業部/03_Analytics/MIKU/X/`を作成。
- `main.py`実行時にDrive上のCSVをローカル分析フォルダへ同期してからSNS_REPORTを生成する。
- `DRIVE_INPUT_MANIFEST.json`を追加し、Google Drive同期済みCSVのみを分析対象にした。
- ローカルに手動配置したCSVは正データとして扱わない。

### Safety

- SNS投稿なし。
- SNSログイン操作なし。
- ファイル削除なし。
- CSV未取得でも処理継続。

## 2026-07-05

### Added

- TASK-002 SNS_REPORT.md生成機能を実装。
- `03_SNS事業部/main.py`を追加。
- `03_SNS事業部/core/sns_report.py`を追加。
- `02_Daily_Output/YYYY-MM-DD/`のMIKU/RIO出力解析に対応。

### Safety

- SNS投稿なし。
- 画像生成なし。
- WordPress更新なし。
- 解析のみ。

---

## 2026-07-05

### Added

- TASK-003 DAILY_BRIEF.md生成機能を実装。
- `03_SNS事業部/generate_daily_brief.py`を追加。
- `03_SNS事業部/core/sns_daily_brief.py`を追加。
- `SNS_REPORT.md`から今日やることTOP3、Blocker、明日の候補を生成。

### Changed

- Daily Briefの出力名を`SNS_DAILY_BRIEF.md`から`DAILY_BRIEF.md`へ統一。

### Safety

- SNS投稿なし。
- 画像生成なし。
- 分析のみ。
## 2026-07-09

### Added

- `TODAY_POST.md`生成機能を追加。
- `core/today_post.py`と`generate_today_post.py`を追加。
- MIKU / RIOの当日テーマ、採用画像、投稿文、投稿先、投稿チェック欄を追加。

### Changed

- `main.py`からSNS_REPORTとTODAY_POSTを独立して生成するよう変更。

### Safety

- 自動投稿なし。
- SNSログイン操作なし。
- 画像生成なし。
- ファイル削除なし。

---
