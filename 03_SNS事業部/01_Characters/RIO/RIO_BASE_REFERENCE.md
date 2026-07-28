# RIO Base Reference

## Updated
2026-07-12

## Reference Image
`references/RIO_base_reference_2026-07-12.jpg`

## 画質資料 / Quality References
肌感・質感・スマホ写真らしさの参考として以下を使用する。
顔・年齢・体型・髪型の本人設定には使わない。
同じ場所、同じ状況、同じ背景を再現しない。

- `references/quality_texture_refs/RIO_texture_ref_01.jpg`
- `references/quality_texture_refs/RIO_texture_ref_02.jpg`
- `references/quality_texture_refs/RIO_texture_ref_03.jpg`
- `references/quality_texture_refs/RIO_texture_ref_04.jpg`
- `references/quality_texture_refs/README.md`

## 構図資料 / Composition References
構図、連続写真、自然な笑顔、飲食店での座り位置の参考として以下を使用する。
顔・年齢・体型・髪型の本人設定には使わない。
背景の固有名詞・看板・ロゴは生成時に再現しない。
同じ店、同じ看板、同じ窓外の景色、同じ料理、同じ器、同じ席、同じ椅子を再現しない。
資料をそのままコピーした構図にしない。

- `references/composition_refs/RIO_sequence_smile_ref_2026-07-20_01.jpg`
- `references/composition_refs/RIO_sequence_smile_ref_2026-07-20_02.jpg`
- `references/composition_refs/README.md`

## Priority
この参照画像をRIOの顔・体型・髪型の最優先ベース設定として扱う。

## Face Lock
- 顔が一定しない問題を防ぐため、生成時はこの画像の顔を最優先する。
- アーモンド形の目と自然な目尻を維持する。
- 透き通るような色白の肌を維持する。
- やや丸みのある唇と自然な口角を維持する。
- 黒髪ロングヘア、前髪、低めのお団子または自然なまとめ髪を基準にする。
- AI美女顔、美少女に寄せすぎた顔、別人化を避ける。

## Body Lock
- 22歳の成人女性。
- B90 / W60 / H90。
- 足を見せるRIOのテーマは崩さない。
- 細すぎず、スタイルが出る自然な体型を維持する。

## Generation Rule
- 今日分の再生成では、顔の安定を最優先する。
- 構図より本人感を優先する。
- 完全破綻以外は社長判断候補として残す。
- 通常自撮りでは撮影スマホは画面外。膝、机、座席、床、窓際、バッグ上にスマホを出さない。
- 白スマホ指定は、鏡自撮りまたは明示された小物カットでのみ適用する。通常自撮りに不要なスマホを追加しない。
- 画質はAI的な滑らかさを避け、スマホ写真の自然な肌理、軽いノイズ、柔らかいピント、圧縮感、不均一な光を優先する。
- 質感参照画像に顔・髪型・体型を引っ張られないこと。
- 構図・笑顔参考画像に顔・髪型・体型を引っ張られないこと。RIO本人感は必ず `RIO_base_reference_2026-07-12.jpg` を優先する。
- 画質資料と構図資料は別用途として扱い、同時に使う場合も本人固定資料より優先しない。
