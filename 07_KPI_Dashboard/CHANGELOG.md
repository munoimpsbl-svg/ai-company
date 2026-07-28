# KPI Dashboard CHANGELOG

## 2026-07-05

### Added

- `core/kpi/`を追加。
- `instagram.py`を追加。
- `x.py`を追加。
- `wordpress.py`を追加。
- `sales.py`を追加。
- `dashboard.py`を追加。
- 共通`fetch()`インターフェースを追加。

### Changed

- `generate_kpi_dashboard.py`を`core/kpi/dashboard.py`経由の取得へ変更。
- 内部レポート直接集計から取得元抽象化へ変更。

### Notes

- Sprint1ではダミー値を返す。
- 実データ取得は未実装。

---

## 2026-07-05

### Added

- Sprint2 WordPress KPI取得を実装。
- `core/kpi/wordpress.py`でWordPress REST APIから件数取得。
- 記事数、公開記事数、カテゴリ数、タグ数を取得。

### Changed

- `core/kpi/dashboard.py`でWordPress固有KPIを扱えるように拡張。
- `generate_kpi_dashboard.py`の表示項目にposts / published / categories / tagsを追加。

---

## 2026-07-05

### Added

- Sprint3 Google Search Console連携を実装。
- `core/kpi/search_console.py`を追加。
- クリック数、表示回数、CTR、平均掲載順位の取得インターフェースを追加。
- `.env.example`へSearch Console設定例を追加。

### Changed

- `core/kpi/dashboard.py`でSearch Console取得元を集計対象に追加。
- `generate_kpi_dashboard.py`の表示項目にclicks / positionを追加。

---

## 2026-07-06

### Added

- Sprint4 Google Analytics 4連携を実装。
- `core/kpi/ga4.py`を追加。
- ユーザー数、セッション数、PV、平均エンゲージメント時間の取得インターフェースを追加。
- `.env.example`へGA4設定例を追加。

### Changed

- `core/kpi/dashboard.py`でGA4取得元を集計対象に追加。
- `generate_kpi_dashboard.py`の表示項目にusers / sessions / page_views / engagement_timeを追加。
