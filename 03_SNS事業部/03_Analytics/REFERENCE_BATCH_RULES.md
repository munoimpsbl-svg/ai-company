# Reference Batch Rules

## Purpose

Use grouped reference batches for composition and photo-quality learning.
Do not ask the user to explain images one by one when the images are already in the shared reference folder.

## Shared Folder

- Root: `/Volumes/music/写真集/AI_COMPANY_Reference`
- Incoming: `/Volumes/music/写真集/AI_COMPANY_Reference/_incoming`
- Indexes: `/Volumes/music/写真集/AI_COMPANY_Reference/_index`
- Latest index pointer: `/Volumes/music/写真集/AI_COMPANY_Reference/_index/LATEST_INDEX.txt`

## Ingest Command

```bash
python3 scripts/ingest_reference_images.py --source "/Volumes/music/写真集/AI_COMPANY_Reference/_incoming" --recursive --label "daily_reference"
```

## Priority

1. Character profile and identity sheet
2. Daily Brief
3. Wardrobe rules
4. Reference batch

Reference images must never override character identity.

## Use From References

- composition
- camera height and distance
- pose rhythm
- expression rhythm
- light direction
- photo texture
- candid feeling
- sequence variation

## Do Not Use From References

- reference person's face
- reference person's hair
- reference person's body type
- exact outfit
- exact location
- logos, text, signs, labels
- exact restaurant, room, vehicle, or shop setup

## Required Report Output

When a reference batch is used, `report.md` must include:

- reference batch path
- purpose used: composition / quality_texture / mixed
- what was borrowed
- what was explicitly not borrowed
- identity check result
- outfit consistency check result
- text/logo/background breakage check result
