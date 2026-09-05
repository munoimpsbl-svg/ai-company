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

- DashboardからのWordPress更新禁止
- 承認のないWordPress投稿・更新禁止
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

## 承認済み既存ページ更新仕様

対象ページIDと差分について編集長GOが記録されている場合のみ実行できる。

- 認証は`P004_WORDPRESS_USERNAME`と`P004_WORDPRESS_APP_PASSWORD`を優先する。
- 更新前の本文ハッシュ・更新日時が変わった場合は中止する。
- 指定した文字列の一致件数が想定と異なる場合は中止する。
- 切断マーカーまたは許容範囲を超える本文減少を検出した場合は中止する。
- 保存後の生本文が計画と一致しない場合は、安全に復元できる場合だけ元本文へ戻す。
