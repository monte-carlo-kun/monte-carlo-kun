"""
NPB 日程 & 全投手リアルタイム成績取得エンジン
"""

import requests
from bs4 import BeautifulSoup
import re
import urllib.parse

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
			# 重複排除して2チーム以上あればカード追加
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
	"""入力された投手名をスポーツナビで検索し、防御率と左右を取得する"""
	fallback = {"name": pitcher_name, "era": 3.30, "whip": 1.25, "throws": "R"}
	if not pitcher_name or pitcher_name == "未定": return fallback

	try:
		encoded_name = urllib.parse.quote(pitcher_name)
		search_url = f"https://baseball.yahoo.co.jp/npb/search?p={encoded_name}"
		res = requests.get(search_url, headers=HEADERS, timeout=5)
		if res.status_code != 200: return fallback

		soup = BeautifulSoup(res.text, "html.parser")
		player_link = None
		for a in soup.select("a"):
			href = a.get("href", "")
			if "/npb/player/" in href:
				player_link = "https://baseball.yahoo.co.jp" + href if not href.startswith("http") else href
				break
                
		if not player_link: return fallback

		p_res = requests.get(player_link, headers=HEADERS, timeout=5)
		if p_res.status_code != 200: return fallback

		p_soup = BeautifulSoup(p_res.text, "html.parser")
		profile_text = p_soup.get_text()
        
		throws = "L" if "左投" in profile_text else "R"
		era = 3.30
        
		for th in p_soup.find_all("th"):
			if "防御率" in th.get_text():
				td = th.find_next_sibling("td")
				if td:
					try:
						era = float(td.get_text().strip())
					except ValueError:
						pass
				break
                
		return {"name": pitcher_name, "era": era, "whip": 1.25, "throws": throws}
	except Exception:
		return fallback

