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
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                
                # 各試合カードブロックごとに処理
                match_blocks = soup.select(".bb-matchTable__item, section.bb-scoreTable, .bb-headToHeadTable")
                for block in match_blocks:
                    # ブロック内のチーム名を抽出（順番保持）
                    team_elements = block.select(".bb-matchTable__team, .bb-headToHeadTable__team, a")
                    block_teams = []
                    for el in team_elements:
                        t_text = el.get_text(strip=True)
                        for short, full in TEAM_ALIAS.items():
                            if short in t_text and full not in block_teams:
                                block_teams.append(full)
                    
                    # ちょうど2チーム（対戦カード）が判定できた場合のみ登録
                    if len(block_teams) == 2:
                        game_pair = (block_teams[0], block_teams[1])
                        if game_pair not in games:
                            games.append(game_pair)
                    
                    # 予告先発投手の抽出（「予告先発：〇〇」または「先発：〇〇」）
                    block_text = block.get_text()
                    pitcher_matches = re.findall(r"(?:予告先発|先発|投手)[：:\s]*([一-龥ぁ-んァ-ヶa-zA-Z]{2,8})", block_text)
                    for p_name in pitcher_matches:
                        # チーム名（例: 阪神、巨人）を投手名として誤検知するのを排除
                        if p_name not in TEAM_ALIAS and p_name not in ["予告先発", "先発", "投手", "未定"]:
                            for full in block_teams:
                                if full not in starters:
                                    starters[full] = {"name": p_name}

            schedule_db[date_str] = {"games": games, "starters": starters}
            print(f"Result {date_str}: {len(games)} games, {len(starters)} starters.")
            time.sleep(1)
        except Exception as e:
            print(f"Error fetching schedule for {date_str}: {e}")

    with open("schedule_db.json", "w", encoding="utf-8") as f:
        json.dump(schedule_db, f, ensure_ascii=False, indent=4)
    print("schedule_db.json completely updated!")

if __name__ == "__main__":
    fetch_all()