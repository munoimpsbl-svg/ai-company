# P002 SPEC

## Sprint1

SNS分析AIを実装する。

## 入力

- Instagram
- X

Sprint1では実API未接続のため、ダミーデータを使用してREPORT生成フローを確認する。

## 出力

- REPORT.md

## REPORT項目

- 投稿数
- フォロワー数
- エンゲージメント
- 伸びた投稿
- 改善候補
- Blocker

## 制約

- 投稿禁止
- 更新禁止
- 削除禁止
- 分析のみ

## Failure Handling

エラー時は停止せず、理由をREPORT.mdのBlockerへ出力する。

推測は禁止。未取得項目は「未取得」と記録する。
