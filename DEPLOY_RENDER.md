# Render Deploy Guide

目的: Editor Dashboardを外部URLで起動し、携帯から常時確認できるようにする。

## 構成

- Hosting: Render Web Service
- Runtime: Python 3.11
- App: Streamlit
- Entry point: `main.py`
- Start command: `streamlit run main.py --server.address 0.0.0.0 --server.port $PORT --server.headless true`
- Source of Truth: Google Drive

## 必須環境変数

RenderのEnvironment Variablesへ設定する。

| Key | 必須 | 内容 |
|---|---:|---|
| `DASHBOARD_PASSWORD` | YES | 外部公開Dashboardのログイン用パスワード |
| `AI_COMPANY_NON_INTERACTIVE` | YES | `1`を設定。クラウド上でOAuth画面を起動しない |
| `P003_WORDPRESS_URL` | YES | 解析対象WordPress URL |
| `P003_WORDPRESS_ADMIN_URL` | NO | WordPress管理画面URL |
| `P004_WORDPRESS_URL` | NO | アダルト事業部用WordPress URL。未設定時はP003を利用 |
| `AI_COMPANY_DRIVE_ROOT_ID` | NO | 既存DriveルートフォルダID |
| `GOOGLE_DRIVE_OAUTH_TOKEN_JSON` | YES | `.secrets/google_token.json`のJSON全体 |
| `GOOGLE_SEARCH_CONSOLE_TOKEN_JSON` | NO | `.secrets/search_console_token.json`のJSON全体 |
| `GOOGLE_GA4_TOKEN_JSON` | NO | `.secrets/ga4_token.json`のJSON全体 |
| `SEARCH_CONSOLE_SITE_URL` | NO | Search ConsoleのsiteUrl |
| `GA4_PROPERTY_ID` | NO | GA4 Property ID |

Search Console / GA4のtokenが無い場合、該当KPIは`未取得`または`0`として表示する。

## デプロイ手順

1. このプロジェクトをGitHubへpushする。
2. RenderでNew BlueprintまたはNew Web Serviceを作成する。
3. `render.yaml`を使ってWeb Serviceを作成する。
4. Environment Variablesを設定する。
5. Deployする。
6. 発行されたRender URLへアクセスし、`DASHBOARD_PASSWORD`でログインする。

## Token JSONの作り方

ローカルで既にOAuth済みの場合、以下のファイル内容をRender環境変数へ貼り付ける。

```text
.secrets/google_token.json
.secrets/search_console_token.json
.secrets/ga4_token.json
```

改行を含めず、JSON全体を1行として登録する。

## 運用ルール

- Google Driveを正データとする。
- Renderのローカルファイルは一時領域として扱う。
- Dashboard外部公開時は`DASHBOARD_PASSWORD`を必ず設定する。
- WordPress投稿、削除、SNS自動投稿は行わない。
