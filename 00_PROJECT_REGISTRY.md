# AI COMPANY PROJECT REGISTRY

最終更新: 2026-07-29

このファイルは、ローカル内に散らばっているAI COMPANYのプロジェクト、部署、運営社員、成果物の置き場所を一枚にまとめるための台帳です。

Google Driveの `AI_COMPANY` を正本とし、ローカル `/Users/izumisub/Documents/ai会社` は作業場所として扱います。

## まとめ方

- 正本: 今後の運用で優先して見る場所。
- 旧版/重複: 参照はするが、新規更新の中心にしない場所。
- 日次成果物: 日付ごとの出力・投稿文・生成結果。
- 運営社員: AI COMPANY内の役割。人間の編集長判断が必要な操作は自動実行しない。

## 現在の正本

| 区分 | 正本/優先場所 | 役割 |
|---|---|---|
| 全体ルール | `00_MASTER_INSTRUCTION.md` | 会社全体の最優先ルール |
| 組織表 | `00_AI_COMPANY_ORG.md` | AI会社とAI社員の役割表 |
| 引き継ぎ | `01_PROJECT_HANDOFF.md` | 再開時に最初に見る状態メモ |
| 制作フロー | `02_WORKFLOW.md` | 企画からDrive保存までの標準手順 |
| Drive運用 | `03_GOOGLE_DRIVE_RULE.md` / `AI_COMPANY_Google_Drive運用ルール.md` | Google Driveを正本にする運用 |
| 全体タスク | `TASK.md` | 直近の最優先タスク |
| 全体報告 | `REPORT.md` | 直近の作業報告 |
| ダッシュボード | `main.py` / `07_Editor_Dashboard/` | 編集長用の確認画面 |
| 日次出力 | `02_Daily_Output/YYYY-MM-DD/` | 当日ごとの成果物保存先 |

## プロジェクト一覧

| ID | プロジェクト/部署 | 正本/優先場所 | 状態 | 主な役割 |
|---|---|---|---|---|
| P001 | Core Platform | `04_システム開発部/P001_Core_Platform/` / `core/` | 稼働中 | 共通基盤、Drive連携、レポート保存、KPI部品 |
| P002 | SNS事業部 | `03_SNS事業部/` | 稼働中 | MIKU/RIO運用、SNS分析、日次ブリーフ、投稿素材管理 |
| P003 | グラビア事業部 | `01_グラビア事業部/P003_グラビア事業部/` | 稼働中 | WordPress解析、SEO改善案、承認後の改善実行 |
| P004 | アダルト事業部 | `04_アダルト事業部/` | 稼働中 | アダルト領域のWordPress解析、SEO候補分離 |
| P005 | AI社長 | `00_社長室/P005_AI社長/` | 稼働中 | 各部署のDaily Brief集約、CEOレポート生成 |
| P006 | AI COMPANY Runner | `06_AI_COMPANY_Runner/` | 稼働中 | 会社全体の日次実行、Drive保存、RUN_REPORT生成 |
| P007 | Editor Dashboard | `07_Editor_Dashboard/` / `main.py` | 稼働中 | 編集長が会社状態・承認・KPIを見る画面 |
| KPI | KPI Dashboard | `07_KPI_Dashboard/` / `generate_kpi_dashboard.py` | 稼働中 | WordPress、Search Console、GA4などのKPI集計 |
| RIO | RIO Cinematic Bible / Morning Routine | `02_Daily_Output/2026-07-19/RIO/morning_routine/` | 最優先制作 | RIO動画制作のSHOT資産化 |

## 運営社員/役割

| 運営社員 | 担当 | 見る場所 | 出すもの | 禁止/注意 |
|---|---|---|---|---|
| 編集長 | 最終判断、GO/STOP | Dashboard、`APPROVALS.md`、各PLAN | 承認、優先順位 | 不明点はAI側で勝手に確定しない |
| AI社長 | 会社全体の判断材料作成 | 各部署の`DAILY_BRIEF.md` | `CEO_REPORT.md`、P005 `REPORT.md` | 各部署ファイルを勝手に変更しない |
| Runner社員 | 日次実行係 | `06_AI_COMPANY_Runner/` | `RUN_REPORT.md`、日次成果物 | エラーがあっても次部署へ進む |
| SNS社員 | MIKU/RIO運用 | `03_SNS事業部/`、`02_Daily_Output/` | `SNS_REPORT.md`、`DAILY_BRIEF.md`、`TODAY_POST.md` | 自動投稿しない |
| グラビア社員 | SEO/WordPress改善 | `01_グラビア事業部/P003_グラビア事業部/` | 改善PLAN、BACKLOG、REPORT | 編集長GOなしで更新しない |
| アダルト社員 | アダルト領域SEO | `04_アダルト事業部/` | `SEO_PLAN.md`、`DAILY_BRIEF.md` | 対象判定を推測で確定しない |
| システム開発社員 | 共通基盤整備 | `core/`、`04_システム開発部/P001_Core_Platform/` | 共通処理、KPI取得元、Drive連携 | 既存構成を壊さない |
| Dashboard社員 | 編集長画面 | `07_Editor_Dashboard/`、`main.py` | Streamlit UI | 表示と承認記録を中心にする |

## 散らばり整理

| 似ている場所 | 判断 | メモ |
|---|---|---|
| `02_SNS事業部/` と `03_SNS事業部/` | `03_SNS事業部/`を優先 | `02_SNS事業部/`は初期SNS分析実装として参照扱い |
| `04_グラビア事業部/` と `01_グラビア事業部/P003_グラビア事業部/` | `01_グラビア事業部/P003_グラビア事業部/`を優先 | `04_グラビア事業部/APPROVALS.md`は承認センターとして利用中 |
| `05_AI社長/` と `00_社長室/P005_AI社長/` | `00_社長室/P005_AI社長/`を優先 | `05_AI社長/`は旧実装または互換参照 |
| `07_Editor_Dashboard/` と `08_Editor_Dashboard/` | `07_Editor_Dashboard/`を優先 | `08_Editor_Dashboard/`は旧版/履歴参照 |
| `07_KPI_Dashboard/` と `KPI_DASHBOARD.md` | 両方使う | 前者は仕様・実装管理、後者は生成レポート |
| `02_Daily_Output/` | 成果物置き場 | プロジェクト定義ではなく日次実行結果として扱う |
| `dist/`、`installer/`、`output/` | 配布/一時成果物 | 通常の運営判断では優先しない |

## 正本フォルダ案

今後の新規作業は、次の構造へ寄せる。

```text
00_社長室/
  P005_AI社長/
01_グラビア事業部/
  P003_グラビア事業部/
03_SNS事業部/
04_アダルト事業部/
04_システム開発部/
  P001_Core_Platform/
06_AI_COMPANY_Runner/
07_Editor_Dashboard/
07_KPI_Dashboard/
02_Daily_Output/
```

## 運用ルール

1. 新規タスクは、まずこの台帳で該当プロジェクトを確認する。
2. 更新する前に、各プロジェクトの `TASK.md` と `REPORT.md` を見る。
3. 実行結果は `02_Daily_Output/YYYY-MM-DD/` と各プロジェクトの `REPORT.md` に残す。
4. 外部サービスへの投稿、公開、削除、WordPress更新は編集長GOがある場合だけ実行する。
5. 旧版フォルダは、参照はしてよいが勝手に削除・移動・リネームしない。
6. Google Driveへ保存できる成果物は、最終的に `AI_COMPANY` へ反映する。

## 直近の整理タスク

- [ ] `02_SNS事業部/`の役割を「旧SNS分析実装」としてREADMEへ明記する。
- [ ] `05_AI社長/`の役割を「旧AI社長実装」としてREADMEへ明記する。
- [ ] `08_Editor_Dashboard/`の役割を「旧Dashboard」としてREADMEへ明記する。
- [ ] Dashboardにこの台帳へのリンクを追加する。
- [ ] Google Driveの `AI_COMPANY` 直下にもこの台帳を保存する。
- [ ] RIO Morning RoutineのSHOT一覧を確定し、P002/SNS制作と日次成果物の関係を明記する。
