"""
NPB 日程 & 予告先発 リアルタイム自動取得エンジン
指定日の試合カードの有無と予告先発を解析します。
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

FALLBACK_STARTERS = {
    "阪神タイガース": {"name": "才木 浩人", "era": 1.83, "whip": 1.02, "throws": "R"},
    "読売ジャイアンツ": {"name": "戸郷 翔征", "era": 2.30, "whip": 1.08, "throws": "R"},
    "広島東洋カープ": {"name": "床田 寛樹", "era": 2.40, "whip": 1.10, "throws": "L"},
    "横浜DeNAベイスターズ": {"name": "東 克樹", "era": 2.10, "whip": 1.05, "throws": "L"},
    "東京ヤクルトスワローズ": {"name": "高橋 奎二", "era": 3.50, "whip": 1.25, "throws": "L"},
    "中日ドラゴンズ": {"name": "高橋 宏斗", "era": 1.38, "whip": 0.98, "throws": "R"},
    "福岡ソフトバンクホークス": {"name": "有原 航平", "era": 2.20, "whip": 1.05, "throws": "R"},
    "北海道日本ハムファイターズ": {"name": "伊藤 大海", "era": 2.60, "whip": 1.12, "throws": "R"},
    "千葉ロッテマリーンズ": {"name": "小島 和哉", "era": 3.20, "whip": 1.20, "throws": "L"},
    "オリックス・バファローズ": {"name": "宮城 大弥", "era": 2.30, "whip": 1.06, "throws": "L"},
    "東北楽天ゴールデンイーグルス": {"name": "早川 隆久", "era": 3.00, "whip": 1.15, "throws": "L"},
    "埼玉西武ライオンズ": {"name": "今井 達也", "era": 2.50, "whip": 1.10, "throws": "R"},
}

def fetch_schedule_and_starters(target_date_str: str = None) -> tuple[list, dict]:
    """
    指定日の試合カード一覧 [(ホーム, ビジター), ...] と 予告先発辞書 を返す
    """
    starters = {k: dict(v) for k, v in FALLBACK_STARTERS.items()}
    games = []

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
            
            # カードに含まれる球団を特定
            for short_name, full_name in TEAM_ALIAS.items():
                if short_name in text and full_name not in matched_teams:
                    matched_teams.append(full_name)

            # 対戦カード（2チーム）が検出された場合
            if len(matched_teams) >= 2:
                home = matched_teams[0]
                away = matched_teams[1]
                if (home, away) not in games:
                    games.append((home, away))

            # 予告先発名の抽出
            for short_name, full_name in TEAM_ALIAS.items():
                if short_name in text:
                    match = re.search(r"(?:予告先発|先発)[：:\s]*([一-龥ぁ-んァ-ヶa-zA-Z\s]{2,8})", text)
                    if match:
                        pitcher_name = match.group(1).strip()
                        if pitcher_name and len(pitcher_name) >= 2:
                            starters[full_name]["name"] = pitcher_name

        return games, starters

    except Exception:
        return games, starters
