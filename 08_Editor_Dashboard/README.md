# Editor Dashboard

## Sprint1

編集長専用ダッシュボード。

## 技術

Streamlit

## 実行

```bash
streamlit run main.py
```

## 入力

- `KPI_DASHBOARD.md`
- `02_Daily_Output/YYYY-MM-DD/CEO_REPORT.md`
- `02_Daily_Output/YYYY-MM-DD/RUN_REPORT.md`
- `03_SNS事業部/04_Daily/DAILY_BRIEF.md`
- `04_グラビア事業部/DAILY_BRIEF.md`

## 制約

- 表示のみ。
- 更新禁止。
- 投稿禁止。
- 削除禁止。
- Google Drive変更禁止。

## Sprint2

Markdown全文表示ではなく、経営ダッシュボードUIへ変更した。

表示:

- システム状態カード
- KPIカード
- 今日やることTOP3
- Blocker
- AI社長コメント

Markdownは内部で読み込み、必要な情報だけ抽出して表示する。

## Sprint3

編集長が5秒で会社状態を把握できるよう、ビジュアルを強化した。

- KPIカードを色付き表示
- システム状態を 🟢 🟡 🔴 で表示
- 今日やることTOP3をカード化
- Blockerを強調表示
- MIKU / RIO 採用候補画像をサムネイル表示
- 詳細レポートを展開表示

## Sprint4

通知センターと操作ボタンを追加した。

- GA4認証待ち
- Search Consoleデータ0件
- Runner正常終了
- 画像生成完了
- Blockerあり/なし
- Runner実行
- KPI更新
- CEO_REPORT再生成
- 各レポートの詳細表示
- WordPress外部リンク
