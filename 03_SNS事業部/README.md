# P002 SNS事業部

## 目的

SNS運営状況を分析し、投稿・分析・日次運用・スケジュールを分けて管理する。

## フォルダ構成

```text
03_SNS事業部/
  01_Characters/
  02_Posts/
  03_Analytics/
  04_Daily/
  05_Schedule/
```

## フォルダ役割

- `01_Characters`: キャラクター設定、プロフィール、人物設定
- `02_Posts`: 投稿案、投稿文、投稿素材の管理
- `03_Analytics`: Instagram / X の分析結果
- `04_Daily`: DAILY_BRIEF.mdなどの日次運用
- `05_Schedule`: 投稿予定、実行予定、運用カレンダー

## 制約

- 投稿禁止
- 更新禁止
- 削除禁止
- 分析のみ

## 関連実装

Sprint1のSNS分析AI実装は`02_SNS事業部/`にある。

## TASK-002 SNS_REPORT生成

既存の日次出力を解析し、`SNS_REPORT.md`を生成する。

```bash
python3 03_SNS事業部/main.py
```

出力:

```text
03_SNS事業部/SNS_REPORT.md
```

## TASK-003 DAILY_BRIEF生成

`SNS_REPORT.md`を要約し、今日やることTOP3を`04_Daily/DAILY_BRIEF.md`へ出力する。

```bash
python3 03_SNS事業部/generate_daily_brief.py
```

## SNS Today連動

当日のMIKU / RIO投稿素材から`TODAY_POST.md`を生成する。

```bash
python3 03_SNS事業部/generate_today_post.py
```

入力:

- `02_Daily_Output/YYYY-MM-DD/MIKU/`
- `02_Daily_Output/YYYY-MM-DD/RIO/`

出力:

- `03_SNS事業部/04_Daily/TODAY_POST.md`

`03_SNS事業部/main.py`実行時にもSNS_REPORTとあわせて生成する。画像生成、自動投稿、SNSログイン操作、ファイル削除は行わない。

## MIKU X分析

今回の分析対象はMIKUのXアカウントのみ。
RIOのThreads分析は現段階では実装しない。

Google Drive入力:

- `AI_COMPANY_INPUT/03_SNS事業部/03_Analytics/MIKU/X/*.csv`

ローカルミラー:

- `03_SNS事業部/03_Analytics/MIKU/X/*.csv`

`03_SNS事業部/main.py`は、実行時にGoogle Drive入力フォルダからCSVをローカルミラーへ同期してから分析する。
正データは必ずGoogle Driveとし、分析対象は`DRIVE_INPUT_MANIFEST.json`に記録されたDrive同期済みCSVのみとする。
ローカルへ手動配置したCSVは分析対象にしない。

対応CSV列:

- `date` または `日付`
- `post_id` または `投稿ID`
- `text` または `投稿文`
- `url` または `投稿URL`
- `impressions` または `インプレッション`
- `engagements` または `エンゲージメント`
- `likes` または `いいね`
- `replies` または `返信`
- `reposts` または `リポスト`
- `bookmarks` または `ブックマーク`
- `profile_clicks` または `プロフィールクリック`
- `link_clicks` または `リンククリック`
- `followers` または `フォロワー`
- `followers_delta` または `フォロワー増減`

表示:

- Editor Dashboardの`SNS Analytics`
- `generate_kpi_dashboard.py`のX KPI

制約:

- Xへログインしない
- 投稿しない
- Threads CSVは読み込まない
- 将来拡張は`core/sns_analytics.py`の`AnalysisTarget`と`SocialPlatform`で行う

## Google Drive入力同期

入力フォルダ作成とCSV同期:

```bash
python3 03_SNS事業部/sync_drive_inputs.py
```

Google Drive上でCSVを入れる場所:

```text
AI_COMPANY_INPUT/
  03_SNS事業部/
    03_Analytics/
      MIKU/
        X/
          *.csv
```

同期結果:

```text
03_SNS事業部/03_Analytics/DRIVE_INPUT_SYNC_RESULT.md
03_SNS事業部/03_Analytics/DRIVE_INPUT_MANIFEST.json
```

## 衣装ローテーション監査

MIKU / RIOの服装が同じになりがちな問題を確認するため、`03_SNS事業部/main.py`実行時に`WARDROBE_ROTATION_REPORT.md`も生成する。

出力:

```text
03_SNS事業部/03_Analytics/WARDROBE_ROTATION_REPORT.md
```

判定方法:

- `prompt.txt`
- `report.md`
- `status.json`
- フォルダ名

上記から取得できる範囲で衣装タグを記録する。根拠がない場合は推測せず`未取得`とする。SNS投稿、画像生成、ファイル削除は行わない。
