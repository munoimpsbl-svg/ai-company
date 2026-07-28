# P007 Editor Dashboard

## Sprint3

編集長が5秒で会社状態を把握できる経営ダッシュボードUI。

## 実行

```bash
streamlit run main.py
```

## 携帯表示

同じWi-Fi上の携帯から表示する場合:

```bash
cd /Users/izumisub/Documents/ai会社
scripts/run_mobile_dashboard.sh 8510
```

携帯URL:

```text
http://192.168.1.9:8510
```

停止:

```bash
scripts/stop_mobile_dashboard.sh
```

MacのIPが変わった場合は、起動スクリプトが表示するMobile URLを使用する。

## 外部公開

外出先から携帯で見る場合はRenderへデプロイする。

```text
DEPLOY_RENDER.md
render.yaml
```

必須:

- `DASHBOARD_PASSWORD`
- `AI_COMPANY_NON_INTERACTIVE=1`
- `GOOGLE_DRIVE_OAUTH_TOKEN_JSON`
- `P003_WORDPRESS_URL`

Google Driveを正データとして扱い、Renderのローカルファイルは一時領域とする。

## 表示

- KPIカード
- システム状態カード
- 今日やることTOP3
- Blocker
- AI社長コメント
- MIKU / RIO 採用候補画像サムネイル
- 詳細レポート展開表示

## 制約

- 表示のみ。
- 投稿禁止。
- 更新禁止。
- 削除禁止。

## Sprint4

通知センターと操作ボタンを追加した。

通知:

- GA4認証待ち
- Search Consoleデータ0件
- Runner正常終了
- 画像生成完了
- Blockerあり/なし

操作:

- Runner実行
- KPI更新
- CEO_REPORT再生成
- RUN_REPORTを開く
- KPI_DASHBOARDを開く
- CEO_REPORTを開く
- WordPressサイトを開く
- WordPress管理画面を開く

ボタンはローカル処理または画面内ファイル表示のみ。

## Sprint5

改善案件ボードを追加した。

メイン画面の表示順:

- AI COMPANY
- KPI
- 今日やること
- 改善案件
- Blocker
- AI社長コメント

改善案件は以下を読み込んでカード表示する。

- `01_グラビア事業部/P003_グラビア事業部/IMPROVEMENT_BACKLOG.md`
- `01_グラビア事業部/P003_グラビア事業部/EXECUTION_BOARD.md`
- `01_グラビア事業部/P003_グラビア事業部/TASK.md`

GOボタンは表示のみで、WordPress更新は行わない。

## Sprint6

改善案件のGO承認機能を追加した。

改善案件カードごとに以下の承認ボタンを表示する。

- GO
- STOP
- 要確認

承認結果は以下に保存する。

- `04_グラビア事業部/APPROVALS.md`

保存する内容:

- ID
- タスク
- 承認状態
- 承認日時
- コメント

承認ボタンは状態記録のみを行い、WordPress更新、投稿、削除は行わない。

## Sprint7

P006 Runnerが`APPROVALS.md`のGO案件を読み込み、`EXECUTION_BOARD.md`へ`実装待ち`として反映する。

ダッシュボードは承認状態の記録を担当し、Runnerが実行対象への状態遷移を担当する。

### GO承認後の状態確認

- GO案件はカード上で`GO済み`かつ`実装待ち`と表示する。
- 状態ラベルは`提案中`、`承認待ち`、`GO済み`、`実装待ち`、`実装中`、`完了`に対応する。
- 各カードに最終更新日時と`GO反映済み`を表示する。
- 画面下部に`APPROVALS.md`の承認履歴を表示する。
- `04_グラビア事業部`の入力を優先し、既存のP003プロジェクト配下を互換入力として扱う。

状態確認は表示のみで、WordPress更新、投稿、削除は行わない。

## P002 + P007 SNS連動

サイドバーの画面切替から`SNS Today`を表示できる。

- MIKU / RIOタブ
- 朝・夜の採用画像サムネイル
- Instagram / X / Threads投稿文
- コピー機能付き投稿文表示
- 各SNSを開く外部リンク
- 投稿完了チェック
- 投稿URLとメモの記録

投稿結果は`02_Daily_Output/YYYY-MM-DD/POST_RESULT.md`へ保存する。SNSへの自動投稿やログイン操作は行わない。

## SNS Input Manager

Google Driveを正データとして、SNS分析CSVをビジュアル管理する画面を追加した。

画面切替:

- `SNS Input Manager`

機能:

- Google Drive入力フォルダを表示
- Drive上のCSV一覧を表示
- CSVをアップロード
- 同名CSVを明示チェック付きで上書き
- CSVをプレビュー
- Driveから同期
- 同期結果とmanifestを表示

削除は運用事故防止のため無効。

正データ:

```text
AI_COMPANY_INPUT/03_SNS事業部/03_Analytics/MIKU/X/
```
