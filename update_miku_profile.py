import warnings

warnings.filterwarnings("ignore", category=FutureWarning, module="google.*")

from core.character import load_character_folder
from core.config import load_config
from core.drive import DriveClient, DriveError
from core.logger import setup_logger


PROFILE_UPDATE = """# MIKU 追加固定設定

## 必須事項

- マスク着用写真のMIKU本人感を最優先する。
- 白い不織布マスクを必ず着用する。
- マスクは鼻と口を必ず覆う。
- 口元は出さない。
- 目元、前髪、髪質、マスク姿を本人判定の基準にする。

## 生成時の判断ルール

- Codex側の必須判定は「MIKU本人感」と「白マスク必須」を最優先にする。
- 胸元、衣装の攻め具合、ポーズ、色気、ファン化に使えるかは社長判断に回す。
- 明確な別人化、マスクなし、口元表示、未成年に見える表現、重大な顔や手の崩れは不採用にする。

## 構図ルール

- 本人感とマスク以外は自由度を高くする。
- 寄り、引き、上半身、下半身、全身を混ぜる。
- 前、横、後ろ、振り向き、見上げ、見下ろし、屈む、立つ、座る、歩く、斜め構図を使う。
- 小物、衣装テーマ、場所、ポーズはDaily Briefに合わせて自由に展開する。
- 同じ窓際の座り構図だけを繰り返さない。

## 天候ルール

- 天候テーマはMIKU居住地域のウェザーリポートを確認してから使う。
- 雨、晴れ、曇り、気温、湿度、季節感を投稿文と画像に反映する。
- Daily Briefで明示されている場合を除き、思い込みで雨にしない。

## 自部屋設定

- 大きな窓。
- 白いレースカーテン。
- グレージュのカーテン。
- 木製デスク。
- 白からベージュ系のベッドまたはソファベッド。
- 木製棚。
- 小さな観葉植物。
- ドライフラワー。
- マグカップ、卓上ミラー。
- 暖色の間接照明。
- 都会のマンションの一室。
- 窓の外、またはマンション裏には緑豊かな公園が見える。
- 清潔だが生活感のある、大人の一人暮らし感。
"""


def main() -> int:
    logger = setup_logger()
    config = load_config()

    try:
        drive = DriveClient(config, logger)
        company_folder = drive.find_folder(config.company_folder_name)
        if not company_folder:
            raise DriveError(f"{config.company_folder_name}フォルダが見つかりません。")

        character_data = load_character_folder(
            drive, company_folder, config.character_name
        )
        profile = next(
            (
                child
                for child in character_data["children"]
                if child["name"].lower() == "profile.md"
            ),
            None,
        )
        if not profile:
            raise DriveError(
                f"{config.character_name}フォルダにprofile.mdが見つかりません。"
            )

        current = drive.read_text_file(profile["id"], profile["mimeType"])
        if "MIKU 追加固定設定" in current:
            logger.info("profile.mdには既にMIKU追加固定設定があります。追記はスキップします。")
            return 0

        drive.append_text_file(profile["id"], profile["mimeType"], PROFILE_UPDATE)
        logger.info("profile.mdへMIKU追加固定設定を保存しました。")
        return 0
    except DriveError as exc:
        logger.error("処理に失敗しました: %s", exc)
        return 1
    except Exception as exc:
        logger.exception("予期しないエラーが発生しました: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
