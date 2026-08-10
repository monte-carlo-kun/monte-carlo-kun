import requests
from bs4 import BeautifulSoup
import json
import time
import os

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Yahooスポーツの各球団ID
TEAM_IDS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 376]

def fetch_all_pitchers():
    pitcher_db = {}
    
    for team_id in TEAM_IDS:
        url = f"https://baseball.yahoo.co.jp/npb/teams/{team_id}/memberlist?type=p"
        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
            if res.status_code != 200:
                print(f"Failed to fetch team {team_id}")
                continue
                
            soup = BeautifulSoup(res.text, "html.parser")
            
            # 選手一覧のテーブル行を取得
            rows = soup.select(".bb-playerTable__row")
            for row in rows:
                name_td = row.select_one(".bb-playerTable__data--player a")
                era_td = row.select_one(".bb-playerTable__data--era")
                throws_td = row.select_one("td:nth-of-type(4)") # 投打の列（大体4番目）

                if name_td and era_td:
                    name = name_td.get_text(strip=True).replace(" ", "").replace(" ", "")
                    era_str = era_td.get_text(strip=True)
                    
                    # 防御率が "-" などの場合は 3.50 をデフォルトにする
                    try:
                        era = float(era_str)
                    except ValueError:
                        era = 3.50
                        
                    throws = "L" if throws_td and "左投" in throws_td.get_text(strip=True) else "R"
                    
                    pitcher_db[name] = {
                        "era": era,
                        "throws": throws,
                        "whip": 1.25 # 固定（必要なら後で拡張可能）
                    }
            
            print(f"Team {team_id} updated. ({len(pitcher_db)} pitchers total)")
            time.sleep(2) # サーバーに負荷をかけないよう2秒待機
            
        except Exception as e:
            print(f"Error processing team {team_id}: {e}")

    # 取得したデータをJSONとして保存
    with open("pitcher_db.json", "w", encoding="utf-8") as f:
        json.dump(pitcher_db, f, ensure_ascii=False, indent=4)
    print("✅ pitcher_db.json successfully updated!")

if __name__ == "__main__":
    fetch_all_pitchers()
