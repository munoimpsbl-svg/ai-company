# AI COMPANY 引き継ぎ書

別のパソコンでAI COMPANYを動かすためのセットアップ手順です。

このリポジトリは、SNS事業部、グラビア事業部、AI社長、Runner、Editor Dashboardをローカルで実行します。WordPress更新やSNS投稿は、明示された実行タスク以外では行いません。

## 1. 前提

- OS: macOS想定
- Python: 3.9以上
- 作業ディレクトリ例: `~/Documents/ai会社`
- 起動確認URL: `http://localhost:8501`

## 2. 別PCへ移すもの

Gitまたはフォルダコピーで移すもの:

- このプロジェクト一式
- `README.md`
- `requirements.txt`
- `core/`
- `03_SNS事業部/`
- `04_グラビア事業部/`
- `05_AI社長/`
- `06_AI_COMPANY_Runner/`
- `07_Editor_Dashboard/`
- `main.py`
- `generate_kpi_dashboard.py`

手動で安全に移すもの:

- `.env`
- `.secrets/`
- Google OAuth client secret JSON
- Google OAuth token JSON
- Search Console token JSON
- 必要であればGA4 token JSON

注意:

- `.env` と `.secrets/` はGit管理対象外です。
- チャット、GitHub、公開ストレージへ秘密情報を貼らないでください。
- 別PCでOAuthをやり直す場合、token JSONはコピー不要です。

## 3. 初期セットアップ

プロジェクトルートへ移動します。

```bash
cd ~/Documents/ai会社
```

仮想環境を作成します。

```bash
python3 -m venv .venv
```

依存ライブラリを入れます。

```bash
.venv/bin/python -m pip install -r requirements.txt
```

Streamlitコマンドを使う場合は、以後 `.venv/bin/streamlit` を使います。

## 4. `.env` の作成

`.env.example` をコピーして `.env` を作成します。

```bash
cp .env.example .env
```

最低限確認する項目:

```env
GOOGLE_OAUTH_CLIENT_SECRET=.secrets/client_secret.json
GOOGLE_OAUTH_TOKEN=.secrets/google_token.json
P003_WORDPRESS_URL=https://example.com
SEARCH_CONSOLE_SITE_URL=https://example.com/
GOOGLE_SEARCH_CONSOLE_TOKEN=.secrets/search_console_token.json
GA4_PROPERTY_ID=123456789
GOOGLE_GA4_TOKEN=.secrets/ga4_token.json
```

現在の環境で使っているclient secretのファイル名が長い場合は、どちらかで対応します。

方法A: `.env` に実ファイル名を書く

```env
GOOGLE_OAUTH_CLIENT_SECRET=.secrets/client_secret_2_492958396539-n02clof64sjh7tdbj4fuddoe99lkjr3k.apps.googleusercontent.com.json
```

方法B: `.secrets/client_secret.json` にリネームまたはコピーする

```bash
mkdir -p .secrets
cp ".secrets/client_secret_2_492958396539-n02clof64sjh7tdbj4fuddoe99lkjr3k.apps.googleusercontent.com.json" .secrets/client_secret.json
```

## 5. `.secrets/` の配置

`.secrets/` を作成します。

```bash
mkdir -p .secrets
```

既存PCから引き継ぐ場合は、以下を安全な方法でコピーします。

```text
.secrets/
├── client_secret_*.json
├── google_token.json
└── search_console_token.json
```

GA4連携を使う場合は、必要に応じて以下も配置します。

```text
.secrets/ga4_token.json
```

OAuthを再認証する場合:

- `client_secret_*.json` だけ配置します。
- `search_console_token.json` や `ga4_token.json` が無ければ、初回実行時に認証URLを表示してtokenを生成します。

## 6. 起動確認

Editor Dashboardを起動します。

```bash
.venv/bin/streamlit run main.py
```

ブラウザで開きます。

```text
http://localhost:8501
```

画面上部で切り替えます。

- `Command Center`
- `SNS Today`

`SNS Today` では以下を確認します。

- MIKU / RIOタブ
- 採用画像サムネイル
- Instagram / X / Threads投稿文
- 投稿完了チェック
- `POST_RESULT.md` 記録

## 7. 日次実行

会社全体を順番に実行します。

```bash
.venv/bin/python 06_AI_COMPANY_Runner/main.py
```

実行順:

1. P002 SNS事業部
2. P003 グラビア事業部
3. P005 AI社長
4. KPI Dashboard生成
5. ログ保存

出力確認:

```text
06_AI_COMPANY_Runner/RUN_REPORT.md
02_Daily_Output/YYYY-MM-DD/RUN_REPORT.md
KPI_DASHBOARD.md
02_Daily_Output/YYYY-MM-DD/KPI_DASHBOARD.md
02_Daily_Output/YYYY-MM-DD/CEO_REPORT.md
```

エラーがあってもRunnerは次の部署へ進みます。

## 8. SNS Today生成

SNS投稿補助用の `TODAY_POST.md` を生成します。

```bash
.venv/bin/python 03_SNS事業部/generate_today_post.py
```

出力:

```text
03_SNS事業部/04_Daily/TODAY_POST.md
```

入力:

```text
02_Daily_Output/YYYY-MM-DD/MIKU/
02_Daily_Output/YYYY-MM-DD/RIO/
```

制約:

- 自動投稿しません。
- SNSログイン操作はしません。
- 画像生成はしません。
- 表示と手動投稿補助のみです。

## 9. KPI Dashboard生成

KPIだけ再生成する場合:

```bash
.venv/bin/python generate_kpi_dashboard.py
```

対象:

- WordPress KPI
- Search Console KPI
- GA4 KPI
- SNS / Salesの抽象取得元

Search Consoleで `clicks=0` の場合は、以下を確認します。

- `.env` の `SEARCH_CONSOLE_SITE_URL`
- Search Consoleで取得可能な `siteUrl`
- API送信期間
- `startDate`
- `endDate`
- `dimensions`
- `rowLimit`
- APIレスポンスJSON

## 10. AI社長レポート生成

AI社長だけ実行する場合:

```bash
.venv/bin/python 05_AI社長/main.py
```

入力:

```text
03_SNS事業部/04_Daily/DAILY_BRIEF.md
04_グラビア事業部/DAILY_BRIEF.md
KPI_DASHBOARD.md
```

出力:

```text
02_Daily_Output/YYYY-MM-DD/CEO_REPORT.md
```

未提出の部署は `未提出` として扱います。推測は禁止です。

## 11. 改善承認フロー

Editor Dashboardの改善案件カードで承認状態を記録します。

保存先:

```text
04_グラビア事業部/APPROVALS.md
```

承認状態:

- `GO`
- `STOP`
- `要確認`

Runnerは `GO` の案件だけを `実装待ち` として認識します。

現在のSprint7では、WordPress更新はまだ実行しません。状態遷移のみです。

## 12. WordPress関連の安全ルール

通常運用で禁止:

- WordPress投稿
- WordPress削除
- WordPress本文更新
- WordPressカテゴリ変更
- WordPressタイトル変更

例外:

- 明示された実行タスクで、かつ `GO` 承認済みの対象のみ。

現時点のCommand Center / Dashboardは表示と状態記録が中心です。

## 13. よく使うコマンド

Dashboard起動:

```bash
.venv/bin/streamlit run main.py
```

Runner実行:

```bash
.venv/bin/python 06_AI_COMPANY_Runner/main.py
```

KPI更新:

```bash
.venv/bin/python generate_kpi_dashboard.py
```

SNS Today更新:

```bash
.venv/bin/python 03_SNS事業部/generate_today_post.py
```

Python構文チェック:

```bash
.venv/bin/python -m py_compile main.py 03_SNS事業部/main.py 03_SNS事業部/generate_today_post.py 05_AI社長/main.py 06_AI_COMPANY_Runner/main.py
```

## 14. トラブル対応

Dashboardが開かない:

```bash
lsof -i :8501
```

別プロセスが使っている場合は、別ポートで起動します。

```bash
.venv/bin/streamlit run main.py --server.port 8502
```

認証エラー:

- `.env` のパスを確認します。
- `.secrets/` にclient secretがあるか確認します。
- token JSONを消してOAuthをやり直します。

```bash
rm .secrets/search_console_token.json
```

ただし、token削除後は再認証が必要です。

SNS Todayに画像が出ない:

- `02_Daily_Output/YYYY-MM-DD/MIKU/`
- `02_Daily_Output/YYYY-MM-DD/RIO/`
- 各フォルダ内の `report.md`
- 画像ファイル名

を確認します。

GO承認が画面に反映されない:

- `04_グラビア事業部/APPROVALS.md`
- `01_グラビア事業部/P003_グラビア事業部/EXECUTION_BOARD.md`
- Runner実行結果

を確認します。

## 15. 引き継ぎチェックリスト

- [ ] プロジェクト一式を別PCへ配置した
- [ ] `.env` を作成した
- [ ] `.secrets/` を配置した
- [ ] `pip install -r requirements.txt` を実行した
- [ ] `streamlit run main.py` でDashboardが開いた
- [ ] `SNS Today` が表示された
- [ ] `06_AI_COMPANY_Runner/main.py` が実行できた
- [ ] `RUN_REPORT.md` が生成された
- [ ] `KPI_DASHBOARD.md` が生成された
- [ ] `CEO_REPORT.md` が生成された
- [ ] WordPress/SNSへ自動投稿されていないことを確認した
