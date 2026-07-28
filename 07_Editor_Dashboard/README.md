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

## Sprint11 Company Hub

会社情報を集約する`Company Hub`画面を追加した。

表示:

- スマホ向け会社状態カード
- WordPress / Search Console / GA4 / X蓄積のサマリー
- P002 / P003 / P004 / P005 / P006の事業部ステータス
- 今日の流れをアニメーション付きで表示
- X結果の貼り付け保存
- AI COMPANY情報のタブ集約

X結果保存先:

```text
03_SNS事業部/03_Analytics/X_RESULTS/X_RESULT_LOG.md
03_SNS事業部/03_Analytics/X_RESULTS/x_results.csv
```

制約:

- SNS自動投稿禁止
- SNSログイン操作禁止
- WordPress更新禁止
- 削除禁止

## Sprint12 Console Visual Upgrade

Command Center / Company Hubの見た目を強化した。

- 上部に動きのあるコンソールヘッダーを表示
- KPI / SNS / X / SEO / CEO / Driveの色付きナビカードを表示
- AI稼働状態をレーダー風アニメーションで表示
- MIKU / RIOの直近候補画像をVisual Statusとして表示
- スマホ表示時はカードを1列中心へ自動調整

## Sprint13 AI美女 品質監査

Command Center / Company HubへAI美女作成の品質監査を集約した。

表示:

- 総合判定
- 本人感未確認
- 別人化リスク
- AI感・不自然表現リスク
- 投稿前チェック
- 要確認画像
- AI-VQC / MIKU / RIO固定ルール

## 衣装ローテーション監査

Command Center / Company Hubで`03_SNS事業部/03_Analytics/WARDROBE_ROTATION_REPORT.md`を読み込み、MIKU / RIOの衣装タグ、根拠、明日の候補、Blockerをカード表示する。

表示のみで、SNS投稿、画像生成、ファイル削除は行わない。

入力:

```text
03_SNS事業部/AI_VQC.md
03_SNS事業部/03_Analytics/GENERATION_QUALITY_REPORT.md
03_SNS事業部/01_Characters/MIKU/MIKU_FIXED_RULES.md
03_SNS事業部/01_Characters/RIO/RIO_BASE_REFERENCE.md
02_Daily_Output/YYYY-MM-DD/*/reports/image_*_report.json
```

この画面は投稿前の品質確認だけを目的とする。AI検出回避、SNS自動投稿、画像削除は行わない。

## Sprint14 Visual Boost

Command Center / Company Hubの第一印象を強化した。

追加表示:

- SEO Engine
- SNS Studio
- Data Pulse
- Quality Guard
- Blocker Watch
- Creative Deck

上部に色付きの状態カードと動くゲージを追加し、SEO、SNS、KPI、品質監査、Blockerをすぐ判断できるようにした。

## Sprint15 AI社員 Live Run

Runner実行とAI社員アニメーションを連動した。

表示:

- SNS分析AI
- グラビア事業部長AI
- KPI分析AI
- アダルト事業部長AI
- 品質監査AI
- AI社長
- 同期AI

`Runner実行`ボタンを押すとバックグラウンドでRunnerを開始し、`.dashboard_jobs/runner_progress.json`を読み込んで各AI社員の状態を表示する。

状態:

- 待機
- 作業中
- 完了
- 要確認

実行中はアニメーションで現在の進行を見せる。AI社員の進捗に合わせて画面は自動更新される。

## Sprint16 Daily Brief Factory

Daily BriefをCommand Centerへ集約し、生成ラインとして表示する。

表示:

- P002 SNS事業部 Daily Brief
- P003 グラビア事業部 Daily Brief
- P004 アダルト事業部 Daily Brief
- AI社長 CEO_REPORT

`Daily Brief更新`ボタンを押すと、バックグラウンドで以下を順番に実行する。

1. SNS Daily Brief生成
2. グラビア Daily Brief生成
3. アダルト Daily Brief生成
4. CEO_REPORT生成

進捗は`.dashboard_jobs/daily_brief_progress.json`に保存し、画面上では入力確認、SNS生成、グラビア生成、アダルト生成、AI社長集約のステップが動く。生成中は画面が自動更新される。

制約:

- SNS投稿禁止
- WordPress更新禁止
- 削除禁止

## Sprint17 成果物ページ

画面切替に`成果物`を追加した。

表示:

- CEO_REPORT
- KPI_DASHBOARD
- RUN_REPORT
- P002 / P003 / P004 DAILY_BRIEF
- SNS_REPORT
- TODAY_POST
- P003改善計画
- P004 SEO_PLAN
- Generation Quality / AI_VQC

各成果物はカードで状態、パス、更新日時を表示し、展開して本文確認とダウンロードができる。
