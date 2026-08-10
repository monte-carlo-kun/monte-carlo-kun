import numpy as np
import pandas as pd
import plotly.graph_objects as go
from handicap_engine import evaluate_handicap_single_game

def run_monte_carlo(home_expected: float, away_expected: float, handicap_str: str, num_simulations: int = 100000):
    """
    10万回シミュレーションを実行し、ハンデゾーン別3色カラー表示用Plotlyグラフを自動生成します。
    """
    home_scores = np.random.poisson(home_expected, num_simulations)
    away_scores = np.random.poisson(away_expected, num_simulations)

    diffs = home_scores - away_scores

    home_win_total = 0.0
    push_total = 0.0
    away_win_total = 0.0

    for diff in diffs:
        hw, pw, aw = evaluate_handicap_single_game(diff, handicap_str)
        home_win_total += hw
        push_total += pw
        away_win_total += aw

    home_win_prob = round((home_win_total / num_simulations) * 100, 1)
    push_prob = round((push_total / num_simulations) * 100, 1)
    away_win_prob = round((away_win_total / num_simulations) * 100, 1)

    clipped_diffs = np.clip(diffs, -6, 6)
    diff_counts = pd.Series(clipped_diffs).value_counts().sort_index()

    x_labels = []
    y_probs = []
    colors = []
    hover_texts = []

    for diff, count in diff_counts.items():
        hw, pw, aw = evaluate_handicap_single_game(diff, handicap_str)
        prob = round((count / num_simulations) * 100, 2)
        
        if diff == -6:
            label = "-6点以上"
        elif diff == 6:
            label = "+6点以上"
        else:
            label = f"{diff:+d}点"

        if hw > aw and hw > pw:
            color = "#1E88E5"
            zone_name = "出し側勝利ゾーン"
        elif aw > hw and aw > pw:
            color = "#E53935"
            zone_name = "相手側勝利ゾーン"
        else:
            color = "#757575"
            zone_name = "勝負なし・分割ゾーン"

        x_labels.append(label)
        y_probs.append(prob)
        colors.append(color)
        hover_texts.append(f"<b>得点差: {label}</b><br>発生確率: {prob}% ({count:,}試合)<br>判定: {zone_name}")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=x_labels,
        y=y_probs,
        marker_color=colors,
        hovertext=hover_texts,
        hoverinfo="text",
        text=[f"{p}%" if p >= 2.0 else "" for p in y_probs],
        textposition="auto"
    ))

    fig.update_layout(
        title=dict(text=f"100,000試合の得点差分布 (ハンデ {handicap_str} 判定ゾーン)", font=dict(size=14)),
        xaxis_title="試合結果（得点差）",
        yaxis_title="発生確率 (%)",
        margin=dict(l=20, r=20, t=40, b=20),
        height=320,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="#E0E0E0")
    )

    return home_win_prob, push_prob, away_win_prob, fig
