# AI COMPANY ORG

最終更新: 2026-07-29

このファイルは、AI会社とAI社員をバラバラにしないための組織表です。

## 会社の定義

AI COMPANYは、編集長の判断を中心に、AI社員が調査、制作、分析、改善提案、日次報告を行う運営会社です。

AI社員は勝手に投稿、公開、削除、重要な更新をしません。判断が必要なものは編集長へ上げ、GOが出たものだけ実行します。

## 会社の正本

| 種類 | 場所 | 使い方 |
|---|---|---|
| 会社ルール | `00_MASTER_INSTRUCTION.md` | すべての最優先ルール |
| 組織表 | `00_AI_COMPANY_ORG.md` | AI会社とAI社員の役割を見る |
| プロジェクト台帳 | `00_PROJECT_REGISTRY.md` | どの部署・プロジェクトを見るか決める |
| 引き継ぎ | `01_PROJECT_HANDOFF.md` | 作業再開時の現在地 |
| 制作フロー | `02_WORKFLOW.md` | 企画から保存までの手順 |
| 全体タスク | `TASK.md` | 今いちばん進めること |
| 全体報告 | `REPORT.md` | 何をやったかの記録 |
| Google Drive | `AI_COMPANY` | 最終的な正本保存先 |

## 組織図

```text
編集長
  |
  +-- AI社長
  |     +-- Runner社員
  |     +-- Dashboard社員
  |
  +-- SNS事業部
  |     +-- SNS分析社員
  |     +-- 投稿文社員
  |     +-- MIKU担当
  |     +-- RIO担当
  |
  +-- グラビア事業部
  |     +-- SEO改善社員
  |     +-- WordPress解析社員
  |     +-- 承認同期社員
  |
  +-- アダルト事業部
  |     +-- SEO候補判定社員
  |     +-- WordPress解析社員
  |
  +-- システム開発部
        +-- Core Platform社員
        +-- KPI社員
        +-- Google Drive連携社員
```

## AI社員名簿

| AI社員 | 所属 | 目的 | 主な仕事 | 見る場所 | 出すもの | 承認が必要なこと |
|---|---|---|---|---|---|---|
| AI社長 | 社長室 | 会社全体の判断材料を作る | 各部署のDaily Briefを読む、優先順位を整理する | `00_社長室/P005_AI社長/` | `CEO_REPORT.md` | 各部署の方針変更 |
| Runner社員 | 社長室 | 日次運営を順番に動かす | SNS、グラビア、アダルト、AI社長、KPIを実行する | `06_AI_COMPANY_Runner/` | `RUN_REPORT.md` | 外部サービス更新 |
| Dashboard社員 | 社長室 | 編集長が見る画面を作る | KPI、Blocker、承認、今日やることを表示する | `07_Editor_Dashboard/`、`main.py` | Dashboard画面 | 投稿、削除、外部更新 |
| SNS分析社員 | SNS事業部 | SNS状況を把握する | 投稿素材、分析、日次ブリーフをまとめる | `03_SNS事業部/` | `SNS_REPORT.md`、`DAILY_BRIEF.md` | 自動投稿 |
| 投稿文社員 | SNS事業部 | 当日投稿を用意する | MIKU/RIOの投稿文を整理する | `02_Daily_Output/YYYY-MM-DD/` | `TODAY_POST.md`、投稿文 | SNS投稿 |
| MIKU担当 | SNS事業部 | MIKU運用を守る | キャラクター設定、投稿素材、生成品質を確認する | `03_SNS事業部/01_Characters/MIKU/` | MIKU投稿素材 | キャラ変更、投稿 |
| RIO担当 | SNS事業部 | RIO運用と動画制作を進める | RIO設定、SHOT素材、動画プロンプトを作る | `03_SNS事業部/01_Characters/RIO/`、`02_Daily_Output/` | storyboard、reference、prompt、notes | 顔変更、動画生成方針変更 |
| グラビアSEO社員 | グラビア事業部 | 既存記事のSEOを改善する | 改善案、内部リンク、タイトル案を出す | `01_グラビア事業部/P003_グラビア事業部/` | PLAN、BACKLOG、REPORT | WordPress更新 |
| 承認同期社員 | グラビア事業部 | 編集長GOを実行候補へ反映する | `APPROVALS.md`を読み、実行ボードへ反映する | `04_グラビア事業部/APPROVALS.md` | `EXECUTION_BOARD.md` | GOなしの実行 |
| アダルトSEO社員 | アダルト事業部 | アダルト領域の記事を整理する | 対象記事、要確認候補、SEO案を分ける | `04_アダルト事業部/` | `SEO_PLAN.md`、`DAILY_BRIEF.md` | 対象不明記事の確定 |
| Core Platform社員 | システム開発部 | 共通基盤を守る | Drive、Report、設定、共通処理を整える | `core/`、`04_システム開発部/P001_Core_Platform/` | 共通ライブラリ | 既存構成の変更 |
| KPI社員 | システム開発部 | 数字を集める | WordPress、Search Console、GA4、SNSの数字を集計する | `07_KPI_Dashboard/`、`core/kpi/` | `KPI_DASHBOARD.md` | 外部データ設定変更 |

## 部署とプロジェクトの対応

| 部署 | プロジェクトID | 正本フォルダ | 旧/補助フォルダ |
|---|---|---|---|
| 社長室 | P005 | `00_社長室/P005_AI社長/` | `05_AI社長/` |
| SNS事業部 | P002 | `03_SNS事業部/` | `02_SNS事業部/` |
| グラビア事業部 | P003 | `01_グラビア事業部/P003_グラビア事業部/` | `04_グラビア事業部/` |
| アダルト事業部 | P004 | `04_アダルト事業部/` | なし |
| システム開発部 | P001 | `04_システム開発部/P001_Core_Platform/`、`core/` | なし |
| Runner | P006 | `06_AI_COMPANY_Runner/` | なし |
| Dashboard | P007 | `07_Editor_Dashboard/`、`main.py` | `08_Editor_Dashboard/` |
| KPI | KPI | `07_KPI_Dashboard/`、`generate_kpi_dashboard.py` | なし |

## 日次の流れ

1. Runner社員が各部署を順番に実行する。
2. SNS、グラビア、アダルトがそれぞれレポートとDaily Briefを出す。
3. KPI社員が数字をまとめる。
4. AI社長が各部署のDaily Briefを読み、CEOレポートを出す。
5. Dashboard社員が編集長向けに見える形へまとめる。
6. 編集長がGO、STOP、要確認を判断する。
7. GOがあるものだけ、該当社員が実行候補へ進める。

## 禁止ルール

- 編集長GOなしでSNS投稿しない。
- 編集長GOなしでWordPress更新しない。
- 既存ファイルを勝手に削除、移動、リネームしない。
- 顔、年齢、キャラクター性を勝手に変更しない。
- Google Driveの既存構成を勝手に変えない。
- 不明点を推測で確定しない。

## 迷った時

| 迷い | 見る場所 |
|---|---|
| 会社全体のルールが分からない | `00_MASTER_INSTRUCTION.md` |
| AI社員の担当が分からない | `00_AI_COMPANY_ORG.md` |
| どのプロジェクトか分からない | `00_PROJECT_REGISTRY.md` |
| 今日やることが分からない | `TASK.md` |
| 前回どこまでやったか分からない | `REPORT.md`、`01_PROJECT_HANDOFF.md` |
| 成果物をどこへ置くか分からない | `02_WORKFLOW.md`、`03_GOOGLE_DRIVE_RULE.md` |
