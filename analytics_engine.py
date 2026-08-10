"""
NPB分析・予測スコア算出エンジン (正確な先発反映 ＆ 投手DB版)
"""

from scraper import fetch_schedule_and_starters

LEAGUE_AVG_ERA = 3.30
LEAGUE_AVG_OPS = 0.700
HOME_ADVANTAGE = 1.03

TEAM_DATA = {
    "阪神タイガース": {"rpg": 3.8, "ops_vs_right": 0.710, "ops_vs_left": 0.670, "park_factor": 0.92, "bullpen_era": 2.20, "bullpen_fatigue": 1.05},
    "読売ジャイアンツ": {"rpg": 3.7, "ops_vs_right": 0.720, "ops_vs_left": 0.690, "park_factor": 1.08, "bullpen_era": 2.90, "bullpen_fatigue": 1.00},
    "広島東洋カープ": {"rpg": 3.4, "ops_vs_right": 0.670, "ops_vs_left": 0.650, "park_factor": 1.02, "bullpen_era": 3.10, "bullpen_fatigue": 0.95},
    "横浜DeNAベイスターズ": {"rpg": 4.1, "ops_vs_right": 0.730, "ops_vs_left": 0.710, "park_factor": 1.12, "bullpen_era": 3.40, "bullpen_fatigue": 1.10},
    "東京ヤクルトスワローズ": {"rpg": 3.9, "ops_vs_right": 0.700, "ops_vs_left": 0.720, "park_factor": 1.10, "bullpen_era": 3.80, "bullpen_fatigue": 1.00},
    "中日ドラゴンズ": {"rpg": 3.0, "ops_vs_right": 0.640, "ops_vs_left": 0.620, "park_factor": 0.85, "bullpen_era": 2.50, "bullpen_fatigue": 0.90},
    "福岡ソフトバンクホークス": {"rpg": 4.3, "ops_vs_right": 0.745, "ops_vs_left": 0.725, "park_factor": 1.05, "bullpen_era": 2.40, "bullpen_fatigue": 1.00},
    "北海道日本ハムファイターズ": {"rpg": 3.8, "ops_vs_right": 0.715, "ops_vs_left": 0.695, "park_factor": 1.00, "bullpen_era": 2.70, "bullpen_fatigue": 0.95},
    "千葉ロッテマリーンズ": {"rpg": 3.6, "ops_vs_right": 0.690, "ops_vs_left": 0.680, "park_factor": 0.95, "bullpen_era": 3.00, "bullpen_fatigue": 1.05},
    "オリックス・バファローズ": {"rpg": 3.5, "ops_vs_right": 0.685, "ops_vs_left": 0.670, "park_factor": 0.90, "bullpen_era": 2.80, "bullpen_fatigue": 1.00},
    "東北楽天ゴールデンイーグルス": {"rpg": 3.6, "ops_vs_right": 0.695, "ops_vs_left": 0.685, "park_factor": 1.00, "bullpen_era": 3.20, "bullpen_fatigue": 1.05},
    "埼玉西武ライオンズ": {"rpg": 3.1, "ops_vs_right": 0.640, "ops_vs_left": 0.630, "park_factor": 0.92, "bullpen_era": 3.30, "bullpen_fatigue": 1.10},
}

# 主要な先発投手の簡易データベース（ここにない投手はリーグ平均の3.30で計算）
PITCHER_DB = {
    "才木 浩人": {"era": 1.83, "whip": 1.02, "throws": "R"},
    "村上 頌樹": {"era": 2.58, "whip": 1.05, "throws": "R"},
    "大竹 耕太郎": {"era": 2.80, "whip": 1.15, "throws": "L"},
    "戸郷 翔征": {"era": 2.30, "whip": 1.08, "throws": "R"},
    "菅野 智之": {"era": 1.67, "whip": 0.95, "throws": "R"},
    "山﨑 伊織": {"era": 2.01, "whip": 1.00, "throws": "R"},
    "床田 寛樹": {"era": 2.40, "whip": 1.10, "throws": "L"},
    "森下 暢仁": {"era": 2.50, "whip": 1.12, "throws": "R"},
    "東 克樹": {"era": 2.10, "whip": 1.05, "throws": "L"},
    "高橋 奎二": {"era": 3.50, "whip": 1.25, "throws": "L"},
    "高橋 宏斗": {"era": 1.38, "whip": 0.98, "throws": "R"},
    "有原 航平": {"era": 2.20, "whip": 1.05, "throws": "R"},
    "モイネロ": {"era": 1.80, "whip": 0.95, "throws": "L"},
    "伊藤 大海": {"era": 2.60, "whip": 1.12, "throws": "R"},
    "小島 和哉": {"era": 3.20, "whip": 1.20, "throws": "L"},
    "佐々木 朗希": {"era": 2.10, "whip": 1.00, "throws": "R"},
    "宮城 大弥": {"era": 2.30, "whip": 1.06, "throws": "L"},
    "早川 隆久": {"era": 3.00, "whip": 1.15, "throws": "L"},
    "今井 達也": {"era": 2.50, "whip": 1.10, "throws": "R"},
}

def get_pitcher_data(pitcher_name: str) -> dict:
    """DBから投手成績を取得。未登録や未定の場合は平均値を返す"""
    if pitcher_name == "未定":
        return {"name": "未定", "era": LEAGUE_AVG_ERA, "whip": 1.25, "throws": "R"}
    
    # DBに完全一致するかチェック
    if pitcher_name in PITCHER_DB:
        return {"name": pitcher_name, **PITCHER_DB[pitcher_name]}
    
    # 苗字だけなどの部分一致チェック
    for db_name, stats in PITCHER_DB.items():
        if pitcher_name in db_name or db_name.replace(" ", "") in pitcher_name.replace(" ", ""):
            return {"name": pitcher_name, **stats}
            
    # DBに見つからなかった場合はリーグ平均を適用
    return {"name": pitcher_name, "era": LEAGUE_AVG_ERA, "whip": 1.25, "throws": "R"}

def calculate_expected_score(home_team: str, away_team: str, target_date_str: str = None) -> tuple[float, float, dict]:
    home_info = TEAM_DATA.get(home_team, TEAM_DATA["阪神タイガース"])
    away_info = TEAM_DATA.get(away_team, TEAM_DATA["読売ジャイアンツ"])
    
    _, starters = fetch_schedule_and_starters(target_date_str)
    
    # スクレイピングで取得できた名前（なければ"未定"）
    home_starter_name = starters.get(home_team, {}).get("name", "未定")
    away_starter_name = starters.get(away_team, {}).get("name", "未定")
    
    # DBと照合して成績を確定
    home_starter = get_pitcher_data(home_starter_name)
    away_starter = get_pitcher_data(away_starter_name)
    
    park_factor = home_info["park_factor"]

    home_offense_ops = home_info["ops_vs_left"] if away_starter["throws"] == "L" else home_info["ops_vs_right"]
    away_offense_ops = away_info["ops_vs_left"] if home_starter["throws"] == "L" else away_info["ops_vs_right"]

    home_pitching_era = (home_starter["era"] * 0.6) + (home_info["bullpen_era"] * home_info["bullpen_fatigue"] * 0.4)
    away_pitching_era = (away_starter["era"] * 0.6) + (away_info["bullpen_era"] * away_info["bullpen_fatigue"] * 0.4)

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
