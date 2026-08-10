"""
バックテスト実行エンジン (Backtest Engine - Phase 8 閾値調整版)
ハンデ戦の基準確率（ベースライン）からの乖離率（優位度）に基づき★評価を動的判定します。
"""

import numpy as np
from analytics_engine import calculate_expected_score
from simulation_engine import run_monte_carlo
from handicap_engine import evaluate_handicap_single_game

def get_calibrated_star_rating(prob: float, base_prob: float = 40.0) -> str:
    """
    ハンデ戦用 ★評価ロジック
    基準確率(base_prob: 約40%)からの上振れ幅（優位度）で★を決定
    """
    diff = prob - base_prob
    if diff >= 20.0:     # 60.0%以上
        return "★★★★★"
    elif diff >= 15.0:   # 55.0%以上
        return "★★★★☆"
    elif diff >= 10.0:   # 50.0%以上
        return "★★★☆☆"
    elif diff >= 5.0:    # 45.0%以上
        return "★★☆☆☆"
    elif diff >= 0.0:    # 40.0%以上
        return "★☆☆☆☆"
    else:
        return "☆☆☆☆☆"

HISTORICAL_GAMES = [
    {"home": "阪神タイガース", "away": "読売ジャイアンツ", "handicap": "1", "actual_home": 5, "actual_away": 3},
    {"home": "阪神タイガース", "away": "読売ジャイアンツ", "handicap": "1", "actual_home": 4, "actual_away": 3},
    {"home": "横浜DeNAベイスターズ", "away": "中日ドラゴンズ", "handicap": "0.5", "actual_home": 2, "actual_away": 3},
    {"home": "読売ジャイアンツ", "away": "広島東洋カープ", "handicap": "1.5", "actual_home": 4, "actual_away": 2},
    {"home": "東京ヤクルトスワローズ", "away": "阪神タイガース", "handicap": "0.7", "actual_home": 1, "actual_away": 1},
    {"home": "中日ドラゴンズ", "away": "横浜DeNAベイスターズ", "handicap": "1", "actual_home": 3, "actual_away": 1},
    {"home": "広島東洋カープ", "away": "東京ヤクルトスワローズ", "handicap": "0.5", "actual_home": 4, "actual_away": 1},
    {"home": "阪神タイガース", "away": "横浜DeNAベイスターズ", "handicap": "1.3", "actual_home": 2, "actual_away": 3},
    {"home": "読売ジャイアンツ", "away": "中日ドラゴンズ", "handicap": "1半", "actual_home": 3, "actual_away": 2},
    {"home": "横浜DeNAベイスターズ", "away": "東京ヤクルトスワローズ", "handicap": "0.3", "actual_home": 6, "actual_away": 4},
]

def run_backtest():
    print("========================================")
    print("⚾ モンテカルロ君 バックテスト(Phase 8) 実行中...")
    print("========================================\n")

    star_results = {}

    for i, game in enumerate(HISTORICAL_GAMES, 1):
        home = game["home"]
        away = game["away"]
        h_cap = game["handicap"]
        act_home = game["actual_home"]
        act_away = game["actual_away"]

        home_exp, away_exp, _ = calculate_expected_score(home, away)
        home_prob, push_prob, away_prob = run_monte_carlo(home_exp, away_exp, h_cap, num_simulations=100000)

        # 実際のハンデ判定結果
        diff = act_home - act_away
        hw, pw, aw = evaluate_handicap_single_game(diff, h_cap)

        if hw > aw and hw > pw:
            actual_outcome = "home"
        elif aw > hw and aw > pw:
            actual_outcome = "away"
        else:
            actual_outcome = "push"

        # 最高確率の選択肢
        probs = {"home": home_prob, "push": push_prob, "away": away_prob}
        pred_outcome = max(probs, key=probs.get)
        pred_prob = probs[pred_outcome]

        # ハンデ戦用補正★評価
        stars = get_calibrated_star_rating(pred_prob)

        if stars not in star_results:
            star_results[stars] = {"total": 0, "correct": 0}
        star_results[stars]["total"] += 1
        if pred_outcome == actual_outcome:
            star_results[stars]["correct"] += 1

        print(f"試合 {i}: {home} vs {away} (ハンデ {h_cap})")
        print(f"  予測確率: 出し {home_prob}% | 勝負なし {push_prob}% | 相手 {away_prob}%")
        print(f"  判定評価: {stars} | 予測: {pred_outcome} | 実測: {actual_outcome} -> {'✅ 的中' if pred_outcome == actual_outcome else '❌ 不的中'}\n")

    print("========================================")
    print("📊 最適化後の★別的中実績")
    print("========================================")
    for star, data in sorted(star_results.items(), reverse=True):
        acc = (data["correct"] / data["total"]) * 100 if data["total"] > 0 else 0
        print(f"  {star}: {data['correct']}/{data['total']} 試合的中 ({acc:.1f}%)")

if __name__ == "__main__":
    run_backtest()
