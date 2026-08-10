
"""
NPB 日程 & 予告先発 リアルタイム自動取得エンジン
（ダミーデータを廃止し、実際に取得できた名前のみを返します）
"""

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
	games = []
	starters = {} # 取得できた場合のみ {"球団名": {"name": "投手名"}} を格納

	try:
		if target_date_str:
			url = f"https://baseball.yahoo.co.jp/npb/schedule/?date={target_date_str}"
		else:
			url = "https://baseball.yahoo.co.jp/npb/schedule/"
            
		response = requests.get(url, headers=HEADERS, timeout=5)
		if response.status_code != 200:
			return games, starters

		soup = BeautifulSoup(response.text, "html.parser")
		match_cards = soup.select(".bb-matchTable__item, .bb-scoreTable, .bb-headToHeadTable")

		for card in match_cards:
			text = card.get_text()
			matched_teams = []
            
			for short_name, full_name in TEAM_ALIAS.items():
				if short_name in text and full_name not in matched_teams:
					matched_teams.append(full_name)

			if len(matched_teams) >= 2:
				home = matched_teams[0]
				away = matched_teams[1]
				if (home, away) not in games:
					games.append((home, away))

			for short_name, full_name in TEAM_ALIAS.items():
				if short_name in text:
					# 予告先発名の抽出
					match = re.search(r"(?:予告先発|先発)[：:\s]*([一-龥ぁ-んァ-ヶa-zA-Z\s]{2,8})", text)
					if match:
						pitcher_name = match.group(1).strip()
						if pitcher_name and len(pitcher_name) >= 2:
							starters[full_name] = {"name": pitcher_name}

		return games, starters

	except Exception:
		return games, starters
