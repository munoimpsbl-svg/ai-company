# P002 TASK

## TASK-001 SNS運営フォルダ作成

Status
DONE

Priority
★★★★★

担当
SNS事業部

成果物

- `03_SNS事業部/01_Characters`
- `03_SNS事業部/02_Posts`
- `03_SNS事業部/03_Analytics`
- `03_SNS事業部/04_Daily`
- `03_SNS事業部/05_Schedule`
- `README.md`
- `SPEC.md`
- `TASK.md`
- `CHANGELOG.md`
- `REPORT.md`
- `REVIEW.md`

完了条件

- [x] SNS運営フォルダを作成
- [x] README.mdを更新
- [x] SPEC.mdを更新
- [x] TASK.mdを更新
- [x] CHANGELOG.mdを更新
- [x] REPORT.mdを更新
- [x] REVIEW.mdを更新

## Next Task

- 03_AnalyticsへSNS分析結果を保存する。
- 04_DailyへSNS事業部DAILY_BRIEF.mdを生成する。

---

## TASK-002 SNS_REPORT.md生成

Status
DONE

Priority
★★★★★

担当
SNS事業部

成果物

- `03_SNS事業部/SNS_REPORT.md`

完了条件

- [x] SNS_REPORT.mdを生成できること
- [x] エラーで停止しないこと
- [x] 推測は禁止
- [x] SNS投稿しない
- [x] 画像生成しない
- [x] WordPress更新しない
- [x] 解析のみ

---

## TASK-003 DAILY_BRIEF.md生成

Status
DONE

Priority
★★★★★

担当
SNS事業部

入力

- `SNS_REPORT.md`

出力

- `04_Daily/DAILY_BRIEF.md`

内容

- 今日やることTOP3
- 優先順位
- 期待ROI
- 理由
- Blocker
- 明日の予定

完了条件

- [x] DAILY_BRIEF.mdが生成されること
- [x] 分析のみ
- [x] SNS投稿禁止
- [x] 画像生成禁止

## Interface

- [x] 全事業部のDaily Brief命名規則を`DAILY_BRIEF.md`へ統一
- [x] P005がP002 SNS事業部のDaily Briefを読める

---

## P002 + P007 SNS連動

Status
DONE

Priority
★★★★★

完了条件

- [x] 当日のMIKU / RIO素材を読み込む
- [x] 朝・夜の投稿素材を取得する
- [x] `TODAY_POST.md`を生成する
- [x] テーマ、採用画像、投稿文、投稿先を出力する
- [x] 投稿チェック欄を出力する
- [x] 取得できない項目を推測しない
- [x] エラーで処理を停止しない
- [x] 自動投稿、SNSログイン操作、削除を行わない

---

## TASK-004 Google Drive SNS入力同期

Status
DONE

Priority
★★★★★

入力

- `AI_COMPANY_INPUT/03_SNS事業部/03_Analytics/MIKU/X/*.csv`

出力

- `03_SNS事業部/03_Analytics/MIKU/X/*.csv`
- `03_SNS事業部/03_Analytics/DRIVE_INPUT_SYNC_RESULT.md`
- `03_SNS事業部/03_Analytics/DRIVE_INPUT_MANIFEST.json`

完了条件

- [x] Google Drive入力フォルダを作成できる
- [x] Drive上のCSVをローカル分析フォルダへ同期できる
- [x] Google Driveを正データとして扱う
- [x] manifestに載らないローカルCSVを分析対象外にする
- [x] CSVが無くてもエラー停止しない
- [x] `03_SNS事業部/main.py`実行時に同期される
- [x] SNS投稿しない
- [x] SNSログインしない
- [x] ファイル削除しない

---

## TASK-005 衣装ローテーション監査

Status
DONE

Priority
★★★★☆

入力

- `02_Daily_Output/YYYY-MM-DD/MIKU/`
- `02_Daily_Output/YYYY-MM-DD/RIO/`
- `prompt.txt`
- `report.md`
- `status.json`
- フォルダ名

出力

- `03_SNS事業部/03_Analytics/WARDROBE_ROTATION_REPORT.md`
- `03_SNS事業部/04_Daily/TODAY_POST.md`の衣装タグ欄

完了条件

- [x] 今日の衣装タグを出力する
- [x] 直近ローテーションを出力する
- [x] 明日の衣装候補を出力する
- [x] 根拠がない場合は`未取得`にする
- [x] SNS投稿しない
- [x] 画像生成しない
- [x] ファイル削除しない
