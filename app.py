
import streamlit as st
import datetime
from simulation_engine import run_monte_carlo
from analytics_engine import calculate_expected_score
from report_engine import generate_note_report, generate_sns_post

ADMIN_PASSWORD = "1234"

ALL_NPB_TEAMS = [
	"阪神タイガース", "読売ジャイアンツ", "広島東洋カープ", 
	"横浜DeNAベイスターズ", "東京ヤクルトスワローズ", "中日ドラゴンズ",
	"福岡ソフトバンクホークス", "北海道日本ハムファイターズ", "千葉ロッテマリーンズ", 
	"オリックス・バファローズ", "東北楽天ゴールデンイーグルス", "埼玉西武ライオンズ"
]

HANDICAP_OPTIONS = ["0.3", "0.5", "0.7", "1", "1.3", "1.5", "1.7", "1半", "1半3", "1半5", "1半7", "2"]

def get_calibrated_star_rating(prob: float) -> str:
	if prob >= 65.0:
		return "★★★★★"
	elif prob >= 60.0:
		return "★★★★☆"
	elif prob >= 55.0:
		return "★★★☆☆"
	elif prob >= 50.0:
		return "★★☆☆☆"
	elif prob >= 45.0:
		return "★☆☆☆☆"
	else:
		return "☆☆☆☆☆"

st.set_page_config(
	page_title="⚾ MONTE CARLO KUN | NPB AI ANALYTICS",
	page_icon="⚾",
	layout="wide"
)

if "authenticated" not in st.session_state:
	st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
	st.title("🔒 MONTE CARLO KUN (管理者専用)")
	input_pass = st.text_input("パスワードを入力してください", type="password")
	if st.button("ログイン", type="primary"):
		if input_pass == ADMIN_PASSWORD:
			st.session_state["authenticated"] = True
			st.rerun()
		else:
			st.error("パスワードが正しくありません")
	st.stop()

st.title("⚾ MONTE CARLO KUN")
st.caption("NPB AI ANALYTICS — 10万回シミュレーション型 ハンデ解析ダッシュボード")

# 日付選択エリア
target_date = st.date_input("📅 対象日程を選択", datetime.date.today())
date_str = target_date.strftime("%Y-%m-%d")
date_jp_str = target_date.strftime("%Y年%m月%d日")

mode = st.radio("機能選択", ["1試合ごとの個別分析", "全試合一括解析（note・SNS自動生成）"], horizontal=True)
st.markdown("---")

if mode == "1試合ごとの個別分析":
	st.subheader(f"⚙️ 単発試合分析 ({date_jp_str})")
	col1, col2, col3, col4 = st.columns([2, 1.5, 1, 2])
	with col1:
		home_team = st.selectbox("ホームチーム", ALL_NPB_TEAMS, index=0, key="single_home")
	with col2:
		give_side = st.selectbox("出し側", ["ホーム出し", "ビジター出し"], key="single_give")
	with col3:
		handicap = st.selectbox("ハンデ", HANDICAP_OPTIONS, index=3, key="single_handi")
	with col4:
		away_team = st.selectbox("ビジターチーム", ALL_NPB_TEAMS, index=6, key="single_away")

	actual_handicap = handicap if give_side == "ホーム出し" else f"-{handicap}"

	if st.button("🚀 AI分析実行", use_container_width=True, type="primary"):
		home_exp, away_exp, details = calculate_expected_score(home_team, away_team, date_str)
		with st.spinner(f"{date_jp_str} の予告先発を読み込み、100,000試合のシミュレーションを実行中..."):
			home_prob, push_prob, away_prob, fig = run_monte_carlo(home_exp, away_exp, actual_handicap)
        
		home_stars = get_calibrated_star_rating(home_prob)
		away_stars = get_calibrated_star_rating(away_prob)

		st.subheader("📊 ハンデ込みAI分析結果")
		res_col1, res_col2, res_col3 = st.columns(3)
		with res_col1:
			st.metric(label=f"{home_team}（{'出し' if give_side == 'ホーム出し' else '貰い'}）", value=f"{home_prob}%", delta=home_stars)
		with res_col2:
			st.metric(label="勝負なし", value=f"{push_prob}%")
		with res_col3:
			st.metric(label=f"{away_team}（{'貰い' if give_side == 'ホーム出し' else '出し'}）", value=f"{away_prob}%", delta=away_stars)

		st.plotly_chart(fig, use_container_width=True)

		note_text = f"【{date_jp_str} NPB AI分析】\n" + generate_note_report(
			home_team, away_team, actual_handicap,
			home_prob, push_prob, away_prob,
			home_stars, away_stars, home_exp, away_exp, details
		)
		sns_text = f"【{date_jp_str}】 " + generate_sns_post(home_team, away_team, actual_handicap, home_prob, push_prob, away_prob, home_stars, away_stars)

		tab1, tab2 = st.tabs(["📄 note用分析レポート", "📱 X / Threads用投稿文"])
		with tab1:
			st.text_area("そのままコピーしてnoteへ", value=note_text, height=300)
		with tab2:
			st.text_area("そのままコピーしてSNSへ", value=sns_text, height=180)

else:
	st.subheader(f"⚙️ NPBカード 一括設定 ({date_jp_str})")
	st.caption("対戦カードと「どちらが出しているか」を指定して「一括解析」を押してください。")

	num_games = st.number_input("本日の試合数", min_value=1, max_value=6, value=6, step=1)
    
	games_input = []
	for i in range(int(num_games)):
		st.markdown(f"**第 {i+1} 試合**")
		g_col1, g_col2, g_col3, g_col4 = st.columns([2, 1.5, 1, 2])
		with g_col1:
			h_team = st.selectbox(f"ホーム #{i+1}", ALL_NPB_TEAMS, index=i % 12, key=f"bulk_h_{i}")
		with g_col2:
			g_side = st.selectbox(f"出し側 #{i+1}", ["ホーム出し", "ビジター出し"], key=f"bulk_give_{i}")
		with g_col3:
			h_handi = st.selectbox(f"ハンデ #{i+1}", HANDICAP_OPTIONS, index=3, key=f"bulk_handi_{i}")
		with g_col4:
			a_team = st.selectbox(f"ビジター #{i+1}", ALL_NPB_TEAMS, index=(i + 6) % 12, key=f"bulk_a_{i}")
        
		act_h = h_handi if g_side == "ホーム出し" else f"-{h_handi}"
		games_input.append((h_team, act_h, a_team, g_side, h_handi))

	if st.button("🔥 全試合一括AI解析 ＆ note記事生成", use_container_width=True, type="primary"):
		all_results = []
		star3_or_more = []
        
		progress_bar = st.progress(0)
		for idx, (h_team, act_h, a_team, g_side, raw_h) in enumerate(games_input):
			h_exp, a_exp, details = calculate_expected_score(h_team, a_team, date_str)
			h_prob, p_prob, a_prob, _ = run_monte_carlo(h_exp, a_exp, act_h)
            
			h_stars = get_calibrated_star_rating(h_prob)
			a_stars = get_calibrated_star_rating(a_prob)
            
			res_item = {
				"home": h_team, "away": a_team, "act_handicap": act_h, "g_side": g_side, "raw_h": raw_h,
				"home_prob": h_prob, "push_prob": p_prob, "away_prob": a_prob,
				"home_stars": h_stars, "away_stars": a_stars,
				"home_exp": h_exp, "away_exp": a_exp, "details": details
			}
			all_results.append(res_item)
            
			if "★★★" in h_stars or "★★★" in a_stars:
				star3_or_more.append(res_item)
                
			progress_bar.progress((idx + 1) / len(games_input))

		st.success(f"✅ {date_jp_str} 全試合の解析が完了しました！")
		st.markdown("---")

		# メンバーシップ用テキストの作成
		bulk_note_text = f"【{date_jp_str} NPB全試合 AIハンデ解析・モンテカルロ予想】\n\n"
		bulk_note_text += f"10万回のモンテカルロシミュレーションによる{date_jp_str}全試合の勝率・期待得点解析です。\n\n"
        
		for res in all_results:
			bulk_note_text += f"━━━━━━━━━━━━━━━━━━━━\n"
			bulk_note_text += f"⚾ {res['home']} vs {res['away']} (ハンデ: {res['g_side']} {res['raw_h']})\n"
			bulk_note_text += f"・{res['home']}側勝率: {res['home_prob']}% [{res['home_stars']}]\n"
			bulk_note_text += f"・{res['away']}側勝率: {res['away_prob']}% [{res['away_stars']}]\n"
			bulk_note_text += f"・勝負なし (Push): {res['push_prob']}%\n"
			bulk_note_text += f"・予測スコア: {res['home']} {res['home_exp']} - {res['away_exp']} {res['away']}\n"
			bulk_note_text += f"・予告先発: {res['details']['home_starter']['name']} vs {res['details']['away_starter']['name']}\n\n"

		# 星3以上限定テキストの作成
		star3_note_text = f"【{date_jp_str} 厳選おすすめ予想（星3以上対象カード）】\n\n"
		if star3_or_more:
			for res in star3_or_more:
				best_side = res['home'] if res['home_prob'] > res['away_prob'] else res['away']
				best_prob = max(res['home_prob'], res['away_prob'])
				best_stars = res['home_stars'] if res['home_prob'] > res['away_prob'] else res['away_stars']
                
				star3_note_text += f"🔥 厳選カード: {res['home']} vs {res['away']}\n"
				star3_note_text += f"・ハンデ設定: {res['g_side']} {res['raw_h']}\n"
				star3_note_text += f"・推奨サイド: {best_side} ({best_stars})\n"
				star3_note_text += f"・分析勝率: {best_prob}%\n"
				star3_note_text += f"・予告先発: {res['details']['home_starter']['name']} vs {res['details']['away_starter']['name']}\n\n"
		else:
			star3_note_text += "本日は星3以上の高信頼度カードはありませんでした。"

		tab_bulk, tab_star3 = st.tabs(["👑 メンバーシップ用 (全試合まとめ)", "💎 単発有料用 (星3以上厳選)"])
        
		with tab_bulk:
			st.text_area("メンバーシップ限定記事へそのままコピー", value=bulk_note_text, height=350)
            
		with tab_star3:
			st.text_area("単発有料記事へそのままコピー", value=star3_note_text, height=250)
