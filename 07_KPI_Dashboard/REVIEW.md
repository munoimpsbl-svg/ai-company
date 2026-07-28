# KPI Dashboard REVIEW

## Sprint1 Review

## 確認結果

- 取得元アダプタを作成済み。
- 全アダプタが共通`fetch()`を持つ。
- 戻り値形式は統一済み。
- Dashboardは`core/kpi/dashboard.py`から取得する。

## 残課題

- 各取得元の実API接続。
- 認証情報管理。
- エラー時の未取得表示。

---

## Sprint2 Review

## 確認結果

- WordPress REST APIからKPIを取得できる。
- `fetch()`は指定形式で返す。
- エラー時は停止せず0を返す。
- WordPress更新は未実行。

## 残課題

- Instagram / X / Salesの実データ接続。

---

## Sprint3 Review

## 確認結果

- Google Search Console連携用の`core/kpi/search_console.py`を追加済み。
- `fetch()`は指定形式で返す。
- 認証情報、スコープ、権限不足時も停止せず0を返す。
- KPI DashboardへSearch Console KPIを反映済み。
- WordPress更新、SNS投稿、Google Drive変更は未実行。

## 残課題

- Search Console用OAuthトークンの発行。
- Search Consoleプロパティ権限の確認。
- Instagram / X / Salesの実データ接続。

---

## Sprint4 Review

## 確認結果

- Google Analytics 4連携用の`core/kpi/ga4.py`を追加済み。
- `fetch()`は指定形式で返す。
- 認証情報、プロパティID、権限不足時も停止せず0を返す。
- KPI DashboardへGA4 KPIを反映済み。
- WordPress更新、SNS投稿、Google Drive変更は未実行。

## 残課題

- GA4用OAuthトークンの発行。
- GA4プロパティIDの設定。
- GA4プロパティ権限の確認。
- Instagram / X / Salesの実データ接続。
