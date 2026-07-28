# AI-VQC

AI Visual Quality Control System / AI質感監査部

## 目的

画像生成後に、人物、物・小物、背景・空間、写真品質、本人感を分けて監査し、投稿準備へ進める候補を選別する。

この監査はAI検出サービス回避ではなく、人間が見たときの違和感を減らすための品質管理。

## 実行

```bash
python3 scripts/run_visual_quality_control.py --date 2026-07-25 --character MIKU --slot morning_photobook_outfit
```

`--slot` を省略すると、そのキャラクター配下全体を監査する。

## 出力

対象シーン配下に以下を作成する。

```text
images/
  pass/
  review/
  fail/
reports/
  image_01_report.json
  image_02_report.json
  batch_summary.json
status.json
```

元画像は移動しない。`pass`、`review`、`fail` にはコピーを保存する。

## 数値化項目

各 `image_XX_report.json` には以下を保存する。

```json
{
  "scores": {
    "person": 0,
    "object": 0,
    "background": 0,
    "photo_quality": 0,
    "character_consistency": 0
  },
  "score_summary": {
    "average": 0.0,
    "minimum": 0,
    "pass_threshold_minimum": 80,
    "pass_threshold_average": 85,
    "fail_threshold_minimum": 64
  },
  "metrics": {
    "width": 0,
    "height": 0,
    "megapixels": 0.0,
    "aspect_ratio": 0.0,
    "file_size_bytes": 0,
    "bytes_per_megapixel": 0,
    "exif_cleaned": true,
    "luminance_range": 0,
    "luminance_mean": 0.0,
    "luminance_stddev": 0.0,
    "edge_mean": 0.0,
    "problem_marker_lines": 0,
    "person_problem_hits": 0,
    "object_problem_hits": 0,
    "background_problem_hits": 0,
    "consistency_problem_hits": 0,
    "resolution_component": 0,
    "aspect_ratio_component": 0,
    "file_size_component": 0,
    "contrast_component": 0,
    "edge_component": 0,
    "exif_component": 0
  }
}
```

`*_component` は100点満点の内訳スコア。

現時点で画像から機械的に数値化しているもの:

- 解像度
- 画角比率
- ファイルサイズ
- 1メガピクセルあたりのバイト数
- EXIF削除状態
- 明暗レンジ
- 平均輝度
- 輝度標準偏差
- エッジ量
- 既存レポートやノート内のNG記録ヒット数

## 判定

PASS:
- 全スコア80点以上
- 平均85点以上
- 重大エラーなし
- `identity_review.json` または画像別 `_notes.json` に本人感レビューが入力済み
- 本人感スコアが80点以上
- `base_reference_used` と `face_matches_base` が true
- 身体破綻、自撮り整合性、服装連動、背景文字、場面物理、明るさレビューがすべて true

REVIEW:
- 重大エラーはないが、いずれかの項目に確認が必要
- 本人感レビューが未入力
- 本人感スコアが65〜79点
- 顔、髪型、年齢感、体型のどれかに採用前確認が必要
- 身体破綻、自撮り整合性、服装連動、背景文字、場面物理、明るさレビューが未入力

FAIL:
- 重大エラーあり
- いずれかのスコアが64点以下
- 本人感スコアが64点以下
- `base_reference_used=false`
- `face_matches_base=false`
- `physical_integrity_ok=false`
- `hands_limbs_ok=false`
- `selfie_logic_ok=false`
- `scene_physics_ok=false`

## 本人感レビュー必須化

2026-07-27以降、本人感レビュー未入力の画像は自動PASSにしない。

理由:

- 解像度、EXIF、背景NG語だけでは「顔が別人」を止められない。
- 衣装資料や構図資料に顔が引っ張られる事故が多い。
- 本人感はMIKU/RIO運用の最重要品質なので、機械的に良い写真でも目視確認なしで合格にしない。

VQC実行後、各シーンに以下が自動作成される。

```text
identity_review_template.json
```

これをコピーまたはリネームして `identity_review.json` とし、画像ごとに目視点数を入力する。

```json
{
  "images": {
    "2026-07-27_RIO_morning_01.png": {
      "identity_score": 90,
      "base_reference_used": true,
      "face_matches_base": true,
      "age_matches": true,
      "hair_matches": true,
      "body_matches": true,
      "outfit_reference_limited_to_clothes": true,
      "physical_integrity_ok": true,
      "hands_limbs_ok": true,
      "selfie_logic_ok": true,
      "outfit_continuity_ok": true,
      "background_text_logo_ok": true,
      "scene_physics_ok": true,
      "lighting_ok": true,
      "notes": "RIOベースに近い。衣装資料の顔には寄っていない。"
    }
  }
}
```

点数基準:

- 90〜100: 本人感が強い。候補として進めてよい。
- 80〜89: 採用前に社長確認。大きなズレはない。
- 65〜79: 再生成候補。顔、髪型、年齢感、体型のどれかが弱い。
- 0〜64: FAIL。別人化、年齢感崩れ、顔の基本ズレ。

必須チェック:

- `base_reference_used`: 本人固定リファレンスを最優先したか
- `face_matches_base`: 顔がベース設定からズレていないか
- `age_matches`: 年齢感が合っているか
- `hair_matches`: 髪型、前髪、髪色が合っているか
- `body_matches`: 体型が設定から大きくズレていないか
- `outfit_reference_limited_to_clothes`: 衣装資料を服だけに使い、顔や体型を持ち込んでいないか
- `physical_integrity_ok`: 身体、首、肩、膝、足先が破綻していないか
- `hands_limbs_ok`: 手指、腕、脚の接続が自然か
- `selfie_logic_ok`: 自撮りとしてスマホ、腕、反射、画角が矛盾していないか
- `outfit_continuity_ok`: 同一シリーズ内で服装、髪型、小物が連動しているか
- `background_text_logo_ok`: 背景文字、ロゴ、固有名詞が破綻していないか
- `scene_physics_ok`: ジム器具、家具、床、鏡、車内などの物理関係が成立しているか
- `lighting_ok`: 場面に対して暗すぎない、明るすぎないか

## 注意

現在の実装は、画像ファイルの存在、解像度、EXIF削除状態、既存レポートやノート内のNG記録、本人感レビュー入力をもとにした監査基盤。

顔、指、背景、物理破綻を完全に目視代替するものではない。特に本人感は目視レビューを必須とし、最終判断はCEO確認を優先する。

画像ごとの補足ノートを置く場合は、画像と同じフォルダに以下の形式で保存できる。

```text
画像名_notes.json
```

例:

```json
{
  "memo": "顔破綻の記録あり"
}
```

この場合、該当画像は重大エラーとしてFAILになる。
