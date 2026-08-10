import streamlit as st
import datetime
from simulation_engine import run_monte_carlo
from analytics_engine import calculate_expected_score
from scraper import fetch_schedule_and_starters
from report_engine import generate_note_report, generate_sns_post

ADMIN_PASSWORD = "1234"

ALL_NPB_TEAMS = [
    "阪神タイガース", "読売ジャイアンツ", "広島東洋カープ", 
    "横浜DeNAベイスターズ", "東京ヤクルトスワローズ", "中日ドラゴンズ",
    "福岡ソフトバンクホークス", "北海道日本ハムファイターズ", "千葉ロッテマリーンズ", 
    "オリックス・バファローズ", "東北楽天ゴールデンイーグルス", "埼玉西武ライオンズ"
]

HANDICAP_OPTIONS = ["0.3", "0.5", "0.7", "1", "1.3", "1.5", "1.7", "1半", "1半3", "1半5", "1半7", "2"]

# 試合が取得できなかった場合の自然なデフォルトカード
DEFAULT_MATCHUPS = [
    ("読売ジャイアンツ", "阪神タイガース"),
    ("横浜DeNAベイスターズ", "東京ヤクルトスワローズ"),
    ("広島東洋カープ", "中日ドラゴンズ"),
    ("福岡ソフトバンクホークス", "オリックス・バファローズ"),
    ("千葉ロッテマリーンズ", "東北楽天ゴールデンイーグルス"),
    ("北海道日本ハムファイターズ", "埼玉西武ライオンズ")
]

def get_calibrated_star_rating(prob: float) -> str:
    if prob >= 65.0: return "★★★★★"
    elif prob >= 60.0: return "★★★★☆"
    elif prob >= 55.0: return "★★★☆☆"
    elif prob >= 50.0: return "★★☆☆☆"
    elif prob >= 45.0: return "★☆☆☆☆"
    else: return "☆☆☆☆☆"

st.set_page_config(page_title="⚾ MONTE CARLO KUN", page_icon="⚾", layout="wide")

if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
if not st.session_state["authenticated"]:
    st.title("🔒 MONTE CARLO KUN (管理者専用)")
    if st.button("ログイン", type="primary") if (input_pass := st.text_input("パスワード", type="password")) == ADMIN_PASSWORD else (st.error("パスワードエラー") if input_pass else None):
        st.session_state["authenticated"] = True; st.rerun()
    st.stop()

st.title("⚾ MONTE CARLO KUN")
target_date = st.date_input("📅 対象日程を選択", datetime.date.today())
date_str = target_date.strftime("%Y-%m-%d")
date_jp_str = target_date.strftime("%Y年%m月%d日")

today_games, auto_starters = fetch_schedule_and_starters(date_str)
if not today_games:
    st.warning(f"⚠️ {date_jp_str} の試合情報がWeb上で確認できませんでした。手動で対戦カードと予想先発を設定してください。")

st.markdown("---")
st.subheader(f"⚙️ NPBカード 一括設定 ({date_jp_str})")

default_num_games = len(today_games) if today_games else 6
num_games = st.number_input("本日の試合数", min_value=1, max_value=6, value=default_num_games, step=1)

games_input = []
for i in range(int(num_games)):
    st.markdown(f"**第 {i+1} 試合**")
    
    # 取得できれば実際のカード、できなければ自然なカードをセット
    def_home = today_games[i][0] if i < len(today_games) else DEFAULT_MATCHUPS[i % 6][0]
    def_away = today_games[i][1] if i < len(today_games) else DEFAULT_MATCHUPS[i % 6][1]

    default_home_idx = ALL_NPB_TEAMS.index(def_home) if def_home in ALL_NPB_TEAMS else 0
    default_away_idx = ALL_NPB_TEAMS.index(def_away) if def_away in ALL_NPB_TEAMS else 6

    g_col1, g_col2, g_col3, g_col4 = st.columns([2, 1.5, 1, 2])
    with g_col1: h_team = st.selectbox(f"ホーム #{i+1}", ALL_NPB_TEAMS, index=default_home_idx, key=f"bulk_h_{i}")
    with g_col2: g_side = st.selectbox(f"出し側 #{i+1}", ["ホーム出し", "ビジター出し"], key=f"bulk_give_{i}")
    with g_col3: h_handi = st.selectbox(f"ハンデ #{i+1}", HANDICAP_OPTIONS, index=3, key=f"bulk_handi_{i}")
    with g_col4: a_team = st.selectbox(f"ビジター #{i+1}", ALL_NPB_TEAMS, index=default_away_idx, key=f"bulk_a_{i}")
    
    # ★新機能: 先発投手の自由入力枠（自動取得できれば初期値が入る）
    p_col1, p_col2 = st.columns(2)
    auto_h_pitcher = auto_starters.get(h_team, {}).get("name", "未定")
    auto_a_pitcher = auto_starters.get(a_team, {}).get("name", "未定")
    
    with p_col1: h_pitcher = st.text_input(f"⚾ {h_team}の先発 (手動編集可)", value=auto_h_pitcher, key=f"pitcher_h_{i}")
    with p_col2: a_pitcher = st.text_input(f"⚾ {a_team}の先発 (手動編集可)", value=auto_a_pitcher, key=f"pitcher_a_{i}")
    
    act_h = h_handi if g_side == "ホーム出し" else f"-{h_handi}"
    games_input.append((h_team, act_h, a_team, g_side, h_handi, h_pitcher, a_pitcher))

if st.button("🔥 全試合一括AI解析 ＆ note記事生成", use_container_width=True, type="primary"):
    all_results = []
    star3_or_more = []
    
    progress_bar = st.progress(0)
    for idx, (h_team, act_h, a_team, g_side, raw_h, h_pitcher, a_pitcher) in enumerate(games_input):
        with st.spinner(f"「{h_pitcher}」「{a_pitcher}」の最新成績を検索し、10万回シミュレーション中..."):
            h_exp, a_exp, details = calculate_expected_score(h_team, a_team, h_pitcher, a_pitcher)
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
            if "★★★" in h_stars or "★★★" in a_stars: star3_or_more.append(res_item)
            
        progress_bar.progress((idx + 1) / len(games_input))

    st.success(f"✅ {date_jp_str} 全試合の解析が完了しました！")
    
    bulk_note_text = f"【{date_jp_str} NPB全試合 AIハンデ解析・モンテカルロ予想】\n\n"
    for res in all_results:
        bulk_note_text += f"━━━━━━━━━━━━━━━━━━━━\n"
        bulk_note_text += f"⚾ {res['home']} vs {res['away']} (ハンデ: {res['g_side']} {res['raw_h']})\n"
        bulk_note_text += f"・{res['home']}側勝率: {res['home_prob']}% [{res['home_stars']}]\n"
        bulk_note_text += f"・{res['away']}側勝率: {res['away_prob']}% [{res['away_stars']}]\n"
        bulk_note_text += f"・勝負なし (Push): {res['push_prob']}%\n"
        bulk_note_text += f"・予測スコア: {res['home']} {res['home_exp']} - {res['away_exp']} {res['away']}\n"
        bulk_note_text += f"・予告先発(成績反映): {res['details']['home_starter']['name']} (防{res['details']['home_starter']['era']}) vs {res['details']['away_starter']['name']} (防{res['details']['away_starter']['era']})\n\n"

    tab_bulk, tab_star3 = st.tabs(["👑 メンバーシップ用 (全試合)", "💎 単発有料用 (星3以上)"])
    with tab_bulk: st.text_area("コピー用", value=bulk_note_text, height=350)
