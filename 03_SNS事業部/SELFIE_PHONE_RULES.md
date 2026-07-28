# Selfie Phone Rules

最終更新: 2026-07-23

## 目的

自撮り画像で、撮影しているはずのスマホが膝・机・座席・窓際などに別物として写る破綻を防ぐ。

## 最優先ルール

- 通常の自撮りでは、撮影用スマホは画面外にある。
- 通常の自撮りでは、スマホを膝・机・座席・床・窓際・バッグ上に置かない。
- 通常の自撮りでスマホが画面内に写った場合はNG候補として扱う。
- 「スマホが写る場合は白」は、スマホを画面内に出す許可ではない。鏡自撮りや明示された小物カットの場合だけ適用する。

## 撮影タイプ別ルール

### 通常自撮り

- 撮影スマホ: 画面外。
- 画面内スマホ: 禁止。
- 手元、膝、机、座席、窓際にスマホがある候補はNG。

### 鏡自撮り

- スマホは手に持っている、または鏡に反射している必要がある。
- スマホ、手、腕、反射、目線、背景の位置関係が一致していること。
- スマホが複数ある候補はNG。

### 第三者撮影

- 自撮りではないため、撮影スマホは画面内に不要。
- スマホを小物として入れる場合は、Daily Briefで明示された場合のみ許可する。

## プロンプト必須文

通常自撮りでは以下を必ず入れる。

```text
This is a normal selfie. The camera phone is outside the frame. No visible phone anywhere in the image: not on lap, not on table, not on seat, not near the window, not on the floor, not on or near a bag.
```

鏡自撮りでは以下を必ず入れる。

```text
This is a mirror selfie. Exactly one phone is visible and it is held by the subject. The phone, hand, arm, reflection, gaze, and background must be physically consistent. No second phone anywhere.
```

## 生成後チェック

以下が1つでも該当した場合は社長確認前にNGまたは再編集対象にする。

- 通常自撮りなのにスマホが画面内にある。
- 膝、机、座席、床、窓際、バッグ上にスマホがある。
- 鏡自撮りでスマホと手・反射・目線が合っていない。
- スマホが2台以上ある。
- 「白スマホ固定」を理由に、不要なスマホが追加されている。
