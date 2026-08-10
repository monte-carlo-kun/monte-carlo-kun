import requests
from bs4 import BeautifulSoup
import json
import time
import datetime
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

def fetch_all():
    # 1. 投手成績データの取得
    TEAM_IDS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 376]
    pitcher_db = {}
    print("Fetching pitcher stats...")
    for team_id in TEAM_IDS:
        url = f"https://baseball.yahoo.co.jp/npb/teams/{team_id}/memberlist?type=p"
        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                for row in soup.select(".bb-playerTable__row"):
                    name_td = row.select_one(".bb-playerTable__data--player a")
                    era_td = row.select_one(".bb-playerTable__data--era")
                    throws_td = row.select_one("td:nth-of-type(4)")
                    if name_td and era_td:
                        name = name_td.get_text(strip=True).replace(" ", "").replace(" ", "")
                        era_str = era_td.get_text(strip=True)
                        try: era = float(era_str)
                        except ValueError: era = 3.50
                        throws = "L" if throws_td and "左投" in throws_td.get_text(strip=True) else "R"
                        pitcher_db[name] = {"era": era, "throws": throws, "whip": 1.25}
            time.sleep(1)
        except Exception as e:
            print(f"Error fetching team {team_id}: {e}")

    with open("pitcher_db.json", "w", encoding="utf-8") as f:
        json.dump(pitcher_db, f, ensure_ascii=False, indent=4)
    print("pitcher_db.json updated!")

    # 2. 試合日程・先発投手の取得（昨日〜明後日までの4日間分）
    print("Fetching schedules...")
    schedule_db = {}
    JST = datetime.timezone(datetime.timedelta(hours=9))
    today = datetime.datetime.now(JST).date()

    for i in range(-1, 3): 
        target_date = today + datetime.timedelta(days=i)
        date_str = target_date.strftime("%Y-%m-%d")
        games = []
        starters = {}
        url = f"https://baseball.yahoo.co.jp/npb/schedule/?date={date_str}"
        
        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
            if res.status_code == 200:
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
            
            schedule_db[date_str] = {"games": games, "starters": starters}
            time.sleep(1)
        except Exception as e:
            print(f"Error fetching schedule for {date_str}: {e}")

    with open("schedule_db.json", "w", encoding="utf-8") as f:
        json.dump(schedule_db, f, ensure_ascii=False, indent=4)
    print("schedule_db.json updated!")

if __name__ == "__main__":
    fetch_all()