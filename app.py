import streamlit as st
from simulation_engine import run_monte_carlo
from analytics_engine import calculate_expected_score
from report_engine import generate_note_report, generate_sns_post

# 管理者認証パスワード（必要に応じて変更可能）
ADMIN_PASSWORD = "1234"

ALL_NPB_TEAMS = [
    "阪神タイガース", "読売ジャイアンツ", "広島東洋カープ", 
    "横浜DeNAベイスターズ", "東京ヤクルトスワローズ", "中日ドラゴンズ",
    "福岡ソフトバンクホークス", "北海道日本ハムファイターズ", "千葉ロッテマリーンズ", 
    "オリックス・バファローズ", "東北楽天ゴールデンイーグルス", "埼玉西武ライオンズ"
]

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
    layout="centered"
)

# パスワード認証ゲート
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

# --- 以下、ログイン成功後の画面 ---

st.title("⚾ MONTE CARLO KUN")
st.caption("NPB AI ANALYTICS — 10万回シミュレーション型 ハンデ解析ダッシュボード")
st.markdown("---")

# 1. 条件入力エリア
st.subheader("⚙️ 分析条件設定")
col1, col2, col3 = st.columns([2, 1, 2])

with col1:
    home_team = st.selectbox("ホームチーム", ALL_NPB_TEAMS, index=0)

with col2:
    handicap_options = ["0.3", "0.5", "0.7", "1", "1.3", "1.5", "1.7", "1半", "1半3", "1半5", "1半7", "2"]
    handicap = st.selectbox("ハンデ（出し）", handicap_options, index=3)

with col3:
    away_team = st.selectbox("ビジターチーム", ALL_NPB_TEAMS, index=6)

analyze_btn = st.button("🚀 AI分析実行", use_container_width=True, type="primary")

st.markdown("---")

# 2. 分析結果表示
if analyze_btn:
    home_exp, away_exp, details = calculate_expected_score(home_team, away_team)
    
    with st.spinner("100,000試合のモンテカルロシミュレーションを実行中..."):
        home_prob, push_prob, away_prob, fig = run_monte_carlo(home_exp, away_exp, handicap)
    
    home_stars = get_calibrated_star_rating(home_prob)
    away_stars = get_calibrated_star_rating(away_prob)

    st.subheader("📊 ハンデ込みAI分析結果")
    
    res_col1, res_col2, res_col3 = st.columns(3)
    with res_col1:
        st.metric(label=f"{home_team}側（出し）", value=f"{home_prob}%", delta=home_stars)
    with res_col2:
        st.metric(label="勝負なし (Push)", value=f"{push_prob}%")
    with res_col3:
        st.metric(label=f"{away_team}側", value=f"{away_prob}%", delta=away_stars)
        
    st.markdown("---")
    
    col_score, col_chart = st.columns([1, 2])
    
    with col_score:
        st.markdown("### ⚾ AI予測スコア")
        st.subheader(f"{home_exp} - {away_exp}")
        st.caption(f"{home_team} vs {away_team}")
        st.write("")
        st.write("🔵 **青色**: 出し側勝ち")
        st.write("⚪ **灰色**: 勝負なし")
        st.write("🔴 **赤色**: 相手側勝ち")

    with col_chart:
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("🔍 採用モデル指標 & コンディション詳細", expanded=False):
        home_starter = details.get('home_starter', {})
        away_starter = details.get('away_starter', {})
        
        home_throws = "右" if home_starter.get('throws', 'R') == 'R' else "左"
        away_throws = "右" if away_starter.get('throws', 'R') == 'R' else "左"
        
        info_col1, info_col2 = st.columns(2)
        with info_col1:
            st.write(f"**{home_team} 先発:** {home_starter.get('name', '未定')} ({home_throws}投 / ERA {home_starter.get('era', 3.30)})")
            st.write(f"**救援防御率:** {details.get('home_bullpen_era', 2.50)} (疲労度: {details.get('home_bullpen_fatigue', 1.00)})")
            st.write(f"**球場補正 (PF):** {details.get('park_factor', 1.00)}")
        with info_col2:
            st.write(f"**{away_team} 先発:** {away_starter.get('name', '未定')} ({away_throws}投 / ERA {away_starter.get('era', 3.30)})")
            st.write(f"**救援防御率:** {details.get('away_bullpen_era', 2.50)} (疲労度: {details.get('away_bullpen_fatigue', 1.00)})")
            st.write(f"**試行回数:** 100,000 Sim")

    st.markdown("---")
    
    st.subheader("📝 レポート・SNS文面 自動生成")
    
    note_text = generate_note_report(
        home_team, away_team, handicap,
        home_prob, push_prob, away_prob,
        home_stars, away_stars,
        home_exp, away_exp, details
    )
    
    sns_text = generate_sns_post(
        home_team, away_team, handicap,
        home_prob, push_prob, away_prob,
        home_stars, away_stars
    )

    tab1, tab2 = st.tabs(["📄 note用分析レポート", "📱 X / Threads用投稿文"])
    
    with tab1:
        st.text_area("そのままコピーしてnoteに貼り付けられます", value=note_text, height=320)
    
    with tab2:
        st.text_area("そのままコピーしてSNSに投稿できます", value=sns_text, height=180)