# P002 SPEC

## TASK-001 SNS運営フォルダ

SNS事業部の運営フォルダを作成し、今後のSNS分析AI、投稿案管理、日次運用、スケジュール管理の置き場所を固定する。

## 対象フォルダ

```text
03_SNS事業部/
  01_Characters/
  02_Posts/
  03_Analytics/
  04_Daily/
  05_Schedule/
```

## 入力

- Instagram
- X
- キャラクター設定
- Daily Brief

## 出力

- REPORT.md
- REVIEW.md
- 03_Analytics配下の分析結果
- 04_Daily配下の日次ブリーフ

## 運用ルール

- `01_Characters`は既存キャラクター運用の置き場所として保持する。
- `02_Posts`は投稿案と投稿素材の置き場所とする。
- `03_Analytics`は分析結果の置き場所とする。
- `04_Daily`は日次運用ファイルの置き場所とする。
- `05_Schedule`は投稿予定と運用予定の置き場所とする。

## 禁止事項

- 投稿禁止
- 更新禁止
- 削除禁止
- 自動承認禁止
- 分析のみ

## TASK-002 SNS_REPORT生成

### 目的

SNS運営結果を毎日分析し、SNS_REPORT.mdを生成する。

### 入力

- Google Drive: `AI_COMPANY_INPUT/03_SNS事業部/03_Analytics/MIKU/X/*.csv`
- `03_SNS事業部/02_Posts/`
- `03_SNS事業部/03_Analytics/`
- `03_SNS事業部/04_Daily/`
- `03_SNS事業部/05_Schedule/`
- `02_Daily_Output/YYYY-MM-DD/`

### 出力

- `03_SNS事業部/SNS_REPORT.md`

### 制約

- SNS投稿は禁止。
- 画像生成は禁止。
- WordPress更新は禁止。
- 解析のみ。

### Failure Handling

エラー時は停止せず、理由をSNS_REPORT.mdのBlockerへ出力する。

推測は禁止。取得できない項目は「未取得」と記録する。

### Google Drive入力同期

`03_SNS事業部/main.py`は、SNS_REPORT生成前に`sync_drive_inputs.py`を実行する。
Google Drive上の`AI_COMPANY_INPUT/03_SNS事業部/03_Analytics/MIKU/X/`からCSVを取得し、ローカルの`03_SNS事業部/03_Analytics/MIKU/X/`へ分析用コピーを作成する。

正データは必ずGoogle Driveとする。
分析対象は`03_SNS事業部/03_Analytics/DRIVE_INPUT_MANIFEST.json`に記録されたDrive同期済みCSVのみとし、ローカルへ手動配置したCSVは分析対象にしない。

DriveにCSVが無い場合は停止せず、`DRIVE_INPUT_SYNC_RESULT.md`へCSV未取得として記録する。

## TASK-003 DAILY_BRIEF.md生成

### 目的

SNS_REPORT.mdを要約し、SNS運営の今日やることTOP3を共通仕様のDAILY_BRIEF.mdとして出力する。

### 入力

- `03_SNS事業部/SNS_REPORT.md`

### 出力

- `03_SNS事業部/04_Daily/DAILY_BRIEF.md`

### 出力項目

- 今日やることTOP3
- 優先順位
- 理由
- 期待ROI
- Blocker
- 明日の予定

### 制約

- 分析のみ
- SNS投稿禁止
- 画像生成禁止

## SNS Today連動

### 入力

- `02_Daily_Output/YYYY-MM-DD/MIKU/`
- `02_Daily_Output/YYYY-MM-DD/RIO/`
- 各時間帯の`prompt.txt`、`report.md`、投稿文、画像

### 出力

- `03_SNS事業部/04_Daily/TODAY_POST.md`

### 取得項目

- キャラクター名
- 今日のテーマ
- 採用画像フォルダ
- 採用画像一覧
- Instagram / X / Threads投稿文
- 投稿先
- 投稿チェック欄

テーマは`prompt.txt`のDaily Brief、採用画像は`report.md`の優先候補から取得する。取得できない項目は`未取得`とし、推測しない。

### 禁止事項

- 自動投稿
- SNSログイン操作
- 画像生成
- ファイル削除
