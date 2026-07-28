# P006 CHANGELOG

## 2026-07-05

### Added

- P006 AI COMPANY Runnerを作成。
- P002、P003、P005の順次実行に対応。
- エラー継続実行に対応。
- RUN_REPORT.md生成に対応。

### Changed

- KPI_DASHBOARD.md生成をRunnerの実行順に追加。

---

## 2026-07-05

### Added

- TASK-002 Google Drive完全対応を実装。
- `artifact_sync.py`を追加。
- Runner成果物のGoogle Drive保存試行に対応。
- Google Drive保存失敗時も処理継続するように対応。
- 保存結果をRUN_REPORT.mdへ記録。

---

## 2026-07-08

### Added

- TASK-003 APPROVALS GO同期を実装。
- `approval_sync.py`を追加。
- RunnerのP003実行前に承認同期を実行するように変更。
- `APPROVALS.md`でGOの案件のみ`EXECUTION_BOARD.md`の今日実行へ移動し、状態を`実装待ち`へ変更。

### Safety

- WordPress更新なし。
- 投稿なし。
- 削除なし。
- 状態遷移のみ。

---

## 2026-07-22

### Added

- TASK-004 PLAN記事単位GO同期を実装。
- `plan_approval_sync.py`を追加。
- RunnerのP003実行前に`approval_sync.py`の後続としてPLAN同期を実行するように変更。
- `APPROVALS.md`のGOを`CATEGORY_FIX_PLAN.md`、`INTERNAL_LINK_PLAN.md`、`TITLE_IMPROVEMENT_PLAN.md`の記事単位GOへ反映。
- `PLAN_APPROVAL_SYNC_RESULT.md`を生成。

### Changed

- `run_p003_sprint2.py`でGoogle Drive保存に失敗しても、ローカルREPORT保存済みならP003解析を停止しないように変更。
- RunnerのGoogle Drive同期対象から`dist/`と`installer/`を除外し、日次同期を軽量化。
- `approval_sync.py`で`効果測定中`、`実装済み`、`完了`のGO案件を再び`実装待ち`へ戻さないように変更。
- P004 アダルト事業部をRunner実行順に追加。

### Safety

- WordPress更新なし。
- 投稿なし。
- 削除なし。
- 承認状態の同期のみ。
## 2026-07-28

- Google Drive同期対象にREADME / SPEC / TASK / REVIEW / CHANGELOGを追加。
- 外部公開用の`DEPLOY_RENDER.md`、`render.yaml`、`Procfile`、`runtime.txt`、`.streamlit/config.toml`を同期対象に追加。
