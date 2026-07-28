# RIO night_facefix_roomwear Report

## Date

2026-07-19

## Purpose

RIO夜候補が本人設定から外れていたため、GPT画像生成で顔優先の部屋着候補を5枚作り直した。

## Output

- `images/2026-07-19_RIO_night_facefix_roomwear_01.png`
- `images/2026-07-19_RIO_night_facefix_roomwear_02.png`
- `images/2026-07-19_RIO_night_facefix_roomwear_03.png`
- `images/2026-07-19_RIO_night_facefix_roomwear_04.png`
- `images/2026-07-19_RIO_night_facefix_roomwear_05.png`
- `../../CONTACT_SHEET_RIO_night_facefix_roomwear_2026-07-19.jpg`

## Reference

- 添付画像: 今日のRIO顔・髪・部屋着・ホクロ位置の最優先参照。
- `03_SNS事業部/01_Characters/RIO/references/RIO_base_reference_2026-07-12.jpg`: RIO公式ベース参照。

## Fixed Points

- RIO本人感を最優先。
- 白Tシャツ部屋着、黒ラウンジショートパンツで統一。
- 夜の自部屋、ベッド周りの自撮りに統一。
- 頬周辺の小さなホクロ位置をプロンプトで明示。
- 目を大きくしすぎない、AI美女化させない条件を追加。
- 室内で靴なし。
- 既存 `night_dinner_sendai` は上書きしない。

## Candidate Check

- `01`: 顔・髪・部屋着の参照一致が高い。標準候補。
- `02`: 少し引き。顔は安定、脚と服装も自然。
- `03`: 寄り気味。ホクロと表情が見やすい。
- `04`: 部屋の情報が多い。顔は安定、少し明るめ。
- `05`: 顔の寄りが強め。本人感とホクロ位置確認向き。

## Priority Candidates

- `01`
- `03`
- `05`

## Review Notes

- 添付画像寄せを優先したため構図差は控えめ。
- 既存夜候補より本人設定への寄せを優先。
- ホクロは小さく自然に入っているが、最終的な本人感と位置は社長確認。
- 背景の小物は読める文字が目立たない範囲。
- 完全破綻はなし。最終採用は社長判断。

## EXIF

- 画像5枚: EXIF削除済み。
- コンタクトシート: EXIF削除済み。

## Restrictions

- 自動投稿なし。
- SNSログイン操作なし。
- ブラウザ操作なし。
- 既存画像の削除・上書きなし。
