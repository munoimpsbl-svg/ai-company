# P003 Tasks

## Sprint2 Tasks

## TASK-004 WordPress解析

Status
DONE

Priority
★★★★★

担当
Manager AI / Worker AI

成果物
REPORT.md

完了条件

- [x] WordPressから記事一覧を取得できる
- [x] REPORT.mdを生成できる
- [x] P001の`save_report()`で保存できる
- [x] エラー時に処理が止まらない
- [x] WordPressへ書き込みをしていない

次Task

- TASK-005 SEO改善提案

---

### WordPress Analysis

- [x] WordPress情報取得処理を実装
- [x] タイトル取得処理を実装
- [x] URL取得処理を実装
- [x] 公開日取得処理を実装
- [x] カテゴリ取得処理を実装
- [x] タグ取得処理を実装
- [x] 抜粋取得処理を実装
- [x] 記事一覧取得処理を実装
- [x] 内部リンク候補抽出処理を実装
- [x] 解析結果のREPORT.md生成処理を実装
- [x] P001 Core Platformの`save_report()`保存に接続

### Safety

- [x] WordPress書き込みなし
- [x] 投稿なし
- [x] 更新なし
- [x] 削除なし
- [x] 解析のみ

### 編集長確認待ち

- [ ] `P003_WORDPRESS_URL`
- [ ] Google Drive保存の認証設定
- [ ] 取得記事数の上限

---

## Sprint 1

## TASK-001 サイトレビュー

Status
TODO

Priority
★★★★★

Start
2026-07-06

Deadline
2026-07-07

担当
Manager AI

成果物
REPORT.md

完了条件

- [ ] トップページ確認
- [ ] グラビア一覧確認
- [ ] 記事ページ確認
- [ ] 導線確認

---

## TASK-002 SEOレビュー

Status

TODO

Priority

★★★★★

Start

2026-07-06

Deadline

2026-07-07

担当

Manager AI

成果物
REPORT.md

完了条件

- [ ] タイトル確認
- [ ] Hタグ確認
- [ ] メタ情報確認
- [ ] 内部リンク確認

---

## TASK-003 CTR分析

Status

TODO

Priority

★★★★★

Start

2026-07-06

Deadline

2026-07-07

担当

Manager AI

成果物
REPORT.md

完了条件

- [ ] CTA確認
- [ ] ボタン配置確認
- [ ] 導線確認
- [ ] 改善案作成

# Sprint 1 完了条件

- [ ] TASK-001 完了
- [ ] TASK-002 完了
- [ ] TASK-003 完了
- [ ] REPORT.md 出力
- [ ] REVIEW.md 更新

---

## TASK-101 カテゴリ未設定記事の改善案

Status
DONE

Priority
★★★★★

目的

WordPress内のUncategorized記事を洗い出し、適切なカテゴリ候補を提案する。

成果物

- `CATEGORY_FIX_PLAN.md`

完了条件

- [x] Uncategorized記事を洗い出す
- [x] 対象記事ごとに推奨カテゴリを提案する
- [x] 推測できない場合は「要確認」と記載する
- [x] WordPress更新を行わない
- [x] カテゴリ変更を行わない
- [x] 投稿・削除を行わない

---

## TASK-102 内部リンク改善案

Status
DONE

Priority
★★★★★

目的

関連記事同士の回遊率を向上させる。

成果物

- `INTERNAL_LINK_PLAN.md`

完了条件

- [x] WordPress記事一覧を確認する
- [x] カテゴリ情報を確認する
- [x] タグ情報を確認する
- [x] `CATEGORY_FIX_PLAN.md`を参照する
- [x] 対象記事ごとに推奨リンク先を提案する
- [x] 判断できない場合は「要確認」と記載する
- [x] WordPress更新を行わない
- [x] リンク追加を行わない
- [x] 投稿・削除を行わない

---

## TASK-103 記事タイトル改善案

Status
DONE

Priority
★★★★★

目的

検索CTRの向上を目的として、現在のタイトルを分析し改善案を作成する。

成果物

- `TITLE_IMPROVEMENT_PLAN.md`

完了条件

- [x] WordPress記事一覧を確認する
- [x] Search Consoleデータを確認する
- [x] `CATEGORY_FIX_PLAN.md`を参照する
- [x] 改善タイトル案を作成する
- [x] 改善案がない場合は「現状維持」と記載する
- [x] WordPress更新を行わない
- [x] タイトル変更を行わない
- [x] 投稿・削除を行わない

---

## TASK-201 カテゴリ変更実行

Status
DONE / EFFECT MEASUREMENT

Priority
★★★★★

目的

`CATEGORY_FIX_PLAN.md`のうち、編集長がGOを付けた記事のみカテゴリを変更する。

成果物

- `CATEGORY_FIX_RESULT.md`

実行結果

- GO対象記事: 5件
- WordPressカテゴリ更新: 実行
- 更新成功: 5件
- 更新失敗: 0件

完了条件

- [x] `CATEGORY_FIX_PLAN.md`を確認する
- [x] GO記事のみを対象にする
- [x] STOP / 要確認 / 承認未確定は変更しない
- [x] `CATEGORY_FIX_RESULT.md`を生成する
- [x] タイトル変更を行わない
- [x] 本文変更を行わない
- [x] 削除を行わない

---

## TASK-301 改善バックログ作成

Status
DONE

Priority
★★★★★

目的

P003の改善施策を一覧管理し、編集長の承認状態と実装状況を追跡できるようにする。

成果物

- `IMPROVEMENT_BACKLOG.md`

初期登録

- 101 カテゴリ改善
- 102 内部リンク改善
- 103 タイトル改善
- 104 メタディスクリプション改善
- 105 CTA改善
- 106 画像alt改善
- 107 構造化データ改善
- 108 関連記事強化

完了条件

- [x] `IMPROVEMENT_BACKLOG.md`を作成する
- [x] ID、タスク、優先度、状態、効果、備考を記載する
- [x] 状態定義を記載する
- [x] READMEを更新する
- [x] TASKを更新する
- [x] CHANGELOGを更新する
- [x] REVIEWを更新する

---

## TASK-302 改善実行ボード作成

Status
DONE

Priority
★★★★★

目的

編集長が毎朝確認するだけで、今日実行する改善と承認待ちの改善を判断できるようにする。

成果物

- `EXECUTION_BOARD.md`

完了条件

- [x] 今日実行を一覧表示する
- [x] 今週実行を一覧表示する
- [x] 承認待ちを一覧表示する
- [x] 効果測定中を一覧表示する
- [x] 完了を一覧表示する
- [x] `IMPROVEMENT_BACKLOG.md`と連動した状態表示にする
- [x] WordPress更新を行わない
- [x] 表示のみで作成する

---

## TASK-202 内部リンク追加実行

Status
DONE

Priority
★★★★★

目的

`INTERNAL_LINK_PLAN.md`のうち、編集長がGOした記事のみWordPress本文へ内部リンクを追加する。

成果物

- `INTERNAL_LINK_RESULT.md`

実行結果

- GO対象記事: 0件
- WordPress本文更新: 未実行

完了条件

- [x] `INTERNAL_LINK_PLAN.md`を確認する
- [x] GO記事のみを対象にする
- [x] GO未確認の記事は変更しない
- [x] `INTERNAL_LINK_RESULT.md`を生成する
- [x] 本文以外を変更しない
- [x] タイトル変更を行わない
- [x] カテゴリ変更を行わない
- [x] 投稿を行わない
- [x] 削除を行わない

---

## TASK-303 承認同期

Status
DONE

Priority
★★★★★

目的

Command Centerのタスク単位GOを、改善PLANの記事単位GOへ反映し、更新専用タスクが実行対象を読める状態にする。

成果物

- `PLAN_APPROVAL_SYNC_RESULT.md`

完了条件

- [x] `APPROVALS.md`の101 GOを`CATEGORY_FIX_PLAN.md`へ反映する
- [x] `APPROVALS.md`の102 GOを`INTERNAL_LINK_PLAN.md`へ反映する
- [x] `APPROVALS.md`の103 GOを`TITLE_IMPROVEMENT_PLAN.md`へ反映する
- [x] 記事単位の編集長確認欄を`GO`へ変換する
- [x] WordPress更新を行わない
- [x] 投稿・削除を行わない
## 2026-07-28 TASK-203 タイトル改善実行

- [x] `TITLE_IMPROVEMENT_PLAN.md`のGO対象を抽出
- [x] WordPress記事を現在タイトルで照合
- [x] GO対象9件のタイトルのみ更新
- [x] `TITLE_IMPROVEMENT_RESULT.md`を生成
- [x] `IMPROVEMENT_BACKLOG.md`の103を効果測定中へ更新
- [x] `EXECUTION_BOARD.md`へ反映

制約:

- 本文変更禁止
- カテゴリ変更禁止
- タグ変更禁止
- 投稿禁止
- 削除禁止

## 2026-07-29 TASK-204 記事下書き追加

Status
DONE

目的

グラビア事業部の記事候補をWordPressへ下書きとして追加できる状態にする。

成果物

- `ARTICLE_QUEUE.md`
- `ARTICLE_DRAFTS/G-001.md`
- `create_article_drafts.py`
- `ARTICLE_DRAFT_RESULT.md`

完了条件

- [x] 編集長GO行のみ対象にする
- [x] WordPress作成ステータスを`draft`に固定する
- [x] 公開しない
- [x] 既存記事を更新しない
- [x] 削除しない
- [x] カテゴリ・タグを新規作成しない
- [x] dry-runで認証と処理経路を確認する
