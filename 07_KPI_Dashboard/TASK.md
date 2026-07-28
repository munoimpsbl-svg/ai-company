# KPI Dashboard TASK

## Sprint1 取得元抽象化

Status
DONE

Priority
★★★★★

完了条件

- [x] `core/kpi/`を作成
- [x] `instagram.py`を作成
- [x] `x.py`を作成
- [x] `wordpress.py`を作成
- [x] `sales.py`を作成
- [x] `dashboard.py`を作成
- [x] 各ファイルに`fetch()`を実装
- [x] 共通戻り値形式に統一
- [x] KPI Dashboardが`dashboard.py`から取得する
- [x] ダミー値で動作確認

## Next

- Instagram実データ取得
- X実データ取得
- WordPress Analytics / Search Console接続
- Salesデータ接続

---

## Sprint2 WordPress KPI取得

Status
DONE

Priority
★★★★★

完了条件

- [x] `core/kpi/wordpress.py`でWordPress REST APIを読む
- [x] 記事数を取得
- [x] 公開記事数を取得
- [x] カテゴリ数を取得
- [x] タグ数を取得
- [x] `fetch()`の戻り値を指定形式にする
- [x] エラー時に停止しない
- [x] KPI Dashboardへ反映する

---

## Sprint3 Google Search Console連携

Status
DONE

Priority
★★★★★

完了条件

- [x] `core/kpi/search_console.py`を作成
- [x] クリック数を取得する構造を実装
- [x] 表示回数を取得する構造を実装
- [x] CTRを取得する構造を実装
- [x] 平均掲載順位を取得する構造を実装
- [x] `fetch()`の戻り値を指定形式にする
- [x] エラー時に停止しない
- [x] KPI Dashboardへ反映する
- [x] README / SPEC / TASK / REPORT / REVIEW / CHANGELOGを更新

---

## Sprint4 Google Analytics 4連携

Status
DONE

Priority
★★★★★

完了条件

- [x] `core/kpi/ga4.py`を作成
- [x] ユーザー数を取得する構造を実装
- [x] セッション数を取得する構造を実装
- [x] PVを取得する構造を実装
- [x] 平均エンゲージメント時間を取得する構造を実装
- [x] `fetch()`の戻り値を指定形式にする
- [x] エラー時に停止しない
- [x] KPI Dashboardへ反映する
- [x] README / SPEC / TASK / REPORT / REVIEW / CHANGELOGを更新
