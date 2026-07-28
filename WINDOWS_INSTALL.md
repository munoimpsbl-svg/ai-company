# AI COMPANY Windows Installer

## 対象

- Windows 10 / 11
- PowerShell
- Python 3.11以上

## 配布物

`AI_COMPANY_Windows_Installer.zip` をWindows PCへ渡す。

このZIPには以下を含めない。

- `.env`
- `.secrets/`
- `.venv/`
- Google OAuth token
- Google client secret
- 生成画像の大容量ファイル

## インストール

ZIPを展開し、PowerShellを開いてプロジェクト直下で実行する。

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\installer\windows\install.ps1
```

Pythonが未導入の場合は、Pythonを先にインストールする。

```powershell
.\installer\windows\install.ps1 -InstallPythonWithWinget
```

## Google認証

Windows PC側で以下を配置する。

```text
.secrets\client_secret.json
```

`.env` はインストーラーが `.env.example` から作成する。

基本設定:

```text
GOOGLE_OAUTH_CLIENT_SECRET=.secrets/client_secret.json
GOOGLE_OAUTH_TOKEN=.secrets/google_token.json
```

初回実行時にGoogle認証URLが表示されたら、ブラウザで認証する。

## 起動

ダッシュボード:

```powershell
.\Start-AI-COMPANY-Dashboard.bat
```

Runner:

```powershell
.\Run-AI-COMPANY-Runner.bat
```

KPI:

```powershell
.\Run-AI-COMPANY-KPI.bat
```

## 画像EXIF削除・最適化

macOSのImageOptimはWindowsでは使えない。
標準はGitHub Actions上の `stefmolin/exif-stripper` / `strip-exif`。
画像をGitHubへpushすると、`.github/workflows/strip-exif.yml` がEXIF削除を実行する。

Windowsローカルでは補助処理として、GitHub版EXIF削除アプリを使える。

`.env` に以下を設定すると、そのアプリを実行する。

```text
EXIF_CLEANER_COMMAND=C:\Tools\exif-cleaner\exif-cleaner.exe "{path}"
```

未設定の場合は、PillowベースのローカルEXIF削除と最適化を使う。

```powershell
.\installer\windows\optimize_images.ps1 .\02_Daily_Output\2026-07-12\RIO
```

## Google Drive同期フォルダの自動監視

Google Driveが正のフォルダ。
Google Drive for desktopで `AI_COMPANY` をWindowsへ同期し、そのローカルパスを `.env` に設定する。

例:

```text
GOOGLE_DRIVE_SYNC_ROOT=G:\マイドライブ\AI_COMPANY
```

監視起動:

```powershell
.\Watch-GoogleDrive-EXIF.bat
```

動作:

- `GOOGLE_DRIVE_SYNC_ROOT` 配下に画像が入る
- ファイルサイズと更新時刻が安定するまで待つ
- EXIF削除を実行する
- `.exifcleaned` マーカーを作成して二重処理を防ぐ

## 注意

- 自動投稿はしない。
- SNSログイン操作はしない。
- ブラウザ自動操作はしない。
- Google Driveを唯一の正として扱う。
- `.secrets` と `.env` は各PCで個別に管理する。
