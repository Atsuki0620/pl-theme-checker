import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils import load_data, append_row, admin_gate, COMMON_QUESTIONS, THEME_SIGNAL_KEYS
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="チェックシートアプリ", layout="wide")

# --- テーマ定義（solutionキーを使用） ---
THEME_INFO = {
    "①": {
        "label": "売上・利益の予測精度を高める",
        "problem": "着地見通しが担当者の勘に頼り、精度にばらつきがある",
        "solution": "誰でも安定した予測が得られる「未来予報システム」を構築する",
        "approach": "過去の月次データをもとに売上・利益の着地を自動計算し表示する"
    },
    "②": {
        "label": "月中でも業績の着地を把握する",
        "problem": "月末まで利益着地が見えず、対策が後手になる",
        "solution": "月中の速報値から「今月の見込み」を先読みできるようにする",
        "approach": "日々の累積データから自動で着地予測を行いリアルタイム表示する"
    },
    "③": {
        "label": "見えにくい赤字先をあぶり出す",
        "problem": "一見好調でも利益貢献が低い先を感覚でしか把握できない",
        "solution": "隠れ赤字の商品・顧客を自動発見し、早期に対策を促す",
        "approach": "売上・粗利・費用構成を分析し、損益に悪影響の要因を可視化する"
    },
    "⑥": {
        "label": "異常な費用増加をすぐに察知する",
        "problem": "月次費用の急増要因がレポートからは分かりにくい",
        "solution": "通常と異なる費用動向を自動検出し、事前にアラートを出す",
        "approach": "今月の費用構成を過去傾向と比較し、異常をリアルタイム通知する"
    },
    "⑧": {
        "label": "予算と実績のズレを説明する",
        "problem": "予実差の原因が分かりにくく、説明に時間がかかる",
        "solution": "ズレ要因を自動分解し、即答できる説明アシスタントを実装する",
        "approach": "予算／実績差を項目別に分解・可視化し、因果関係を数値で示す"
    },
    "⑨": {
        "label": "現場KPIと利益の関係を見える化",
        "problem": "改善活動が利益にどう影響するか曖昧で説明しづらい",
        "solution": "現場KPIと利益の因果を可視化し、納得感ある説明を提供する",
        "approach": "稼働率や不良率などと利益を結び付け、改善効果を数値化する"
    },
    "⑩": {
        "label": "中期経営計画の実現性を評価する",
        "problem": "目標の実現可能性が直感に頼っており根拠が弱い",
        "solution": "過去実績に基づく達成確率を提供し、根拠ある計画策定を支援する",
        "approach": "実績と現状トレンドを組み合わせて、目標達成見込みを自動算出する"
    }
}

THEME_ORDER = ["①", "②", "③", "⑥", "⑧", "⑨", "⑩"]
THEME_LABELS = [f"{t} {THEME_INFO[t]['label']}" for t in THEME_ORDER]

# --- ページ状態管理 ---
if 'page' not in st.session_state:
    st.session_state['page'] = 0

def go_page(idx: int):
    st.session_state['page'] = idx
    st.experimental_rerun()

# --- P0: 開始 ---
def page_0():
    st.markdown("""
    # チェックシート診断へようこそ
    所要時間 3 分・全 20 問・回答は匿名可
    """)
    if st.button("アンケート開始"):
        go_page(1)

# --- P1: 質問入力（共通＋シグナル） ---
def page_1():
    from utils import COMMON_QUESTIONS_TEXT, CHOICES, CHOICE_MAP, THEME_SIGNAL_QUESTIONS, CHOICES_SIGNAL, CHOICE_MAP_SIGNAL
    st.header("全20問 一括回答")
    st.text_input("名前（任意）", key="user_name")
    st.text_input("所属（任意）", key="user_affil")
    st.markdown("---")
    st.subheader("共通質問 (6問)")
    for i, q in enumerate(COMMON_QUESTIONS):
        cols = st.columns([3,2])
        with cols[0]:
            st.write(COMMON_QUESTIONS_TEXT[i])
        with cols[1]:
            st.radio("", CHOICES, key=q, horizontal=True)
    st.markdown("---")
    st.subheader("困りごとチェック (14問)")
    for i, (qid, qtext) in enumerate(THEME_SIGNAL_QUESTIONS):
        cols = st.columns([3,2])
        with cols[0]:
            st.write(qtext)
        with cols[1]:
            st.radio("", CHOICES_SIGNAL, key=THEME_SIGNAL_KEYS[i], horizontal=True)
    if st.button("診断結果を見る"):
        all_common = all(st.session_state.get(q) for q in COMMON_QUESTIONS)
        all_signal = all(st.session_state.get(k) for k in THEME_SIGNAL_KEYS)
        if all_common and all_signal:
            ans = {
                'user_name': st.session_state.user_name,
                'user_affil': st.session_state.user_affil
            }
            for q in COMMON_QUESTIONS:
                ans[q] = CHOICE_MAP[st.session_state[q]]
            for i, k in enumerate(THEME_SIGNAL_KEYS):
                ans[k] = CHOICE_MAP_SIGNAL[st.session_state[k]]
            st.session_state['answers'] = ans
            append_row(ans)
            go_page(2)
        else:
            st.warning("全ての質問に回答してください")

# --- P2: 診断結果＋組織ダッシュボード ---
def page_2():
    st.header("診断結果・組織ダッシュボード")
    df = load_data()
    row = st.session_state.get('answers', {})

    # 個人診断（回答済のみ表示）
    if row and all(q in row for q in COMMON_QUESTIONS + THEME_SIGNAL_KEYS):
        common = sum(row[q] for q in COMMON_QUESTIONS) / len(COMMON_QUESTIONS)
        scores = {t: 0.4*common + 0.6*((row[f"{t}_Q1"]+row[f"{t}_Q2"])/2) for t in THEME_ORDER}
        top = max(scores, key=scores.get)
        info = THEME_INFO[top]

        st.markdown("### あなたの診断結果")
        st.markdown(f"**選定テーマ：{info['label']}**")
        st.markdown(f"- **問題**：{info['problem']}")
        st.markdown(f"- **解決策**：{info['solution']}")
        st.markdown(f"- **アプローチ**：{info['approach']}")

        # 棒グラフ（縦軸=スコア、横軸=テーマ → orientation="v"）
        bar = px.bar(
            x=THEME_LABELS,
            y=[scores[t] for t in THEME_ORDER],
            labels={'x':'テーマ','y':'スコア'},
            range_y=[0,100]
        )
        st.plotly_chart(bar, use_container_width=True)

        # レーダーチャート
        radar_df = pd.DataFrame({
            "テーマ": THEME_LABELS + [THEME_LABELS[0]],
            "スコア": [scores[t] for t in THEME_ORDER] + [scores[THEME_ORDER[0]]]
        })
        radar = px.line_polar(
            radar_df, r="スコア", theta="テーマ",
            line_close=True, range_r=[0,100], markers=True
        )
        st.plotly_chart(radar, use_container_width=True)

        st.button("この内容で保存", on_click=lambda: append_row(row) or st.success("回答を保存しました"))
    else:
        st.warning("個人診断は未回答のためスキップします。")

    st.markdown("---")
    st.subheader("組織ダッシュボード")

    # 回答者数
    st.write(f"回答者数：{len(df)} 名")

    # 散布図（各回答者のスコア分布を可視化）
    scatter_list = []
    for t in THEME_ORDER:
        for _, r in df.iterrows():
            avg = (r[f"{t}_Q1"] + r[f"{t}_Q2"]) / 2
            scatter_list.append({"テーマ": THEME_INFO[t]['label'], "スコア": avg})
    scatter_df = pd.DataFrame(scatter_list)
    scatter = px.strip(
        scatter_df, x="テーマ", y="スコア",
        labels={'テーマ':'テーマ','スコア':'スコア'},
    )
    st.plotly_chart(scatter, use_container_width=True)

    if st.button("最新データで更新"):
        st.experimental_rerun()
    if st.button("アンケートに戻る"):
        go_page(1)

# --- P3: 管理者画面 ---
def page_3():
    st.header("回答一覧・管理者専用")
    if not admin_gate():
        return
    df = load_data()
    st.dataframe(df)
    st.download_button("CSVダウンロード", df.to_csv(index=False), file_name="responses.csv")
    if st.button("アンケートに戻る"):
        go_page(1)

# --- ページ描画 ---
page_funcs = {
    0: page_0,
    1: page_1,
    2: page_2,
    3: page_3
}
page_funcs.get(st.session_state['page'], page_0)()

# --- サイドバー（当面残す） ---
with st.sidebar:
    st.title("ページ移動")
    for i, name in enumerate(["開始","質問入力","診断","管理"]):
        if st.button(name):
            go_page(i)