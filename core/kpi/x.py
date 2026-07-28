from pathlib import Path

from core.sns_analytics import MIKU_X_TARGET, analyze_sns_target


def fetch():
    analysis = analyze_sns_target(Path(__file__).resolve().parents[2], MIKU_X_TARGET)
    totals = analysis.totals
    return {
        "followers": totals["followers"],
        "impressions": totals["impressions"],
        "engagement": totals["engagement"],
        "ctr": totals["ctr"],
        "pv": 0,
        "sales": 0,
    }
