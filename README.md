# AI COMPANY Editor Dashboard

Renderで外部公開するStreamlit Dashboardです。

## Render Environment Variables

必須:

- `DASHBOARD_PASSWORD`
- `AI_COMPANY_NON_INTERACTIVE=1`
- `GOOGLE_DRIVE_OAUTH_TOKEN_JSON`
- `P003_WORDPRESS_URL`

任意:

- `P003_WORDPRESS_ADMIN_URL`
- `AI_COMPANY_DRIVE_ROOT_ID`
- `SEARCH_CONSOLE_SITE_URL`
- `GA4_PROPERTY_ID`

`GOOGLE_DRIVE_OAUTH_TOKEN_JSON` はローカルの `.secrets/google_token.json` の中身全体をRenderのEnvironment Variablesへ貼り付けます。

## Start Command

```bash
streamlit run main.py --server.address 0.0.0.0 --server.port $PORT --server.headless true
```

## Safety

- WordPress投稿なし
- WordPress更新なし
- SNS自動投稿なし
- Google Drive削除なし
- 表示専用
