# P005 SPEC

## TASK-001 Daily Brief Reader

AI COMPANY内の`DAILY_BRIEF.md`を読み取り、AI社長が確認するREPORT.mdを生成する。

## 入力

- 各事業部の`DAILY_BRIEF.md`

## 出力

- P005 `REPORT.md`
- P005 `CHANGELOG.md`

## 処理

- ワークスペース内の`DAILY_BRIEF.md`を探索する。
- 隠しフォルダ、`.venv`、`output`、キャッシュ類は対象外にする。
- 「今日やること TOP3」「Blocker」「明日の候補」を抽出する。
- AI社長向けに部署別要約を生成する。

## 禁止事項

- 各事業部のDaily Briefを変更しない。
- WordPressを更新しない。
- 投稿しない。
- 自動承認しない。
