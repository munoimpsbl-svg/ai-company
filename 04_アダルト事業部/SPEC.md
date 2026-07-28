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
