"""
レポート自動生成エンジン (Report Engine - 免責文更新版)
"""

def generate_note_report(
	home_team: str, away_team: str, handicap: str,
	home_prob: float, push_prob: float, away_prob: float,
	home_stars: str, away_stars: str,
	home_exp: float, away_exp: float, details: dict
) -> str:
	"""
	note用分析レポート本文の自動生成（シンプル＆クリーン版）
	"""
	home_starter = details.get('home_starter', {})
	away_starter = details.get('away_starter', {})
    
	home_throws = "右" if home_starter.get('throws', 'R') == 'R' else "左"
	away_throws = "右" if away_starter.get('throws', 'R') == 'R' else "左"

	# 10万回シミュレーション上の優勢判定
	if home_prob > away_prob and home_prob > push_prob:
		winner_summary = f"【{home_team}】（ハンデ {handicap} を考慮しても優勢）"
		winner_stars = home_stars
		winner_prob = home_prob
	elif away_prob > home_prob and away_prob > push_prob:
		winner_summary = f"【{away_team}】（ハンデをもらっている側が優勢）"
		winner_stars = away_stars
		winner_prob = away_prob
	else:
		winner_summary = "【五分五分】（勝負なし・接戦ゾーン）"
		winner_stars = "☆☆☆☆☆"
		winner_prob = push_prob

	report = f"""【NPB AI分析】{home_team} vs {away_team}（ハンデ {handicap}）分析レポート

こんにちは、モンテカルロ君です。
「{home_team} vs {away_team}」の10万回シミュレーション結果をお届けします。

========================================
🏆 AI分析の結論：ハンデ込みでどちらが優勢？
👉 優勢：{winner_summary}
👉 優勢確率：{winner_prob}%（信頼度：{winner_stars}）
========================================

■ 10万回シミュレーション確率の内訳
・{home_team}側（出し）：{home_prob}%（{home_stars}）
・勝負なし（引き分け）：{push_prob}%
・{away_team}側（受け）：{away_prob}%（{away_stars}）

---

■ AI予測平均スコア
{home_team} {home_exp} - {away_exp} {away_team}

■ 先発投手・コンディションデータ
・{home_team}先発: {home_starter.get('name', '未定')}（{home_throws}投 / 防御率 {home_starter.get('era', 3.30)}）
・{away_team}先発: {away_starter.get('name', '未定')}（{away_throws}投 / 防御率 {away_starter.get('era', 3.30)}）
・球場補正: {details.get('park_factor', 1.00)}

■ 分析のまとめ
両チームの打撃成績、先発投手の左右相性、救援陣の状況を加味して10万試合を試行した結果、ハンデ条件「{handicap}」においては **{winner_summary}** の確率が最も高くなりました。

※本レポートは統計データおよび確率モデルに基づく分析結果であり、試合結果を保証するものではありません。参考データとしてご自身の責任においてご活用ください。
"""
	return report


def generate_sns_post(
	home_team: str, away_team: str, handicap: str,
	home_prob: float, push_prob: float, away_prob: float,
	home_stars: str, away_stars: str
) -> str:
	"""
	X / Threads 投稿用ショートテキスト
	"""
	if home_prob > away_prob and home_prob > push_prob:
		top_side = f"{home_team}優勢"
	elif away_prob > home_prob and away_prob > push_prob:
		top_side = f"{away_team}優勢"
	else:
		top_side = "拮抗"

	post = f"""⚾ モンテカルロ君 AI分析速報

【カード】{home_team} vs {away_team} (ハンデ {handicap})

📊 10万回シミュレーション結果
結論: {top_side}
・{home_team}側: {home_prob}% {home_stars}
・勝負なし: {push_prob}%
・{away_team}側: {away_prob}% {away_stars}

詳細分析はnoteで公開中！
#NPB #野球分析 #データ野球 #モンテカルロ君
"""
	return post

