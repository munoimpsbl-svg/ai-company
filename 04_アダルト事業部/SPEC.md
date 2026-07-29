# P004 アダルト事業部 SPEC

## 目的

アダルト領域のWordPress運営状況を読み取り、改善提案と日次判断材料を作る。

## 入力

- `P004_WORDPRESS_URL`
- 未設定の場合は`P003_WORDPRESS_URL`
- WordPress REST API

## 出力

- `REPORT.md`
- `DAILY_BRIEF.md`

## 取得項目

- 記事一覧
- タイトル
- URL
- 公開日
- カテゴリ
- タグ
- 抜粋
- アダルト候補判定

## 制約

- WordPress更新禁止
- WordPress投稿禁止
- WordPress削除禁止
- 推測禁止
## 記事下書き追加仕様

P004は`ARTICLE_QUEUE.md`を読み込み、`編集長確認欄`が`GO`の行のみWordPressへ下書き作成する。

`P004_WORDPRESS_URL`が未設定の場合、`P003_WORDPRESS_URL`を使用する。

入力:

- `ARTICLE_QUEUE.md`
- `ARTICLE_DRAFTS/*.md`

出力:

- `ARTICLE_DRAFT_RESULT.md`

制約:

- WordPress作成ステータスは`draft`のみ。
- 公開は禁止。
- 既存記事更新は禁止。
- 削除は禁止。
- カテゴリ・タグの新規作成は禁止。
- 推測で本文を生成しない。
- 成人・合法・サイト方針内の内容のみ扱う。
