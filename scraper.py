import json
import os
import requests
from bs4 import BeautifulSoup
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

TEAM_ALIAS = {
    "阪神": "阪神タイガース", "巨人": "読売ジャイアンツ", "広島": "広島東洋カープ",
    "DeNA": "横浜DeNAベイスターズ", "ヤクルト": "東京ヤクルトスワローズ", "中日": "中日ドラゴンズ",
    "ソフトバンク": "福岡ソフトバンクホークス", "日本ハム": "北海道日本ハムファイターズ",
    "ロッテ": "千葉ロッテマリーンズ", "オリックス": "オリックス・バファローズ",
    "楽天": "東北楽天ゴールデンイーグルス", "西武": "埼玉西武ライオンズ"
}

def fetch_schedule_and_starters(target_date_str: str = None) -> tuple[list, dict]:
    # ロボットが自動生成したデータベースから一瞬で読み込む
    db_path = "schedule_db.json"
    if target_date_str and os.path.exists(db_path):
        try:
            with open(db_path, "r", encoding="utf-8") as f:
                schedule_db = json.load(f)
            if target_date_str in schedule_db:
                data = schedule_db[target_date_str]
                games = [tuple(g) for g in data["games"]]
                starters = data["starters"]
                return games, starters
        except Exception as e:
            print(f"Schedule DB load error: {e}")

    # 万が一DBがなかった時だけWebを見に行く（フォールバック）
    games = []
    starters = {}
    try:
        url = f"https://baseball.yahoo.co.jp/npb/schedule/?date={target_date_str}" if target_date_str else "https://baseball.yahoo.co.jp/npb/schedule/"
        res = requests.get(url, headers=HEADERS, timeout=5)
        if res.status_code != 200: return games, starters

        soup = BeautifulSoup(res.text, "html.parser")
        for card in soup.select(".bb-matchTable__item, .bb-scoreTable, .bb-headToHeadTable"):
            text = card.get_text()
            matched_teams = [full for short, full in TEAM_ALIAS.items() if short in text]
            matched_unique = list(dict.fromkeys(matched_teams))
            if len(matched_unique) >= 2:
                if (matched_unique[0], matched_unique[1]) not in games:
                    games.append((matched_unique[0], matched_unique[1]))

            for short, full in TEAM_ALIAS.items():
                if short in text:
                    match = re.search(r"(?:予告先発|先発)[：:\s]*([一-龥ぁ-んァ-ヶa-zA-Z\s]{2,8})", text)
                    if match and len(match.group(1).strip()) >= 2:
                        starters[full] = {"name": match.group(1).strip()}
        return games, starters
    except Exception:
        return games, starters

def fetch_pitcher_stats_online(pitcher_name: str) -> dict:
    fallback = {"name": pitcher_name, "era": 3.30, "whip": 1.25, "throws": "R"}
    if not pitcher_name or pitcher_name == "未定": return fallback
    
    clean_name = pitcher_name.replace(" ", "").replace(" ", "")
    db_path = "pitcher_db.json"
    
    if os.path.exists(db_path):
        try:
            with open(db_path, "r", encoding="utf-8") as f:
                pitcher_db = json.load(f)
            for key, data in pitcher_db.items():
                if key in clean_name or clean_name in key:
                    return {
                        "name": pitcher_name,
                        "era": data["era"],
                        "whip": data["whip"],
                        "throws": data["throws"]
                    }
        except Exception as e:
            print(f"DB load error: {e}")
            
    return fallback