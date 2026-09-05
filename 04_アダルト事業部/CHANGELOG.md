# P004 CHANGELOG

## 2026-07-22

### Added

- P004 アダルト事業部を追加。
- `main.py`を追加。
- `generate_daily_brief.py`を追加。
- `REPORT.md` / `DAILY_BRIEF.md`生成に対応。
- P005 AI社長、P006 Runnerへの接続を追加。

### Safety

- WordPress更新なし。
- WordPress投稿なし。
- WordPress削除なし。
- 解析のみ。
## 2026-07-28

- アダルト候補記事の判定を、直接判定と要確認候補に分離。
- `IMPROVEMENT_BACKLOG.md`、`EXECUTION_BOARD.md`、`SEO_PLAN.md`を追加。
- P004 REPORT / DAILY_BRIEF / CEO_REPORTを再生成。
- WordPress更新、投稿、削除は未実行。

## 2026-07-29

- WordPress記事下書き追加フローを追加。
- `ARTICLE_QUEUE.md`、`ARTICLE_DRAFTS/A-001.md`、`create_article_drafts.py`を追加。
- `編集長確認欄=GO`の行だけ下書き作成対象にする。
- `P004_WORDPRESS_URL`未設定時は`P003_WORDPRESS_URL`へフォールバックする。
- dry-runでWordPress認証と処理経路を確認。
- 公開、既存記事更新、削除、カテゴリ・タグ新規作成は未実行。

## 2026-09-05

- P004専用のWordPressユーザー名・アプリケーションパスワードを優先して読み込むよう修正。
- 旧`WORDPRESS_USERNAME`・`WORDPRESS_APP_PASSWORD`は互換用フォールバックとして維持。
- 承認済み既存ページ向けに、完全一致置換・更新前ハッシュ照合・本文減少制限・保存後照合を追加。
- 保存後本文が不一致の場合、安全に復元できる条件下だけ元本文へ戻す処理を追加。
- Dashboardからの自動公開・更新・削除は引き続き無効。
