# P003 グラビア事業部

WordPressサイトをAI COMPANY標準の運営体制へ移行し、日次で改善・分析・提案を行うためのプロジェクトです。

## 目的

- SEO改善
- CTR改善
- 記事品質改善
- 改善履歴蓄積
- 編集長が短時間で判断できる改善提案の作成

## 主要成果物

- `REPORT.md`: WordPress解析レポート
- `CATEGORY_FIX_PLAN.md`: カテゴリ改善案
- `INTERNAL_LINK_PLAN.md`: 内部リンク改善案
- `TITLE_IMPROVEMENT_PLAN.md`: タイトル改善案
- `CATEGORY_FIX_RESULT.md`: カテゴリ変更実行結果
- `PLAN_APPROVAL_SYNC_RESULT.md`: 承認同期結果
- `IMPROVEMENT_BACKLOG.md`: 改善バックログ

## 改善バックログ

改善施策は`IMPROVEMENT_BACKLOG.md`で管理します。

状態は以下のいずれかとします。

- 提案
- 承認待ち
- 実装待ち
- 実装済み
- 効果測定中
- 完了

## 制約

- WordPress自動公開は禁止
- 自動記事公開は禁止
- 記事追加は`ARTICLE_QUEUE.md`で編集長GO済みのものだけ下書き作成する
- 自動承認は禁止
- 編集長GOがないWordPress更新は禁止

## 記事下書き追加

入力:

- `ARTICLE_QUEUE.md`
- `ARTICLE_DRAFTS/*.md`

実行:

```bash
python3 01_グラビア事業部/P003_グラビア事業部/create_article_drafts.py --dry-run
python3 01_グラビア事業部/P003_グラビア事業部/create_article_drafts.py
```

ルール:

- `編集長確認欄`が`GO`の行のみ対象。
- WordPress作成ステータスは`draft`のみ。
- 公開は行わない。
- 既存記事の更新・削除は行わない。
- カテゴリ・タグの新規作成は行わない。

## 承認同期

Command Centerの`APPROVALS.md`でGOになった改善タスクは、Runnerの`plan_approval_sync.py`により各PLANの記事単位GOへ反映されます。

この同期は承認状態の記録のみで、WordPress更新、投稿、削除は行いません。
## 2026-07-28 SEO実行

- `execute_title_improvement.py`を追加。
- `TITLE_IMPROVEMENT_PLAN.md`で編集長GO済みの記事のみ、WordPressタイトルを更新する。
- 本文、カテゴリ、タグ、投稿状態、削除操作は変更しない。
- 実行結果は`TITLE_IMPROVEMENT_RESULT.md`へ記録する。
