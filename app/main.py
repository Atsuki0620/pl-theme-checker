import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils import load_data, append_row, admin_gate, COMMON_QUESTIONS, THEME_QUESTIONS
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="チェックシートアプリ", layout="wide")

# --- 質問／選択肢 定義 ---
COMMON_QUESTIONS_TEXT = [
    "C-1. 過去24か月以上の月次P/Lデータを抽出できますか？",
    "C-2. 製品・得意先・部門など粒度を保ったままP/Lを切り出せますか？",
    "C-3. 計画値（予算・中計）がシステム上で管理されていますか？",
    "C-4. 費用科目を物流費・外注費など内訳レベルで取得できますか？",
    "C-5. 稼働率・不良率など現場KPIをデータで取得できますか？",
    "C-6. PoCを限定スコープ（特定製品／工場）で実施する裁量がありますか？"
]
CHOICES = ["○ 問題ない", "△ 一部可能", "× 不可"]
CHOICE_MAP = {"○ 問題ない": 100, "△ 一部可能": 50, "× 不可": 0}

THEME_SIGNAL_QUESTIONS = [
    ("①-S1", "売上・利益の見通しが担当者の勘に頼りがちですか？"),
    ("①-S2", "予測誤差が調達や在庫に大きく影響していますか？"),
    ("②-S1", "月中に今月の営業利益着地を把握できず対応が遅れますか？"),
    ("②-S2", "月末締め前倒しを経営層から求められていますか？"),
    ("③-S1", "売上好調でも利益が伸び悩む製品／顧客が存在しますか？"),
    ("③-S2", "価格改定交渉の根拠データが不足していますか？"),
    ("⑥-S1", "外注費や物流費が突発的に膨らむ月がありますか？"),
    ("⑥-S2", "その原因特定に1週間以上かかることが多いですか？"),
    ("⑧-S1", "予算差異分析が金額列挙だけで終わっていますか？"),
    ("⑧-S2", "経営会議で乖離理由を即答できず困った経験がありますか？"),
    ("⑨-S1", "現場改善が利益にどう効くか数値裏付けがありませんか？"),
    ("⑨-S2", "工場と経理で成果指標が噛み合わず議論が平行線ですか？"),
    ("⑩-S1", "中期計画のKGIが“精神論”と批判されたことがありますか？"),
    ("⑩-S2", "過去実績から達成確率を検証したいニーズがありますか？")
]
CHOICES_SIGNAL = ["○ はい", "△ 部分的に当てはまる", "× いいえ"]
CHOICE_MAP_SIGNAL = {"○ はい": 100, "△ 部分的に当てはまる": 50, "× いいえ": 0}

# --- テーマ定義（solutionキー） ---
THEME_INFO = {
    "①": {
        "label": "売上・利益の予測精度を高める",
        "problem": "着地見通しが担当者の勘に頼り、精度にばらつきがある",
        "solution": "誰でも安定した予測が得られる未来予報システムを構築する",
        "approach": "過去の月次データを用い、売上・利益の着地を自動計算して表示する"
    },
    "②": {
        "label": "月中でも業績の着地を把握する",
        "problem": "月末まで利益着地が見えず、対策が後手になる",
        "solution": "月中の累積データから見込みを先読みできる可視化を実現する",
        "approach": "日々の速報値をもとに今月の着地を自動予測し表示する"
    },
    "③": {
        "label": "見えにくい赤字先をあぶり出す",
        "problem": "一見好調でも利益が薄い先を感覚でしか把握できない",
        "solution": "隠れ赤字の商品・顧客を自動発見し早期に警告する",
        "approach": "売上・粗利・費用の構成を分析し損益悪化要因を可視化する"
    },
    "⑥": {
        "label": "異常な費用増加をすぐに察知する",
        "problem": "月次費用の急増要因がレポートから分かりにくい",
        "solution": "通常と異なる費用動向を自動検出して事前にアラートを出す",
        "approach": "今月の費用構成を過去傾向と比較し異常をリアルタイム通知する"
    },
    "⑧": {
        "label": "予算と実績のズレを説明する",
        "problem": "予実差の原因が明確でなく説明に時間がかかる",
        "solution": "ズレ要因を自動分解し即答できる説明アシスタントを実装する",
        "approach": "予算と実績の差を項目別に分解・可視化して因果を示す"
    },
    "⑨": {
        "label": "現場KPIと利益の関係を見える化する",
        "problem": "改善活動が利益にどう影響するか曖昧で説明しづらい",
        "solution": "KPIと利益の因果を可視化し納得感ある説明を提供する",
        "approach": "稼働率や不良率と利益を結びつけ改善効果を数値化・表示する"
    },
    "⑩": {
        "label": "中期経営計画の実現性を評価する",
        "problem": "目標の実現可能性が直感に頼り根拠が弱い",
        "solution": "過去実績を基に達成確率を定量試算し根拠ある計画を支援する",
        "approach": "実績と現状トレンドを組み合わせ達成見込みを自動算出する"
    }
}
THEME_ORDER = list(THEME_QUESTIONS.keys())
THEME_LABELS = [f"{t} {THEME_INFO[t]['label']}" for t in THEME_ORDER]
THEME_SIGNAL_KEYS = sum(THEME_QUESTIONS.values(), [])

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
    st.header("全20問 一括回答")
    st.text_input("名前（任意）", key="user_name")
    st.text_input("所属（任意）", key="user_affil")
    st.markdown("---")
    st.subheader("共通質問 (6問)")
    for i, q in enumerate(COMMON_QUESTIONS):
        cols = st.columns([3,2])
        cols[0].write(COMMON_QUESTIONS_TEXT[i])
        cols[1].radio("", CHOICES, key=q, horizontal=True)
    st.markdown("---")
    st.subheader("困りごとチェック (14問)")
    for i, (_, qtext) in enumerate(THEME_SIGNAL_QUESTIONS):
        cols = st.columns([3,2])
        cols[0].write(qtext)
        cols[1].radio("", CHOICES_SIGNAL, key=THEME_SIGNAL_KEYS[i], horizontal=True)
    if st.button("診断結果を見る"):
        if all(st.session_state.get(q) for q in COMMON_QUESTIONS) and all(st.session_state.get(k) for k in THEME_SIGNAL_KEYS):
            ans = {'user_name': st.session_state.user_name, 'user_affil': st.session_state.user_affil}
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

    # 個人診断表示（未回答時はスキップ）
    if row and all(q in row for q in COMMON_QUESTIONS + THEME_SIGNAL_KEYS):
        common_avg = sum(row[q] for q in COMMON_QUESTIONS) / len(COMMON_QUESTIONS)
        scores = {t: 0.4*common_avg + 0.6*((row[f"{t}_Q1"]+row[f"{t}_Q2"])/2) for t in THEME_ORDER}
        top = max(scores, key=scores.get)
        info = THEME_INFO[top]

        st.markdown("### あなたの診断結果")
        st.markdown(f"**選定テーマ：{info['label']}**")
        st.markdown(f"- **問題**：{info['problem']}")
        st.markdown(f"- **解決策**：{info['solution']}")
        st.markdown(f"- **アプローチ**：{info['approach']}")

        # 縦棒グラフ (x=テーマ, y=スコア)
        bar = px.bar(
            x=THEME_LABELS,
            y=[scores[t] for t in THEME_ORDER],
            labels={'x':'テーマ','y':'スコア'},
            range_y=[0,100],
            orientation='v'
        )
        st.plotly_chart(bar, use_container_width=True)

        # レーダーチャート
        radar_df = pd.DataFrame({
            "テーマ": THEME_LABELS + [THEME_LABELS[0]],
            "スコア": [scores[t] for t in THEME_ORDER] + [scores[THEME_ORDER[0]]]
        })
        radar = px.line_polar(radar_df, r="スコア", theta="テーマ",
                              line_close=True, range_r=[0,100], markers=True)
        st.plotly_chart(radar, use_container_width=True)

        st.button("この内容で保存", on_click=lambda: append_row(row) or st.success("回答を保存しました"))
    else:
        st.warning("個人診断は未回答のためスキップします。")

    st.markdown("---")
    st.subheader("組織ダッシュボード")

    st.write(f"回答者数：{len(df)} 名")

    # 散布図で回答者ごとのスコア分布
    scatter_data = []
    for t in THEME_ORDER:
        for _, r in df.iterrows():
            scatter_data.append({"テーマ": THEME_INFO[t]['label'], "スコア": (r[f"{t}_Q1"]+r[f"{t}_Q2"])/2})
    scatter_df = pd.DataFrame(scatter_data)
    scatter = px.strip(scatter_df, x="テーマ", y="スコア", labels={'テーマ':'テーマ','スコア':'スコア'})
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
page_funcs = {0: page_0, 1: page_1, 2: page_2, 3: page_3}
page_funcs.get(st.session_state['page'], page_0)()

# --- サイドバー（残す） ---
with st.sidebar:
    st.title("ページ移動")
    for i, name in enumerate(["開始","質問入力","診断","管理"]):
        if st.button(name):
            go_page(i)
