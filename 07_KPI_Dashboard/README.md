# KPI Dashboard

## Sprint1

KPI Dashboardを内部レポート集計ではなく、取得元アダプタ経由で生成する構造へ変更する。

## 実行

```bash
python3 generate_kpi_dashboard.py
```

## 出力

- `KPI_DASHBOARD.md`
- `02_Daily_Output/YYYY-MM-DD/KPI_DASHBOARD.md`

## データ取得元

- `core/kpi/instagram.py`
- `core/kpi/x.py`
- `core/kpi/wordpress.py`
- `core/kpi/search_console.py`
- `core/kpi/ga4.py`
- `core/kpi/sales.py`
- `core/kpi/dashboard.py`

Sprint1では各取得元はダミー値を返す。

## Sprint2

WordPress KPI取得を実装した。

取得項目:

- 記事数
- 公開記事数
- カテゴリ数
- タグ数

実行:

```bash
python3 generate_kpi_dashboard.py
```

## Sprint3

Google Search Console KPI連携を実装した。

取得項目:

- クリック数
- 表示回数
- CTR
- 平均掲載順位

設定:

```text
SEARCH_CONSOLE_SITE_URL=https://example.com/
GOOGLE_SEARCH_CONSOLE_TOKEN=.secrets/search_console_token.json
```

実行:

```bash
python3 generate_kpi_dashboard.py
```

## Sprint4

Google Analytics 4 KPI連携を実装した。

取得項目:

- ユーザー数
- セッション数
- PV
- 平均エンゲージメント時間

設定:

```text
GA4_PROPERTY_ID=123456789
GOOGLE_GA4_TOKEN=.secrets/ga4_token.json
```

実行:

```bash
python3 generate_kpi_dashboard.py
```
