# P007 Editor Dashboard CHANGELOG

## 2026-07-06

### Added

- Sprint3 ビジュアル強化を実装。
- KPI色付きカードを追加。
- システム状態の 🟢 🟡 🔴 表示を追加。
- MIKU / RIO サムネイル表示を追加。
- 詳細レポートの展開表示を追加。

### Changed

- TOP3とBlockerをカードUIへ変更。

---

## 2026-07-06

### Added

- Sprint4 通知センターを追加。
- Runner実行、KPI更新、CEO_REPORT再生成ボタンを追加。
- RUN_REPORT、KPI_DASHBOARD、CEO_REPORTの詳細表示ボタンを追加。
- WordPressサイト、WordPress管理画面リンクを追加。

### Changed

- 操作結果を画面上に表示するように変更。

---

## 2026-07-07

### Added

- Sprint5 改善案件ボードを追加。
- `IMPROVEMENT_BACKLOG.md`、`EXECUTION_BOARD.md`、`TASK.md`の読み込みを追加。
- 今日の改善案件カードを追加。
- 優先度、状態、推定時間、期待ROI、効果の表示を追加。
- 表示専用のGOボタンを追加。

### Changed

- メイン画面の表示順をAI COMPANY、KPI、今日やること、改善案件、Blocker、AI社長コメントへ整理。
- 通知センターと操作ボタンをサイドバーへ移動。

### Safety

- WordPress更新なし。
- 投稿なし。
- 削除なし。

---

## 2026-07-08

### Added

- Sprint6 改善案件GO承認機能を追加。
- 改善案件カードにGO / STOP / 要確認ボタンを追加。
- 改善案件カードにコメント欄を追加。
- `04_グラビア事業部/APPROVALS.md`への承認状態保存を追加。
- 保存済み承認状態のカード表示を追加。

### Safety

- WordPress更新なし。
- 投稿なし。
- 削除なし。
- 状態記録のみ。

---

## 2026-07-08

### Added

- Sprint7 Runner連携を追加。
- `APPROVALS.md`のGO案件をP006 Runnerが`EXECUTION_BOARD.md`へ反映する流れを追加。

### Safety

- WordPress更新なし。
- 投稿なし。
- 削除なし。
- 状態遷移のみ。

---

## 2026-07-09

### Added

- Sprint7 GO承認後の状態確認機能を追加。
- 改善案件カードへ状態ラベル、最終更新日時、`GO反映済み`表示を追加。
- 画面下部へ`APPROVALS.md`承認履歴を追加。

### Changed

- GO承認済み案件を`GO済み`かつ`実装待ち`として表示。
- `04_グラビア事業部`の改善入力を優先し、既存配置へフォールバックするよう変更。

### Safety

- WordPress更新なし。
- 投稿なし。
- 削除なし。
- 状態表示のみ。

### Added

- `SNS Today`画面を追加。
- MIKU / RIOタブ、採用画像、投稿文、SNSリンクを追加。
- 投稿完了チェックと`POST_RESULT.md`記録機能を追加。

### Safety

- 自動投稿なし。
- SNSログイン操作なし。
- ファイル削除なし。

### Fixed

- `SNS Today`の画面切替をサイドバーから画面上部へ移動。
- スマホやサイドバーを閉じた状態でもSNS連動画面へ移動できるよう改善。
## 2026-07-28

- `SNS Input Manager`画面を追加。
- Google Drive上のSNS分析CSVをビジュアル管理できるようにした。
- Drive CSV一覧、アップロード、上書き、プレビュー、同期、manifest表示に対応。
- 削除は無効化。
- `.venv`へ`streamlit`をインストールし、起動確認を実施。

## 2026-07-28

- 携帯表示用のLAN公開起動手順を追加。
- `scripts/run_mobile_dashboard.sh`を`screen`常駐方式へ更新。
- `scripts/stop_mobile_dashboard.sh`を`screen`停止方式へ更新。
- `http://192.168.1.9:8510`でHTTP 200を確認。

## 2026-07-28

- Render外部公開用の`render.yaml`を追加。
- `Procfile`、`runtime.txt`、`.streamlit/config.toml`を追加。
- `DASHBOARD_PASSWORD`によるログイン画面を追加。
- Google OAuth token JSONの環境変数読み込みに対応。
- `DEPLOY_RENDER.md`を追加。
## 2026-07-28

- `Company Hub`画面を追加。
- 携帯表示向けのサマリーカードとレスポンシブCSSを追加。
- 会社全体の情報集約タブを追加。
- 今日の流れをCSSアニメーション付きで表示。
- X結果貼り付け保存機能を追加。
- X結果をMarkdown / CSVへ蓄積する保存先を追加。

## 2026-07-29

- Command Center / Company Hubのビジュアルを強化。
- 動きのあるコンソールヘッダーを追加。
- KPI / SNS / X / SEO / CEO / Driveのナビカードを追加。
- MIKU / RIO画像プレビューを追加。
- スマホ向けレスポンシブCSSを追加。

## 2026-07-29

- Command Center / Company HubへAI美女品質監査を追加。
- AI-VQC、Generation Quality、MIKU固定ルール、RIO固定ルールをダッシュボードへ集約。
- 本人感未確認、別人化リスク、AI感・不自然表現リスクの集計カードを追加。
- 要確認画像カードと投稿前チェックを追加。
- AI COMPANY情報集約へ`AI美女`タブを追加。

## 2026-07-29

- Command Center / Company Hubのビジュアルをさらに強化。
- 上部に5つの状態カードを追加。
- 状態カードへ動くゲージとスキャンアニメーションを追加。
- 画像プレビューを`Creative Deck`表示へ変更。
- ヒーロー背景へ動くグリッドを追加。

## 2026-07-29

- `AI社員 Live Run`を追加。
- Runner実行をバックグラウンド起動へ変更。
- Runner進捗JSONを追加。
- 実行中のAI社員カードと自動更新を追加。
- 完了済みRUN_REPORTからAI社員の完了状態を表示。

## 2026-07-29

- `Daily Brief Factory`を追加。
- P002 / P003 / P004 / CEO_REPORTのDaily Briefカードを追加。
- `Daily Brief更新`ボタンを追加。
- Daily Brief生成専用ジョブを追加。
- Daily Brief生成進捗JSONを追加。
- 生成ステップのアニメーション表示を追加。

## 2026-07-29

- `成果物`ページを追加。
- 主要Markdown成果物のカード一覧を追加。
- 成果物本文の展開表示とダウンロードを追加。

## 2026-07-29

- Command Center / Company Hubへ`衣装ローテ監査`を追加。
- SNS Todayの投稿カードへ衣装タグと衣装根拠を追加。
- 成果物ページに`WARDROBE_ROTATION_REPORT`を追加。
- 採用候補プレビューから`fail/`配下画像を除外。
