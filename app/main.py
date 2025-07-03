import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils import load_data, append_row, calc_scores, admin_gate, THEMES, THEME_QUESTIONS, COMMON_QUESTIONS, ALL_COLUMNS
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="チェックシートアプリ", layout="wide")

# --- テーマ定義（solutionキーに変更） ---
THEME_INFO = {
    "①": {
        "label": "売上・利益の予測精度を高める",
        "problem": "着地見通しが担当者の経験や勘に頼っており、精度にばらつきがある",
        "solution": "業績の着地予測を属人化せず、誰でも高精度に把握できる“未来予報システム”を実現する",
        "approach": "過去の月次データを活用し、売上や利益の未来値を自動で計算・表示する機能を構築する"
    },
    "②": {
        "label": "月中でも業績の着地を把握する",
        "problem": "月末を迎えるまで売上・費用・利益がどの程度か分からない",
        "solution": "決算を待たずに“今月の見込み”を先読みできるリアルタイム可視化を実現する",
        "approach": "日々の速報値や累積情報から今月の着地を自動予測し、月中でも先手の経営判断を可能にする"
    },
    "③": {
        "label": "見えにくい赤字先をあぶり出す",
        "problem": "製品や顧客ごとの収益性が感覚に頼っており、対策が後手になりやすい",
        "solution": "隠れ赤字の商品・顧客を自動で発見し、早期に対策を打てる状態をつくる",
        "approach": "売上・粗利・費用の構成を分析し、損を生んでいる要因を可視化・警告する"
    },
    "⑥": {
        "label": "異常な費用増加をすぐに察知する",
        "problem": "毎月の費用がどこで大きく変わったのか報告書からでは分かりにくい",
        "solution": "いつもと違う費用の動きを自動で検出し、事前にアラートを出せる仕組みをつくる",
        "approach": "月次費用を過去の傾向と比べ、異常な変化をリアルタイムで検知・通知する"
    },
    "⑧": {
        "label": "予算と実績のズレを説明する",
        "problem": "予実差の原因が分かりにくく、説明に時間がかかる",
        "solution": "ズレの原因を自動で分解し、即答できる説明アシスタント機能を実現する",
        "approach": "予算と実績との差分を項目別に分解・可視化し、因果関係を数値で示す"
    },
    "⑨": {
        "label": "現場KPIと利益の関係を見える化",
        "problem": "現場の改善活動が利益にどう影響するかが曖昧で説明しづらい",
        "solution": "改善活動が財務に与える効果を誰でも理解できる形で示す",
        "approach": "稼働率や不良率と利益データを結びつけ、改善効果を数値化・可視化する"
    },
    "⑩": {
        "label": "中期経営計画の実現性を評価する",
        "problem": "目標値の実現可能性が直感に頼られており根拠が弱い",
        "solution": "過去実績を基に目標達成確率を定量試算し、根拠ある計画策定を支援する",
        "approach": "実績データと現状トレンドを組み合わせて、達成見込みを自動算出する"
    }
}

THEME_ORDER = ["①","②","③","⑥","⑧","⑨","⑩"]
THEME_LABELS = [f"{t} {THEME_INFO[t]['label']}" for t in THEME_ORDER]

# --- ページ遷移 ---
if 'page' not in st.session_state:
    st.session_state['page'] = 0

def go_page(idx):
    st.session_state['page'] = idx
    st.experimental_rerun()

# --- P0: 開始 ---
def page_0():
    st.markdown("""
    # チェックシート診断へようこそ
    所要時間 3 分・全 20 問・回答は匿名可
    """)
    if st.button("アンケート開始", key="start_btn"):
        go_page(1)

# --- P1: 質問（共通+困りごと） ---
def page_1():
    st.header("全20問 一括回答")
    st.markdown("**ユーザー情報**（任意）")
    st.text_input("名前", key="user_name")
    st.text_input("所属", key="user_affil")
    st.markdown("---")
    st.subheader("共通質問 (6問)")
    for i, q in enumerate(COMMON_QUESTIONS):
        cols = st.columns([3,2])
        with cols[0]:
            st.markdown(f"<div style='margin-bottom:0.2em'><b>{COMMON_QUESTIONS_TEXT[i]}</b></div>", unsafe_allow_html=True)
        with cols[1]:
            st.radio("", options=CHOICES, key=q, horizontal=True, label_visibility="collapsed")
    st.markdown("---")
    st.subheader("困りごとチェック (14問/テーマ名は伏せて出題)")
    for i, (qid, qtext) in enumerate(THEME_SIGNAL_QUESTIONS):
        cols = st.columns([3,2])
        with cols[0]:
            st.markdown(f"<div style='margin-bottom:0.2em'>{qtext}</div>", unsafe_allow_html=True)
        with cols[1]:
            st.radio("", options=CHOICES_SIGNAL, key=THEME_SIGNAL_KEYS[i], horizontal=True, label_visibility="collapsed")
    # バリデーション
    all_common = all(st.session_state.get(q) for q in COMMON_QUESTIONS)
    all_signal = all(st.session_state.get(k) for k in THEME_SIGNAL_KEYS)
    if st.button("診断結果を見る", key="to_result"):
        if all_common and all_signal:
            # 回答保存
            st.session_state['answers'] = {
                'user_name': st.session_state.user_name,
                'user_affil': st.session_state.user_affil
            }
            for q in COMMON_QUESTIONS:
                st.session_state['answers'][q] = CHOICE_MAP[st.session_state[q]]
            for i, k in enumerate(THEME_SIGNAL_KEYS):
                st.session_state['answers'][k] = CHOICE_MAP_SIGNAL[st.session_state[k]]
            # ここでレコード追加
            append_row(st.session_state['answers'])
            go_page(2)
        else:
            st.warning("全ての質問に回答してください")


# --- P2: 診断結果＋ダッシュボード ---
def page_2():
    st.header("診断結果・組織ダッシュボード")

    df = load_data()
    row = st.session_state.get('answers', {})

    # --- 個人診断表示部分（未回答時はスキップ） ---
    if row and all(q in row for q in COMMON_QUESTIONS + THEME_SIGNAL_KEYS):
        common_score = sum(row[q] for q in COMMON_QUESTIONS) / len(COMMON_QUESTIONS)
        theme_scores = {
            t: 0.4 * common_score + 0.6 * ((row[f"{t}_Q1"] + row[f"{t}_Q2"]) / 2)
            for t in THEME_ORDER
        }
        top = max(theme_scores, key=theme_scores.get)
        info = THEME_INFO[top]

        st.markdown("### あなたの診断結果")
        # テーマ概要カード
        st.markdown(f"""
        **選定テーマ**：{info['label']}
        - **問題**：{info['problem']}
        - **解決策**：{info['solution']}
        - **アプローチ**：{info['approach']}
        """)

        # 縦棒グラフ（縦軸=スコア、横軸=テーマ）
        bar = px.bar(
            x=[theme_scores[t] for t in THEME_ORDER],
            y=THEME_LABELS,
            orientation="h",
            labels={"x":"スコア","y":"テーマ"},
            range_x=[0,100]
        )
        st.plotly_chart(bar, use_container_width=True)

        # レーダーチャート
        radar_df = pd.DataFrame({
            "スコア": [theme_scores[t] for t in THEME_ORDER] + [theme_scores[THEME_ORDER[0]]],
            "テーマ": THEME_LABELS + [THEME_LABELS[0]]
        })
        radar = px.line_polar(radar_df, r="スコア", theta="テーマ",
                              line_close=True, range_r=[0,100], markers=True)
        st.plotly_chart(radar, use_container_width=True)

        if st.button("この内容で保存"):
            append_row(row)
            st.success("回答を保存しました")
    else:
        st.warning("個人診断は未回答のためスキップします。")

    st.markdown("---")

    # --- 組織ダッシュボード部分（常に表示） ---
    st.subheader("組織ダッシュボード")

    # 全回答者数
    count = len(df)
    st.markdown(f"- **回答者数**：{count} 名")

    # テーマごとの散布図：横軸=テーマ、縦軸=スコア
    scatter_df = []
    for t in THEME_ORDER:
        for idx in df.index:
            avg = (df.at[idx, f"{t}_Q1"] + df.at[idx, f"{t}_Q2"]) / 2
            scatter_df.append({"テーマ": THEME_INFO[t]["label"], "スコア": avg})
    scatter_df = pd.DataFrame(scatter_df)
    scatter = px.strip(scatter_df, x="テーマ", y="スコア",
                       labels={"スコア":"スコア", "テーマ":"テーマ"})
    st.plotly_chart(scatter, use_container_width=True)

    # 最新データ再読込ボタン
    if st.button("最新データで更新"):
        st.experimental_rerun()

    if st.button("アンケートに戻る"):
        go_page(1)

# --- ページ描画 ---
pages = [None, None, page_2, None]  # P0,P1,P2,P3,P5 と対応
pages[st.session_state['page']]()

# --- サイドバー ---
st.sidebar.title("ページ移動")
page_names = ["アンケート開始", "質問入力", "診断・ダッシュボード", "管理者"]
for i, p in enumerate(page_names):
    if st.sidebar.button(p, key=f"side_{i}"):
        go_page(i)
        st.rerun()
