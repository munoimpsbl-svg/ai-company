# AI COMPANY 自動運営システム

Google Driveの `AI_COMPANY` を唯一の正として読み込み、現段階では内容をログ表示するだけの基盤です。

## マスター運用

AI COMPANYの制作・開発作業は [00_MASTER_INSTRUCTION.md](/Users/izumisub/Documents/ai会社/00_MASTER_INSTRUCTION.md) を最優先ルールとして進めます。

作業開始時は以下を確認します。

- [01_PROJECT_HANDOFF.md](/Users/izumisub/Documents/ai会社/01_PROJECT_HANDOFF.md)
- [02_WORKFLOW.md](/Users/izumisub/Documents/ai会社/02_WORKFLOW.md)
- [03_GOOGLE_DRIVE_RULE.md](/Users/izumisub/Documents/ai会社/03_GOOGLE_DRIVE_RULE.md)
- [REPORT.md](/Users/izumisub/Documents/ai会社/REPORT.md)
- [CHANGELOG.md](/Users/izumisub/Documents/ai会社/CHANGELOG.md)
- [TASK.md](/Users/izumisub/Documents/ai会社/TASK.md)

## 引き継ぎ

別のパソコンで動かす場合は [HANDOVER.md](HANDOVER.md) を参照してください。

Windows PCで動かす場合は [WINDOWS_INSTALL.md](WINDOWS_INSTALL.md) を参照してください。

## 実行前準備

依存関係をインストールします。

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

サービスアカウントを使う場合:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
```

OAuthを使う場合:

```bash
export GOOGLE_OAUTH_CLIENT_SECRET="/path/to/client_secret.json"
```

## 実行

```bash
.venv/bin/python main.py
```

## 携帯からDashboardを開く

同じWi-Fiに接続した携帯からEditor Dashboardを見る場合は、StreamlitをLAN公開で起動します。

```bash
cd /Users/izumisub/Documents/ai会社
scripts/run_mobile_dashboard.sh 8510
```

携帯で開くURL:

```text
http://192.168.1.9:8510
```

停止:

```bash
scripts/stop_mobile_dashboard.sh
```

注意:

- PCと携帯は同じWi-Fiに接続する。
- MacのIPが変わった場合は`run_mobile_dashboard.sh`の表示URLを使う。
- macOSのファイアウォール確認が出た場合はPython/Streamlitの受信を許可する。
- 外出先から直接開く構成ではない。まずはLAN内運用。

## 外部公開Dashboard

外出先の携帯から開く場合はRenderへデプロイします。

```text
DEPLOY_RENDER.md
render.yaml
```

Renderでは`DASHBOARD_PASSWORD`を必ず設定し、Google Drive / Search Console / GA4のOAuth tokenは環境変数として登録します。Google Driveを正データとし、Render上のローカルファイルは一時領域として扱います。

## KPI Dashboard

KPI Dashboardは取得元アダプタ経由で生成します。

```bash
python3 generate_kpi_dashboard.py
```

取得元:

- `core/kpi/instagram.py`
- `core/kpi/x.py`
- `core/kpi/wordpress.py`
- `core/kpi/sales.py`
- `core/kpi/dashboard.py`

Sprint1では各取得元はダミー値を返します。

## 現在の処理

- Google Driveへ接続
- `AI_COMPANY` フォルダ確認
- `Daily_Brief.md` 読込
- `03_SNS事業部/01_Characters/MIKU` フォルダ読込
- 見つからない場合のみ旧テスト構成 `01_Characters/MIKU` を確認
- 内容をTerminalへログ表示

投稿、画像生成、ブラウザ操作は行いません。

## GPT Image Quality

GPT画像生成の質を上げるため、生成候補をSQLiteへ記録し、品質レポートを作成する。

```bash
python3 scripts/update_generation_quality.py
```

出力:

- `03_SNS事業部/03_Analytics/generation_quality.sqlite3`
- `03_SNS事業部/03_Analytics/GENERATION_QUALITY_REPORT.md`

Editor Dashboardでは`GPT Image Quality`画面から確認できる。

現段階の評価対象:

- 画像が開けるか
- 解像度、画角
- EXIF削除状態
- `prompt.txt` / `report.md` の有無
- `report.md`内の既知NG記録
- 採用候補、優先候補の記録

現段階で行わないこと:

- 自動採用
- 自動投稿
- 画像削除
- 外部画像生成UIの実行
- 外部画像ストアへの登録
- GPT以外の生成エンジン評価

## 運用ルール

Google Driveの正式運用ルールは [AI_COMPANY_Google_Drive運用ルール.md](/Users/izumisub/Documents/ai会社/AI_COMPANY_Google_Drive運用ルール.md) を参照してください。

## 画像EXIF削除・最適化

画像成果物は保存後にEXIF削除を必ず行います。
標準はGitHub Actions上の `stefmolin/exif-stripper` / `strip-exif` です。
画像をGitHubへpushすると、`.github/workflows/strip-exif.yml` がEXIF削除を実行します。

ローカル補助として使う場合は、`.env` の `EXIF_CLEANER_COMMAND` に実行コマンドを設定できます。
未設定の場合はPython/Pillowでメタデータ削除します。

Windows:

```powershell
.\installer\windows\optimize_images.ps1 .\02_Daily_Output\YYYY-MM-DD\MIKU
```

Google Drive同期フォルダを監視して自動実行する場合:

```text
GOOGLE_DRIVE_SYNC_ROOT=G:\マイドライブ\AI_COMPANY
```

```powershell
.\Watch-GoogleDrive-EXIF.bat
```

macOSで従来のImageOptimを併用する場合:

```bash
scripts/optimize_images_with_imageoptim.sh 02_Daily_Output/YYYY-MM-DD/MIKU/images
```

ImageOptimは補助的な圧縮用途です。EXIF削除を優先します。
