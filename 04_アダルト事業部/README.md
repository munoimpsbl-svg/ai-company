# P004 アダルト事業部

アダルト領域をAI COMPANY標準運営へ載せるための部署です。

## 目的

- SEO改善
- CTR改善
- PV改善
- 回遊率改善
- 対象記事の改善履歴蓄積

## 実行

```bash
python3 04_アダルト事業部/main.py
python3 04_アダルト事業部/generate_daily_brief.py
```

## 出力

- `REPORT.md`
- `DAILY_BRIEF.md`

## 制約

- DashboardからのWordPress公開・更新は禁止。
- 記事追加は`ARTICLE_QUEUE.md`で編集長GO済みのものだけ下書き作成する。
- 既存記事更新は、対象ページIDと差分について編集長GOが記録されている場合のみ行う。
- WordPress削除は禁止。
- 成人・合法・サイト方針内の内容のみ扱う。

## 記事下書き追加

入力:

- `ARTICLE_QUEUE.md`
- `ARTICLE_DRAFTS/*.md`

実行:

```bash
python3 04_アダルト事業部/create_article_drafts.py --dry-run
python3 04_アダルト事業部/create_article_drafts.py
```

ルール:

- `編集長確認欄`が`GO`の行のみ対象。
- WordPress作成ステータスは`draft`のみ。
- 公開は行わない。
- 既存記事の更新・削除は行わない。
- カテゴリ・タグの新規作成は行わない。

## 承認済み既存ページ更新

- `P004_WORDPRESS_USERNAME`と`P004_WORDPRESS_APP_PASSWORD`を使用する。
- 更新前に`context=edit`で生本文を取得し、本文ハッシュと更新日時を記録する。
- 全文生成ではなく、一致件数を指定した部分置換だけを使用する。
- `[Truncated]`混入、想定外の本文減少、計画後の変更を検出した場合は保存しない。
- 保存後にREST APIから再取得し、更新予定の本文と完全一致することを確認する。
- 公開ステータス変更と削除は行わない。

## 2026-07-28 SEO運用

- グラビア事業部と同じ改善バックログ方式を追加。
- `IMPROVEMENT_BACKLOG.md`、`EXECUTION_BOARD.md`、`SEO_PLAN.md`を作成。
- 対象記事判定は、タイトル・カテゴリ・タグで直接判定できる記事のみを対象とする。
- 抜粋のみ対象語が出る記事は`要確認候補`として扱う。
