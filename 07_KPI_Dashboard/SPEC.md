# KPI Dashboard SPEC

## Sprint1目的

KPI Dashboardを実データ取得に対応できる構造へ変更する。

今回は実データ取得までは行わず、取得元を抽象化する。

## 共通インターフェース

各取得元は`fetch()`を持つ。

戻り値:

```python
{
    "followers": 0,
    "impressions": 0,
    "engagement": 0,
    "ctr": 0,
    "pv": 0,
    "sales": 0,
}
```

## 取得元

- Instagram: `core/kpi/instagram.py`
- X: `core/kpi/x.py`
- WordPress: `core/kpi/wordpress.py`
- Sales: `core/kpi/sales.py`

## Dashboard

`generate_kpi_dashboard.py`は`core/kpi/dashboard.py`からKPIを取得する。

内部レポートファイルから直接KPIを読む処理はSprint1で廃止する。

## 制約

- Sprint1ではダミー値を使用する。
- 実API接続は次Sprint以降。
- WordPress更新、SNS投稿、Google Drive変更は行わない。

## Sprint2 WordPress KPI取得

## 対象

- `core/kpi/wordpress.py`

## 目的

ダミー値ではなくWordPressから取得できるKPIを返す。

## 取得対象

- 記事数
- 公開記事数
- カテゴリ数
- タグ数

## 返却形式

```python
{
    "posts": 0,
    "published": 0,
    "categories": 0,
    "tags": 0,
}
```

## 制約

- WordPress REST APIは読み取りのみ使用する。
- WordPress更新は行わない。
- エラー時は停止せず0を返す。

---

## Sprint3 Google Search Console連携

## 対象

- `core/kpi/search_console.py`

## 目的

Google Search ConsoleからKPIを取得する。

## 取得対象

- クリック数
- 表示回数
- CTR
- 平均掲載順位

## 返却形式

```python
{
    "clicks": 0,
    "impressions": 0,
    "ctr": 0,
    "position": 0,
}
```

## 設定

- `GOOGLE_SEARCH_CONSOLE_SITE_URL`
- `GOOGLE_SEARCH_CONSOLE_TOKEN`
- `GOOGLE_SEARCH_CONSOLE_START_DATE`
- `GOOGLE_SEARCH_CONSOLE_END_DATE`

`GOOGLE_SEARCH_CONSOLE_SITE_URL`が未設定の場合は`P003_WORDPRESS_URL`を使用する。

## 制約

- Google Search Console APIは読み取り専用スコープを使用する。
- 認証情報や権限が不足する場合は停止せず0を返す。
- WordPress更新、SNS投稿、Google Drive変更は行わない。

---

## Sprint4 Google Analytics 4連携

## 対象

- `core/kpi/ga4.py`

## 目的

Google Analytics Data APIからKPIを取得する。

## 取得対象

- ユーザー数
- セッション数
- PV
- 平均エンゲージメント時間

## 返却形式

```python
{
    "users": 0,
    "sessions": 0,
    "page_views": 0,
    "engagement_time": 0,
}
```

## 設定

- `GA4_PROPERTY_ID`
- `GOOGLE_ANALYTICS_PROPERTY_ID`
- `GOOGLE_GA4_TOKEN`
- `GOOGLE_GA4_START_DATE`
- `GOOGLE_GA4_END_DATE`

## 制約

- Google Analytics Data APIは読み取り専用スコープを使用する。
- 認証情報、プロパティID、権限が不足する場合は停止せず0を返す。
- WordPress更新、SNS投稿、Google Drive変更は行わない。
