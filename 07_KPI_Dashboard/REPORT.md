# KPI Dashboard REPORT

## 実行日

2026-07-05

## 今日の結論

KPI Dashboard Sprint1として、取得元を抽象化した。

## 実装内容

- `core/kpi/instagram.py`
- `core/kpi/x.py`
- `core/kpi/wordpress.py`
- `core/kpi/sales.py`
- `core/kpi/dashboard.py`

## 動作

`generate_kpi_dashboard.py`は`core/kpi/dashboard.py`からKPIを取得する。

## Blocker

- Instagram / X / Sales は実API未接続。
- WordPress KPIはREST APIから取得。

## 制約確認

- WordPress更新: 未実行
- SNS投稿: 未実行
- Google Drive変更: 未実行

---

## Sprint2 結果

WordPress KPI取得を実装した。

取得項目:

- 記事数
- 公開記事数
- カテゴリ数
- タグ数

`generate_kpi_dashboard.py`でKPI_DASHBOARD.mdへ反映済み。

---

## Sprint3 結果

Google Search Console連携を実装した。

取得項目:

- クリック数
- 表示回数
- CTR
- 平均掲載順位

`core/kpi/search_console.py`を追加し、`generate_kpi_dashboard.py`でKPI_DASHBOARD.mdへ反映済み。

## Sprint3 Blocker

- Search Console OAuthトークンに`webmasters.readonly`スコープがない場合は0を返す。
- Search Consoleプロパティ権限がない場合は0を返す。

---

## Search Console認証テスト

実行日:

2026-07-05

## 実行内容

- Google OAuth初回認証を起動
- `webmasters.readonly`スコープで認証URLを発行
- `.secrets/search_console_token.json`生成を確認
- `core.kpi.search_console.fetch()`でKPI取得を確認

## 結果

- OAuth認証URL発行: 成功
- ブラウザ起動: 実行
- `search_console_token.json`生成: 未生成
- クリック数: 0
- 表示回数: 0
- CTR: 0
- 平均掲載順位: 0

## Blocker

OAuth承認がブラウザ側で完了しなかったため、`search_console_token.json`は生成されていない。

## 次の対応

Google認証画面でSearch Console閲覧権限を持つアカウントを選択し、承認を完了する。
承認完了後、`core.kpi.search_console.fetch()`でクリック数、表示回数、CTR、平均掲載順位を再取得する。

---

## Search Console siteUrl一覧確認

実行日:

2026-07-06

## 実行内容

- 現在の`.secrets/search_console_token.json`を使用
- Google Search Console API `sites.list`を実行
- 取得可能な`siteUrl`一覧を確認
- `.env`のSearch Console設定値と比較

## siteUrl一覧

未取得

## .env比較

- `SEARCH_CONSOLE_SITE_URL`: 未設定
- `GOOGLE_SEARCH_CONSOLE_SITE_URL`: 未設定
- `P003_WORDPRESS_URL`: `https://munoimp.com`
- 比較対象: `https://munoimp.com`
- 一致確認: 未確認

## 結果

Search Console APIがGoogle Cloudプロジェクトで未有効のため、`siteUrl`一覧を取得できなかった。

## Error

`Google Search Console API has not been used in project 492958396539 before or it is disabled.`

## Blocker

Google Cloud ConsoleでSearch Console APIを有効化する必要がある。

## 次の対応

Google Cloud ConsoleでSearch Console APIを有効化し、反映後に再度`sites.list`を実行する。
取得できた`siteUrl`を`.env`の`SEARCH_CONSOLE_SITE_URL`または`GOOGLE_SEARCH_CONSOLE_SITE_URL`へ設定する。

---

## Search Console siteUrl一覧確認 再実行

実行日:

2026-07-06

## 実行内容

- 現在の`.secrets/search_console_token.json`を使用
- Google Search Console API `sites.list`を実行
- 現在ログイン中のアカウントで取得可能な`siteUrl`一覧を確認
- `.env`の`SEARCH_CONSOLE_SITE_URL`と比較

## siteUrl一覧

- `https://www.munoimp.com/`

## .env比較

- `SEARCH_CONSOLE_SITE_URL`: 未設定
- `GOOGLE_SEARCH_CONSOLE_SITE_URL`: 未設定
- `P003_WORDPRESS_URL`: `https://munoimp.com`
- 比較対象: 未設定
- 一致確認: 不一致

## 結果

Search Console API接続に成功し、現在のアカウントで取得できる`siteUrl`一覧を取得した。

`.env`の`SEARCH_CONSOLE_SITE_URL`は未設定のため、Search Consoleプロパティとは一致していない。

## 次の対応

`.env`へ以下を設定する。

```text
SEARCH_CONSOLE_SITE_URL=https://www.munoimp.com/
```

---

## Search Console siteUrl一覧確認 再実行2

実行日:

2026-07-06

## 実行内容

- 現在の`.secrets/search_console_token.json`を使用
- Google Search Console API `sites.list`を実行
- 現在ログイン中のアカウントで取得可能な`siteUrl`一覧を確認
- `.env`の`SEARCH_CONSOLE_SITE_URL`と比較

## siteUrl一覧

- `https://www.munoimp.com/`

## .env比較

- `SEARCH_CONSOLE_SITE_URL`: `https://www.munoimp.com/`
- `GOOGLE_SEARCH_CONSOLE_SITE_URL`: 未設定
- `P003_WORDPRESS_URL`: `https://munoimp.com`
- 比較対象: `https://www.munoimp.com/`
- 一致確認: 一致

## 結果

Search Console API接続に成功し、現在のアカウントで取得できる`siteUrl`一覧を取得した。

`.env`の`SEARCH_CONSOLE_SITE_URL`はSearch Consoleプロパティと一致している。

---

## Search Console clicks=0 デバッグ

実行日:

2026-07-06

## 前提

- OAuth成功
- Search Console API成功
- `siteUrl`取得成功
- `SEARCH_CONSOLE_SITE_URL`一致

## 確認項目

① APIへ送信している`startDate`

`2026-06-08`

② APIへ送信している`endDate`

`2026-07-05`

③ APIへ送信している`dimensions`

```json
[]
```

④ APIへ送信している`rowLimit`

```json
1
```

⑤ APIレスポンスJSON

```json
{
  "siteUrl": "https://www.munoimp.com/",
  "request": {
    "startDate": "2026-06-08",
    "endDate": "2026-07-05",
    "dimensions": [],
    "rowLimit": 1
  },
  "response": {
    "rows": [
      {
        "clicks": 0,
        "impressions": 0,
        "ctr": 0,
        "position": 0
      }
    ],
    "responseAggregationType": "byProperty"
  },
  "error": null
}
```

## ログ出力

APIレスポンスは以下へ出力済み。

`07_KPI_Dashboard/search_console_debug.log`

## 切り分け結果

API接続、認証、対象`siteUrl`、リクエスト形式は正常。

Search Console APIのレスポンス自体が、過去28日分として`clicks=0`、`impressions=0`、`ctr=0`、`position=0`を返している。

そのため、現時点の原因はコード側の取得失敗ではなく、対象プロパティ`https://www.munoimp.com/`に該当期間の検索パフォーマンスデータが存在しない、またはSearch Console側でまだデータが反映されていない可能性が高い。

---

## Sprint4 結果

Google Analytics 4連携を実装した。

取得項目:

- ユーザー数
- セッション数
- PV
- 平均エンゲージメント時間

`core/kpi/ga4.py`を追加し、`generate_kpi_dashboard.py`でKPI_DASHBOARD.mdへ反映済み。

## Sprint4 Blocker

- `GA4_PROPERTY_ID`または`GOOGLE_ANALYTICS_PROPERTY_ID`が未設定の場合は0を返す。
- GA4 OAuthトークンに`analytics.readonly`スコープがない場合は0を返す。
- GA4プロパティ権限がない場合は0を返す。
