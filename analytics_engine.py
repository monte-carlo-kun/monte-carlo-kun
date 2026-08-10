"""
NPB分析・予測スコア算出エンジン (全12球団対応 & ホームアドバンテージ考慮版)
"""

from scraper import fetch_today_starters

LEAGUE_AVG_ERA = 3.30
LEAGUE_AVG_OPS = 0.700

# ホームアドバンテージ（ホームチームの期待得点を1.03倍＝約3%上方修正）
HOME_ADVANTAGE = 1.03

TEAM_DATA = {
    # セ・リーグ
    "阪神タイガース": {"rpg": 3.8, "ops_vs_right": 0.710, "ops_vs_left": 0.670, "park_factor": 0.92, "bullpen_era": 2.20, "bullpen_fatigue": 1.05},
    "読売ジャイアンツ": {"rpg": 3.7, "ops_vs_right": 0.720, "ops_vs_left": 0.690, "park_factor": 1.08, "bullpen_era": 2.90, "bullpen_fatigue": 1.00},
    "広島東洋カープ": {"rpg": 3.4, "ops_vs_right": 0.670, "ops_vs_left": 0.650, "park_factor": 1.02, "bullpen_era": 3.10, "bullpen_fatigue": 0.95},
    "横浜DeNAベイスターズ": {"rpg": 4.1, "ops_vs_right": 0.730, "ops_vs_left": 0.710, "park_factor": 1.12, "bullpen_era": 3.40, "bullpen_fatigue": 1.10},
    "東京ヤクルトスワローズ": {"rpg": 3.9, "ops_vs_right": 0.700, "ops_vs_left": 0.720, "park_factor": 1.10, "bullpen_era": 3.80, "bullpen_fatigue": 1.00},
    "中日ドラゴンズ": {"rpg": 3.0, "ops_vs_right": 0.640, "ops_vs_left": 0.620, "park_factor": 0.85, "bullpen_era": 2.50, "bullpen_fatigue": 0.90},
    # パ・リーグ
    "福岡ソフトバンクホークス": {"rpg": 4.3, "ops_vs_right": 0.745, "ops_vs_left": 0.725, "park_factor": 1.05, "bullpen_era": 2.40, "bullpen_fatigue": 1.00},
    "北海道日本ハムファイターズ": {"rpg": 3.8, "ops_vs_right": 0.715, "ops_vs_left": 0.695, "park_factor": 1.00, "bullpen_era": 2.70, "bullpen_fatigue": 0.95},
    "千葉ロッテマリーンズ": {"rpg": 3.6, "ops_vs_right": 0.690, "ops_vs_left": 0.680, "park_factor": 0.95, "bullpen_era": 3.00, "bullpen_fatigue": 1.05},
    "オリックス・バファローズ": {"rpg": 3.5, "ops_vs_right": 0.685, "ops_vs_left": 0.670, "park_factor": 0.90, "bullpen_era": 2.80, "bullpen_fatigue": 1.00},
    "東北楽天ゴールデンイーグルス": {"rpg": 3.6, "ops_vs_right": 0.695, "ops_vs_left": 0.685, "park_factor": 1.00, "bullpen_era": 3.20, "bullpen_fatigue": 1.05},
    "埼玉西武ライオンズ": {"rpg": 3.1, "ops_vs_right": 0.640, "ops_vs_left": 0.630, "park_factor": 0.92, "bullpen_era": 3.30, "bullpen_fatigue": 1.10},
}

TODAY_STARTERS = fetch_today_starters()

def calculate_expected_score(home_team: str, away_team: str) -> tuple[float, float, dict]:
    home_info = TEAM_DATA.get(home_team, TEAM_DATA["阪神タイガース"])
    away_info = TEAM_DATA.get(away_team, TEAM_DATA["読売ジャイアンツ"])
    
    default_pitcher = {"name": "未定", "era": 3.30, "whip": 1.25, "throws": "R"}
    home_starter = TODAY_STARTERS.get(home_team, default_pitcher)
    away_starter = TODAY_STARTERS.get(away_team, default_pitcher)
    
    park_factor = home_info["park_factor"]

    home_offense_ops = home_info["ops_vs_left"] if away_starter["throws"] == "L" else home_info["ops_vs_right"]
    away_offense_ops = away_info["ops_vs_left"] if home_starter["throws"] == "L" else away_info["ops_vs_right"]

    home_pitching_era = (home_starter["era"] * 0.6) + (home_info["bullpen_era"] * home_info["bullpen_fatigue"] * 0.4)
    away_pitching_era = (away_starter["era"] * 0.6) + (away_info["bullpen_era"] * away_info["bullpen_fatigue"] * 0.4)

    # ホームアドバンテージを乗算
    home_exp = home_info["rpg"] * (home_offense_ops / LEAGUE_AVG_OPS) * (away_pitching_era / LEAGUE_AVG_ERA) * park_factor * HOME_ADVANTAGE
    away_exp = away_info["rpg"] * (away_offense_ops / LEAGUE_AVG_OPS) * (home_pitching_era / LEAGUE_AVG_ERA) * park_factor

    details = {
        "home_starter": home_starter,
        "away_starter": away_starter,
        "park_factor": park_factor,
        "home_bullpen_era": home_info["bullpen_era"],
        "away_bullpen_era": away_info["bullpen_era"],
        "home_bullpen_fatigue": home_info["bullpen_fatigue"],
        "away_bullpen_fatigue": away_info["bullpen_fatigue"]
    }

    return round(home_exp, 2), round(away_exp, 2), details
