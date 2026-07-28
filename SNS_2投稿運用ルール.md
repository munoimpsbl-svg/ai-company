# SNS 1日2投稿運用ルール

## 基本方針

- 朝投稿と夜投稿の2本立てで運用する。
- 朝の作業時点で、朝投稿分と夜投稿分をまとめて作成する。
- 投稿自体は自動実行しない。
- 画像候補、投稿文、社長確認レポートまでを作成する。

## 生成枚数

- 1投稿枠につき通常5枚生成する。
- 1投稿枠の最低必要枚数は3枚。
- 1キャラクターあたり、朝5枚 + 夜5枚 = 1日10枚を通常生成数とする。
- 1キャラクターあたり最低必要枚数は、朝3枚 + 夜3枚 = 1日6枚。
- RIOとMIKUを同日に実行する場合、通常生成数は合計20枚。

## 保存ルール

```text
02_Daily_Output/
YYYY-MM-DD/
CHARACTER/
morning/
images/
night/
images/
```

## 成果物

各キャラクターごとに以下を作成する。

- `morning/prompt.txt`
- `morning/instagram.txt`
- `morning/x.txt` または `morning/threads.txt`
- `morning/report.md`
- `night/prompt.txt`
- `night/instagram.txt`
- `night/x.txt` または `night/threads.txt`
- `night/report.md`

## 投稿内容の分け方

- 朝投稿は、その日の始まり、出勤/通学前、天気、今日の予定、軽い問いかけを中心にする。
- 夜投稿は、帰宅後、1日の振り返り、疲れ、安心感、ファンとの会話を中心にする。
- 同じ日の朝夜で服装は一貫させる。
- 夜は羽織りを脱ぐ、髪をまとめる、部屋着へ自然に変わるなど現実的な変化は社長判断で許可する。

## 社長確認

- 朝候補と夜候補を分けて採用候補を出す。
- 服装一貫性、本人感、設定違反、物理破綻、投稿文の自然さを確認項目に入れる。

## EXIF削除・画像最適化

- 画像保存後は必ずEXIF削除を行う。
- GitHub Actions上の `stefmolin/exif-stripper` / `strip-exif` を標準とする。
- 画像をGitHubへpushした場合、ActionsでEXIF削除を実行する。
- ローカルで同アプリが使えない環境では、Python/Pillowのフォールバックでメタデータを削除する。
- ImageOptimはmacOSで使える場合のみ補助的な圧縮として扱う。
