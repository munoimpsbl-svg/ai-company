# AI COMPANY 画像生成運用 引き継ぎ書

## 目的

別PCでも、AI COMPANYのSNS画像生成作業を同じ品質・同じルールで再現できるようにする。

対象は主に以下。

- Daily Brief確認
- MIKU / RIOの画像候補生成
- 社長確認用の候補一覧作成
- EXIF削除と画像最適化
- Google Drive反映前のローカル候補管理
- 生成品質DBと品質レポートの更新

## 前提

- Google Driveを唯一の正とする。
- 自動投稿はしない。
- SNSログイン操作はしない。
- ブラウザ投稿操作はしない。
- 既存フォルダ、既存ファイル、既存フローを勝手に壊さない。
- 画像は最終的に社長判断で採用する。

## 必須事項の優先順位

Daily Briefや社長指示に書かれた必須事項は、Codex判断で変更しない。

優先順位:

1. 社長の最新指示
2. Daily Briefの必須事項
3. キャラクター固定プロフィール
4. 破綻回避、背景文字回避、保存運用

禁止:

- 破綻回避を理由に、衣装・体型・場所・本人感・マスク・ストーリーを別条件へ置き換える。
- 安全通過を理由に、社長指定の必須表現を勝手に弱める。
- 「自然に見える」という理由で、キャラのテーマを消す。
- 派生生成画像を、社長指定の本人参照より優先する。

衝突がある場合:

- 勝手に変更せず、社長確認事項として止める。

## 必要な環境

- macOS
- Codex Desktop
- Python 3
- Pillow
- GitHub版EXIF削除アプリ
- ImageOptim(macOS補助)
- Google Driveへアクセスできる認証設定

EXIF削除は必須。標準はGitHub Actions上の `stefmolin/exif-stripper` / `strip-exif`。
画像をGitHubへpushすると、`.github/workflows/strip-exif.yml` がEXIF削除を実行する。
ローカルではGitHub版EXIF削除アプリ、またはPython/Pillowのフォールバックを通す。
ImageOptimはmacOSで使える場合のみ補助的な圧縮として扱う。

## Google Drive構成

現在の基準構成。

```text
AI COMPANY
00_社長室
01_グラビア事業部
02_アダルト事業部
03_SNS事業部
04_システム開発部
30_共通素材
40_テンプレート
50_ナレッジ
99_アーカイブ
```

SNS事業部の重要フォルダ。

```text
03_SNS事業部
01_Characters
    MIKU
    RIO
    AIRI
04_Daily
```

重要:

- `03_SNS事業部/01_Characters/MIKU` は既存運用の基準。
- 勝手に移動、リネーム、削除しない。
- サブフォルダ追加が必要な場合は、先に社長へ提案する。

## ローカル保存先

作業PCでは以下を基本にする。

```text
/Users/izumisub/Documents/ai会社/
```

日別成果物。

```text
02_Daily_Output/YYYY-MM-DD/
    MIKU/
        morning/
            images/
            prompt.txt
            instagram.txt
            x.txt
            report.md
        night/
            images/
            prompt.txt
            instagram.txt
            x.txt
            report.md
    RIO/
        morning/
            images/
            prompt.txt
            instagram.txt
            threads.txt
            report.md
        night/
            images/
            prompt.txt
            instagram.txt
            threads.txt
            report.md
    CONTACT_SHEET_*.jpg
    RUN_REPORT.md
```

既存画像をすぐ上書きしない。やり直し候補は別名で保存する。

例:

```text
2026-07-11_MIKU_night_cafe45_selfie_01.png
2026-07-11_RIO_night_roomwear_rework_01.png
```

## Daily Brief運用

Daily Briefにはその日のテーマ、優先順位、投稿先、衣装テーマ、社長確認事項を記載する。

例:

```markdown
# Daily Brief

## Date
2026-07-11

## 優先順位
1、RIO
2、MIKU

## RIO
### 今日の投稿テーマ
① 友人と朝からカフェ
② 部屋で漫画読む

### 衣装テーマ
ゆったりTシャツ胸強調スタイル、ショルダーバッグ

### 投稿先
- Instagram
- スレッズ

### 社長確認事項
- 画像候補
- 投稿文
- RIO本人感
- 体型が参照設定からズレていないか
- 自撮り構図が一辺倒になっていないか
- 背景文字や固有名詞が破綻していないか

## MIKU
### 今日の投稿テーマ
① 朝1からヨガに行く
② 昼過ぎは友人とカフェ

### 衣装テーマ
① ヨガスタイル
② ゆるいおしゃれTシャツ、ショルダーバッグ、胸強調

### 社長確認事項
- 画像候補
- 投稿文
- 写真集導線
- MIKU本人感
- マスク着用
- 35歳の年齢感
- 体型がB95 / W60 / H95からズレていないか
```

## MIKU生成ルール

必須:

- 生成前に、MIKUの最優先本人参照画像を確認する。
- 車内生成画像や過去の派生生成画像を、本人参照の最優先にしない。
- 本人参照が複数ある場合は、社長が指定した「これがMIKU」という画像を最優先する。
- MIKU本人感を最優先。
- マスク着用必須。
- 35歳の成人日本人女性としての落ち着いた年齢感。
- 若くしすぎない。
- 韓国アイドル顔、AI美女顔、20代前半風にしない。
- 目を大きくしない。
- 顔を小さくしすぎない。
- 黒からダークブラウンの柔らかいロングヘア。
- 自然な前髪。
- 体型は現在 `B95 / W60 / H95` を基準にする。
- 胸元や体型の最終安全判定は社長判断。

MIKUの自部屋:

```text
大きな窓、白いレースカーテン、グレージュのカーテン、
木製デスク、白からベージュのベッド、木製棚、
小さな観葉植物、ドライフラワー、マグカップ、
卓上ミラー、暖色の間接照明。
生活感はあるが清潔。
大人の一人暮らし感。
都会のマンション、裏は緑豊かな公園。
```

MIKUの趣味:

- ヨガ
- ピラティス

## RIO生成ルール

必須:

- RIOは素顔キャラ。
- マスクは不要。指定がある場合のみ使う。
- 22歳。
- 身長163cm。
- 体型は `B90 / W60 / H90`。
- 黒髪ロング、自然な前髪。
- 美少女すぎる、アイドルすぎる、AI美女すぎる方向に寄せない。
- 自撮り感を重視する。
- 寄り、引き、斜め上、鏡、外出先など構図を分ける。
- 普段着とジム服は分ける。
- 普段着のままジムでトレーニングしない。
- ジムでは他の人がいる自然な環境も入れる。
- 足を見せるスタイルでは短パンを使う。
- ショルダーバッグ、斜め掛けバッグのバリエーションを入れてよい。

RIOの部屋:

```text
シンプルな1ルームマンション。
薄いグレージュ壁、低いベッド、白からオフホワイトの寝具、
小さな木製デスク、最低限の棚。
清潔だが生活感あり。
豪華ホテル、撮影スタジオ、過剰な装飾は禁止。
```

RIOの部屋着:

```text
チャコールグレーの少しゆったりしたTシャツ。
黒のソフトなショートパンツ。
室内では裸足または靴下。
靴を履かない。
```

## 共通生成ルール

構図:

- 自撮りとして成立しているか確認する。
- 寄り、引き、斜め上45度、横寄り、鏡、座り、立ちを混ぜる。
- 同じ構図ばかりにしない。
- アクセサリー、バッグ、時計などはポーズごとに整合性を取る。
- 背景に読める文字、ロゴ、固有名詞を出さない。
- カフェ看板、メニュー、カップ、ナンバー、店名は読めないようにする。
- 鏡自撮りでは反射、スマホ、手、脚、背景の位置関係を確認する。
- 部屋の中で靴を履かせない。
- 不自然なポーズ、首、肩、肘、手、膝、足先の破綻を確認する。

画像枚数:

- 通常は1投稿あたり5枚。
- 最低3枚。
- 朝と夜の2投稿がある日は、各キャラ各枠で必要枚数を作る。

失敗時:

- 失敗しても全体処理を止めない。
- 最低枚数に届かない場合は `report.md` に記録する。
- 記録項目:
  - 生成失敗数
  - 成功枚数
  - 失敗理由
  - 社長確認事項

## 日本車の右ハンドル注意

MIKUの車内セルフィーで最重要。

日本の右ハンドルとは、画像上で単純に右側へハンドルを置くことではない。

参照構図では以下が正解。

```text
画面左側:
- 運転席ドア
- 運転席窓
- ハンドル

画面右側:
- センターコンソール側
```

ユーザーが指定した正しい例では、ハンドルは画面左下に見える。

NG:

- 画像右側にハンドルを出して「右ハンドル」と解釈する。
- センターコンソールを大きく見せる。
- 左ハンドル車に見える構図。
- 車内の物理関係が曖昧な構図。

車内画像を生成する場合は、まずこのルールをプロンプトに明記する。

## EXIF削除・画像最適化運用

生成後、保存した画像とコンタクトシートに必ずEXIF削除を行う。

Windows:

```powershell
.\installer\windows\optimize_images.ps1 .\02_Daily_Output\YYYY-MM-DD\MIKU
```

Google Drive同期フォルダを監視する場合:

```text
GOOGLE_DRIVE_SYNC_ROOT=G:\マイドライブ\AI_COMPANY
```

```powershell
.\Watch-GoogleDrive-EXIF.bat
```

Google Drive同期フォルダが正。監視スクリプトは画像投入後、ファイルが安定してからEXIF削除を行う。

GitHub Actions:

```text
.github/workflows/strip-exif.yml
.pre-commit-config.yaml
```

ローカルでGitHub版EXIF削除アプリを使う場合は `.env` に `EXIF_CLEANER_COMMAND` を設定する。

```text
EXIF_CLEANER_COMMAND=C:\Tools\exif-cleaner\exif-cleaner.exe "{path}"
```

macOSでImageOptimも併用する場合:

例:

```bash
open -a ImageOptim \
  /Users/izumisub/Documents/ai会社/02_Daily_Output/YYYY-MM-DD/MIKU/night/images/*.png \
  /Users/izumisub/Documents/ai会社/02_Daily_Output/YYYY-MM-DD/CONTACT_SHEET_*.jpg
```

ImageOptimは自動で閉じない場合があるため、併用時は処理後に終了する。

```bash
osascript -e 'tell application "ImageOptim" to quit'
```

処理完了の目安:

- ファイルサイズが15秒以上変化しない。
- その後にImageOptimを終了する。

## コンタクトシート作成

社長確認用に候補一覧を作る。

例:

```text
CONTACT_SHEET_MIKU_NIGHT_CAFE45_SELFIE_2026-07-11.jpg
CONTACT_SHEET_RIO_NIGHT_ROOMWEAR_REWORK_2026-07-11.jpg
```

一覧画像には番号を入れる。

```text
01
02
03
04
05
```

社長が番号で指示できる状態にする。

## 生成品質DB

生成候補は以下のコマンドで品質DBへ登録する。

```bash
python3 scripts/update_generation_quality.py
```

出力:

```text
03_SNS事業部/03_Analytics/generation_quality.sqlite3
03_SNS事業部/03_Analytics/GENERATION_QUALITY_REPORT.md
```

Runner実行時は`GPT Image Quality`ステップで自動更新する。

評価する項目:

- 画像が正常に開けるか
- 解像度、画角
- EXIF削除状態
- prompt.txt / report.md の有無
- report.md内の完全破綻、別人感、顔ズレ、不自然、右ハンドル誤りなどの記録
- 採用候補、優先候補の記録

注意:

- 品質スコアは自動採用ではない。
- 社長判断前の絞り込み補助として使う。
- 本人感、体型、構図、安全判定は社長判断が最終。
- 評価対象はGPT画像生成の候補に限定する。
- 外部画像生成UI、外部画像ストアは今回の対象外。

## チェックリスト

生成後に必ず確認する。

- 本人感があるか
- 本人固定リファレンスを最優先にしているか
- 衣装資料、構図資料、画質資料の人物顔に引っ張られていないか
- `identity_review.json` に本人感スコアを入力したか
- `identity_review.json` に身体破綻、自撮り整合性、背景文字、場面物理、明るさチェックを入力したか
- 年齢設定が合っているか
- 体型設定が大きくズレていないか
- 衣装がDaily Briefと合っているか
- 同じ投稿内で服装が不自然に変わっていないか
- 自撮りとして成立しているか
- 構図が一辺倒ではないか
- 背景文字、固有名詞、ロゴ、ラベルが破綻していないか
- 手、腕、首、肩、膝、脚、足先が破綻していないか
- 鏡の場合、反射と実体が矛盾していないか
- 室内で靴を履いていないか
- 車内の場合、日本車の右ハンドルとして成立しているか
- ImageOptimを通したか
- 既存ファイルを勝手に上書きしていないか

## 本人感チェックの必須工程

2026-07-27以降、AI-VQCは本人感レビュー未入力の画像をPASSにしない。

生成後の順序:

1. コンタクトシートを作成する。
2. ベースリファレンスシートを横に置いて、顔、髪型、年齢感、体型を目視比較する。
3. 各シーンの `identity_review_template.json` を `identity_review.json` にコピーする。
4. 画像ごとに `identity_score` とチェック項目を入力する。
5. AI-VQCを再実行する。
6. `PASS` は本人感レビュー済みの候補だけにする。

点数基準:

```text
90-100: 本人感が強い。候補として進めてよい。
80-89 : 採用前に社長確認。大きなズレはない。
65-79 : 再生成候補。顔、髪型、年齢感、体型のどれかが弱い。
0-64  : FAIL。別人化、年齢感崩れ、顔の基本ズレ。
```

入力例:

```json
{
  "images": {
    "2026-07-27_RIO_morning_01.png": {
      "identity_score": 88,
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
      "notes": "顔は許容範囲。衣装資料の人物顔には寄っていない。"
    }
  }
}
```

絶対NG:

- 画像が綺麗だから本人感チェックを省略する。
- VQCの自動数値だけでPASS扱いにする。
- 衣装候補画像の顔や髪型を採用してしまう。
- 構図資料の人物をキャラクター本人として扱う。
- 明るさ、身体破綻、自撮り矛盾を見ずに「生成できた」として進める。

## 2026-07-11時点の直近作業メモ

作成した候補:

```text
MIKU night:
2026-07-11_MIKU_night_cafe45_selfie_01.png
2026-07-11_MIKU_night_cafe45_selfie_02.png
2026-07-11_MIKU_night_cafe45_selfie_03.png

RIO night:
2026-07-11_RIO_night_roomwear_rework_01.png
2026-07-11_RIO_night_roomwear_rework_02.png
2026-07-11_RIO_night_roomwear_rework_03.png
2026-07-11_RIO_night_roomwear_rework_04.png
2026-07-11_RIO_night_roomwear_rework_05.png
```

コンタクトシート:

```text
CONTACT_SHEET_MIKU_NIGHT_CAFE45_SELFIE_2026-07-11.jpg
CONTACT_SHEET_RIO_NIGHT_ROOMWEAR_REWORK_2026-07-11.jpg
```

注意:

- この時点ではGoogle Drive上の既存採用画像は差し替えていない。
- ローカル候補として保存。
- ImageOptim処理済み。

## 別PCへ移行する手順

1. Codex Desktopをセットアップする。
2. Python 3とPillowを使える状態にする。
3. ImageOptimをインストールする。
4. Google Drive認証を設定する。
5. Google DriveからAI COMPANY構成を確認する。
6. ローカル作業フォルダを作成する。

```text
/Users/ユーザー名/Documents/ai会社/
```

7. 必要なら既存の `02_Daily_Output` をコピーする。
8. Daily Briefを読み込む。
9. キャラクタープロフィールを読み込む。
10. 画像生成する。
11. ローカルに候補保存する。
12. コンタクトシートを作成する。
13. ImageOptimを通す。
14. 社長確認を受ける。
15. 明示指示がある場合のみGoogle Driveへ反映する。

## 絶対にやらないこと

- 自動投稿
- SNSログイン操作
- ブラウザ投稿操作
- Drive内フォルダの勝手な追加
- Drive内フォルダ名の変更
- 既存ファイルの勝手な削除
- 採用前の画像上書き
- ユーザー確認なしの大規模整理
