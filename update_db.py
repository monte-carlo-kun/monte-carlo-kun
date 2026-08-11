import requests
from bs4 import BeautifulSoup
import json
import time
import datetime
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "ja,en-US;q=0.7,en;q=0.3"
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
    print("--- Fetching pitcher stats ---")
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
            time.sleep(0.5)
        except Exception as e:
            print(f"Error fetching team {team_id}: {e}")

    with open("pitcher_db.json", "w", encoding="utf-8") as f:
        json.dump(pitcher_db, f, ensure_ascii=False, indent=4)
    print("pitcher_db.json updated!")

    # 2. 試合日程・先発投手の取得
    print("--- Fetching schedules ---")
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
            print(f"Date: {date_str} | Status: {res.status_code} | Response Size: {len(res.text)}")
            
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                
                # HTML内のカード・行要素を広範囲に取得
                cards = soup.find_all(["section", "div", "li", "tr"])
                for card in cards:
                    text = card.get_text(separator=" ", strip=True)
                    
                    # チーム名の検出
                    matched_teams = []
                    for short, full in TEAM_ALIAS.items():
                        if short in text and full not in matched_teams:
                            matched_teams.append(full)
                    
                    # 2チーム検出されたら試合カードとして登録
                    if len(matched_teams) == 2:
                        game_pair = (matched_teams[0], matched_teams[1])
                        if game_pair not in games:
                            games.append(game_pair)
                    
                    # 予告先発・先発投手の抽出
                    match = re.search(r"(?:予告先発|先発|投手)[：:\s]*([一-龥ぁ-んァ-ヶa-zA-Z\s]{2,8})", text)
                    if match:
                        pitcher_name = match.group(1).strip()
                        for full in matched_teams:
                            if full not in starters and len(pitcher_name) >= 2:
                                starters[full] = {"name": pitcher_name}

            schedule_db[date_str] = {"games": games, "starters": starters}
            print(f" -> Result for {date_str}: {len(games)} games, {len(starters)} starters found.")
            time.sleep(1)
        except Exception as e:
            print(f"Error fetching schedule for {date_str}: {e}")

    with open("schedule_db.json", "w", encoding="utf-8") as f:
        json.dump(schedule_db, f, ensure_ascii=False, indent=4)
    print("schedule_db.json completely updated!")

if __name__ == "__main__":
    fetch_all()