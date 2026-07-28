# P007 Editor Dashboard TASK

## Sprint3

Status
DONE

Priority
★★★★★

完了条件

- [x] KPIカードを色付きで表示
- [x] システム状態を 🟢 🟡 🔴 で表示
- [x] 今日やることTOP3をカード化
- [x] Blockerを目立つ表示にする
- [x] MIKU / RIO の採用候補画像をサムネイル表示
- [x] 展開で詳細レポートを表示
- [x] `streamlit run main.py`で起動できる
- [x] 表示のみ
- [x] 投稿禁止
- [x] 更新禁止

---

## Sprint4 通知センター / 操作ボタン

Status
DONE

Priority
★★★★★

完了条件

- [x] 通知センターを表示
- [x] GA4認証待ちを表示
- [x] Search Consoleデータ0件を表示
- [x] Runner正常終了を表示
- [x] 画像生成完了を表示
- [x] Blockerあり/なしを表示
- [x] Runner実行ボタンを表示
- [x] KPI更新ボタンを表示
- [x] CEO_REPORT再生成ボタンを表示
- [x] RUN_REPORTを開くボタンを表示
- [x] KPI_DASHBOARDを開くボタンを表示
- [x] CEO_REPORTを開くボタンを表示
- [x] WordPressサイトリンクを表示
- [x] WordPress管理画面リンクを表示
- [x] ボタン操作でエラー停止しない
- [x] 投稿禁止
- [x] WordPress更新禁止
- [x] SNS投稿禁止
- [x] 削除禁止

---

## Sprint5 改善案件ボード

Status
DONE

Priority
★★★★★

完了条件

- [x] `IMPROVEMENT_BACKLOG.md`を読み込む
- [x] `EXECUTION_BOARD.md`を読み込む
- [x] `TASK.md`を読み込む
- [x] 今日の改善案件をカード表示する
- [x] 優先順位順で表示する
- [x] 状態を表示する
- [x] 推定時間を表示する
- [x] 期待ROIを表示する
- [x] GOボタンを表示する
- [x] GOボタンは表示のみにする
- [x] 画面順をAI COMPANY、KPI、今日やること、改善案件、Blocker、AI社長コメントにする
- [x] `streamlit run main.py`で起動できる
- [x] WordPress更新禁止
- [x] 投稿禁止
- [x] 解析表示のみ

---

## Sprint6 改善案件GO承認機能

Status
DONE

Priority
★★★★★

完了条件

- [x] 改善案件カードごとにGOボタンを表示する
- [x] 改善案件カードごとにSTOPボタンを表示する
- [x] 改善案件カードごとに要確認ボタンを表示する
- [x] コメント欄を表示する
- [x] ボタンを押した結果を承認状態として保存する
- [x] `04_グラビア事業部/APPROVALS.md`へ保存する
- [x] `APPROVALS.md`をMarkdown表形式にする
- [x] WordPress更新禁止
- [x] 投稿禁止
- [x] 削除禁止
- [x] 状態記録のみ
- [x] エラーで停止しない

---

## Sprint7 Runner連携

Status
DONE

Priority
★★★★★

完了条件

- [x] `APPROVALS.md`のGO案件をRunnerが読める
- [x] GO案件が`EXECUTION_BOARD.md`で`実装待ち`になる
- [x] STOPと要確認は実行対象にしない
- [x] WordPress更新禁止
- [x] 投稿禁止
- [x] 削除禁止
- [x] 状態遷移のみ

---

## Sprint7 GO承認後の状態確認

Status
DONE

Priority
★★★★★

完了条件

- [x] GO案件を`GO済み`と表示する
- [x] GO案件を`実装待ち`と表示する
- [x] 各案件カードに状態ラベルを表示する
- [x] 各案件カードに最終更新日時を表示する
- [x] GO案件に`GO反映済み`を表示する
- [x] 画面下部に`APPROVALS.md`を表示する
- [x] 入力エラーで画面を停止しない
- [x] WordPress更新、投稿、削除を行わない

---

## P002 + P007 SNS連動

Status
DONE

Priority
★★★★★

完了条件

- [x] `SNS Today`画面を追加する
- [x] MIKU / RIOをタブ表示する
- [x] 採用画像をサムネイル表示する
- [x] 投稿文をコピーしやすく表示する
- [x] Instagram / X / Threadsリンクを表示する
- [x] 投稿完了チェック欄を表示する
- [x] `POST_RESULT.md`を作成できる
- [x] エラーで停止しない
- [x] 自動投稿、SNSログイン操作、削除を行わない

---

## Sprint8 SNS Input Manager

Status
DONE

Priority
★★★★★

完了条件

- [x] Google Driveを正データとして表示する
- [x] Drive入力フォルダを開ける
- [x] Drive上のCSV一覧を表示する
- [x] CSVをアップロードできる
- [x] 明示チェック付きで同名CSVを上書きできる
- [x] CSVをプレビューできる
- [x] Drive同期を実行できる
- [x] manifestを表示できる
- [x] 削除は無効にする
- [x] SNS投稿、SNSログイン、削除を行わない

---

## Sprint9 携帯表示対応

Status
DONE

Priority
★★★★★

完了条件

- [x] LAN公開用Streamlit起動コマンドを確認する
- [x] 携帯用URLを確認する
- [x] `scripts/run_mobile_dashboard.sh`を`screen`常駐方式で追加する
- [x] `scripts/stop_mobile_dashboard.sh`を`screen`停止方式で追加する
- [x] READMEへ携帯表示手順を追記する
- [x] `http://192.168.1.9:8510`でHTTP 200を確認する

---

## Sprint10 外部公開対応

Status
DONE

Priority
★★★★★

完了条件

- [x] Render用`render.yaml`を追加する
- [x] `Procfile`を追加する
- [x] `runtime.txt`を追加する
- [x] Streamlit設定`.streamlit/config.toml`を追加する
- [x] `DASHBOARD_PASSWORD`による簡易ログインを追加する
- [x] Google OAuth token JSONを環境変数から読めるようにする
- [x] Renderデプロイ手順を追記する
