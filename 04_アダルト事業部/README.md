# P004 アダルト事業部

アダルト領域をAI COMPANY標準運営へ載せるための部署です。

## 目的

- SEO改善
- CTR改善
- PV改善
- 回遊率改善
- 対象記事の改善履歴蓄積

## 実行

```bash
python3 04_アダルト事業部/main.py
python3 04_アダルト事業部/generate_daily_brief.py
```

## 出力

- `REPORT.md`
- `DAILY_BRIEF.md`

## 制約

- WordPress更新は禁止。
- WordPress投稿は禁止。
- WordPress削除は禁止。
- 解析のみ。
## 2026-07-28 SEO運用

- グラビア事業部と同じ改善バックログ方式を追加。
- `IMPROVEMENT_BACKLOG.md`、`EXECUTION_BOARD.md`、`SEO_PLAN.md`を作成。
- 対象記事判定は、タイトル・カテゴリ・タグで直接判定できる記事のみを対象とする。
- 抜粋のみ対象語が出る記事は`要確認候補`として扱う。
