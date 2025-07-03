import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils import load_data, append_row, calc_scores, admin_gate, THEMES, THEME_QUESTIONS, COMMON_QUESTIONS, ALL_COLUMNS
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="チェックシートアプリ", layout="wide")

# --- テーマ定義 ---
THEME_INFO = {
    "①": {
        "label": "売上・利益の予測精度を高める",
        "problem": "着地見通しが担当者の経験や勘に頼っており、精度にばらつきがある",
        "task": "業績の着地予測を属人化せず、誰でも高精度に把握できる“未来予報システム”を実現する",
        "approach": "これまでの業績推移データを活用し、売上や利益の未来値を“自動で計算・表示”する機能を構築する"
    },
    "②": {
        "label": "月中でも業績の着地を把握する",
        "problem": "月末を迎えるまで売上・費用・利益がどの程度か分からない",
        "task": "決算を待たずに“今月の見込み”を先読みできる“リアルタイム可視化”を実現する",
        "approach": "日々の速報値や累積情報から、今月の売上・利益などを自動予測し、月中でも“先手の経営判断”が可能になる"
    },
    "③": {
        "label": "見えにくい赤字先をあぶり出す",
        "problem": "製品や顧客ごとの収益性が感覚に頼っており、対策が後手になりやすい",
        "task": "一見好調に見える“隠れ赤字商品や顧客”をAIが自動で発見・警告してくれる仕組みをつくる",
        "approach": "売上・利益・販管費などの構成を分析し、“どこで損をしているか”を自動的に可視化して経営判断に活かす"
    },
    "⑥": {
        "label": "異常な費用増加をすぐに察知する",
        "problem": "毎月の費用がどこで大きく変わったのか、報告書からでは分かりにくい",
        "task": "“いつもと違う費用の動き”をAIが察知して、報告前にアラートしてくれる仕組みをつくる",
        "approach": "月次の費用データから、通常とは異なる傾向をリアルタイムで検出し、“経理が先回りして異常を説明できる状態”を実現する"
    },
    "⑧": {
        "label": "予算と実績のズレを説明する",
        "problem": "予実差が出たとき、原因が明確でなく説明に時間がかかる",
        "task": "“なぜズレたのか”を自動で数値分解してくれる“説明アシスタント”を実現する",
        "approach": "予算と実績の差分を、売上構成や費用項目ごとに機械的に分解・可視化し、“即答できる経理”を実現する"
    },
    "⑨": {
        "label": "現場KPIと利益の関係を見える化",
        "problem": "工場の改善活動が利益にどう効いているかが曖昧で説明しづらい",
        "task": "“現場での改善活動が、会社の利益にどうつながるか”を誰が見ても納得できる形で説明できる状態を目指す",
        "approach": "工場の稼働率や不良率といったデータと財務数値をつなげて、“改善の効果がどれだけ利益に効いているか”を数値で証明する"
    },
    "⑩": {
        "label": "中期経営計画の実現性を評価する",
        "problem": "目標値が高すぎる・低すぎるなど、実現可能性が直感に頼っている",
        "task": "“その目標、本当に実現できるのか？”を、根拠ある数字で語れる経営判断ツールを構築する",
        "approach": "過去の実績や傾向をもとに、中期計画の達成確率を定量的に算出し、“机上の空論”から“現実に即した戦略”へ導く"
    }
}

THEME_ORDER = ["①", "②", "③", "⑥", "⑧", "⑨", "⑩"]
THEME_LABELS = [f"{k} {THEME_INFO[k]['label']}" for k in THEME_ORDER]

# テーマのアルファベット識別子
THEME_ALPHA = {
    "①": "A",
    "②": "B",
    "③": "C",
    "⑥": "D",
    "⑧": "E",
    "⑨": "F",
    "⑩": "G"
}
THEME_LABELS_ALPHA = [f"{THEME_ALPHA[k]} {THEME_INFO[k]['label']}" for k in THEME_ORDER]
THEME_LABELS_ALPHA_MAP = {k: f"{THEME_ALPHA[k]} {THEME_INFO[k]['label']}" for k in THEME_ORDER}

# --- 質問文定義 ---
COMMON_QUESTIONS_TEXT = [
    "C-1. 過去24か月以上の月次P/Lデータを抽出できますか？",
    "C-2. 製品・得意先・部門など粒度を保ったままP/Lを切り出せますか？",
    "C-3. 計画値（予算・中計）がシステム上で管理されていますか？",
    "C-4. 費用科目を物流費・外注費など内訳レベルで取得できますか？",
    "C-5. 稼働率・不良率など現場KPIをデータで取得できますか？",
    "C-6. PoCを限定スコープ（特定製品／工場）で実施する裁量がありますか？"
]
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
THEME_SIGNAL_KEYS = [
    '①_Q1', '①_Q2', '②_Q1', '②_Q2', '③_Q1', '③_Q2', '⑥_Q1', '⑥_Q2',
    '⑧_Q1', '⑧_Q2', '⑨_Q1', '⑨_Q2', '⑩_Q1', '⑩_Q2'
]

CHOICES = ["○ 問題ない", "△ 一部可能", "× 不可"]
CHOICE_MAP = {"○ 問題ない": 100, "△ 一部可能": 50, "× 不可": 0}
CHOICES_SIGNAL = ["○ はい", "△ 部分的に当てはまる", "× いいえ"]
CHOICE_MAP_SIGNAL = {"○ はい": 100, "△ 部分的に当てはまる": 50, "× いいえ": 0}

if 'page' not in st.session_state:
    st.session_state['page'] = 0
if 'answers' not in st.session_state:
    st.session_state['answers'] = {}

PAGES = ["P0:開始", "P1:ユーザー情報", "P2:共通質問", "P3:困りごとチェック", "P4:診断結果", "P5:一覧", "P6:ダッシュボード"]

# --- ページ遷移 ---
def go_page(page_idx: int):
    st.session_state['page'] = page_idx

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
    # 最新データを必ずロード
    df = load_data()
    row = st.session_state.get('answers', {})
    # スコア計算
    if not row or not all(q in row for q in COMMON_QUESTIONS+THEME_SIGNAL_KEYS):
        st.warning("先に全ての質問に回答してください")
        if st.button("アンケートに戻る", key="back_to_q"):
            go_page(1)
        return
    common_score = sum([row[q] for q in COMMON_QUESTIONS]) / 6
    theme_scores = {}
    for idx, t in enumerate(THEME_ORDER):
        t_keys = [f'{t}_Q1', f'{t}_Q2']
        theme_scores[t] = 0.4 * common_score + 0.6 * (row[t_keys[0]] + row[t_keys[1]]) / 2
    top_theme = max(theme_scores, key=theme_scores.get)
    # --- テーマ一覧（アルファベット・名称・問題） ---
    st.markdown("""
    <div style='background:#f8fafc;padding:0.5em 1em 0.5em 1em;border-radius:10px;margin-bottom:1em;'>
    <span style='font-size:1.1em;font-weight:bold;color:#1a4b7a;'>【テーマ一覧】</span><br>
    """ +
    "<br>".join([
        f"<b>{THEME_ALPHA[t]} {THEME_INFO[t]['label']}</b>：{THEME_INFO[t]['problem']}"
        for t in THEME_ORDER
    ]) +
    "</div>"
    , unsafe_allow_html=True)
    # --- 選定テーマ概要カード ---
    top_info = THEME_INFO[top_theme]
    st.markdown(f"""
    <div style='background:#f0f6ff;padding:1em 1.5em 1em 1.5em;border-radius:10px;margin-bottom:1em;'>
    <span style='font-size:1.2em;font-weight:bold;color:#1a4b7a;'>選定テーマ：{THEME_INFO[top_theme]['label']}（{THEME_ALPHA[top_theme]}）</span><br>
    <span style='color:#333'><b>問題:</b> {top_info['problem']}<br>
    <b>課題:</b> {top_info['task']}<br>
    <b>アプローチ:</b> {top_info['approach']}</span>
    </div>
    """, unsafe_allow_html=True)
    # --- 個人スコアグラフ ---
    st.subheader("あなたの総合スコア（テーマ別）")
    bar = px.bar(x=[theme_scores[t] for t in THEME_ORDER], y=THEME_LABELS_ALPHA, orientation='h', labels={'x':'総合スコア','y':'テーマ'}, range_x=[0,100], color=[THEME_LABELS_ALPHA_MAP[t] for t in THEME_ORDER], color_discrete_sequence=px.colors.qualitative.Pastel)
    bar.update_layout(yaxis=dict(categoryorder='total ascending'))
    st.plotly_chart(bar, use_container_width=True)
    # レーダーチャート
    radar_df = pd.DataFrame(dict(r=[theme_scores[t] for t in THEME_ORDER]+[theme_scores[THEME_ORDER[0]]], theta=THEME_LABELS_ALPHA+[THEME_LABELS_ALPHA[0]]))
    radar = px.line_polar(radar_df, r="r", theta="theta", line_close=True, range_r=[0,100], markers=True, color_discrete_sequence=["#1a4b7a"])
    st.plotly_chart(radar, use_container_width=True)
    # 保存
    if st.button("この内容で保存", key="save_result"):
        append_row(row)
        st.success("回答を保存しました")
    st.markdown("---")
    # --- 組織ダッシュボード ---
    st.subheader("組織ダッシュボード（全員分のスコア）")
    if 'user_name' in df.columns:
        df = df.drop(columns=['user_name'])
    theme_means = {t: df[[f'{t}_Q1', f'{t}_Q2']].mean(axis=1).mean() for t in theme_scores}
    # theme_popularの生成方法を修正（dictにする）
    theme_popular = {t: ((df[[f'{t}_Q1', f'{t}_Q2']] >= 80).mean().mean()) for t in theme_scores}
    # --- KPIカード（縦並び・内容修正） ---
    kpi_labels = [
        ("平均トップ", max(theme_means, key=theme_means.get) if theme_means else None),
        ("人気率トップ", max(theme_popular, key=theme_popular.get) if theme_popular else None),
        ("データ備え度トップ", max(theme_popular, key=lambda t: theme_popular[t]) if theme_popular else None)
    ]
    recommend_theme = [t for t in theme_means if theme_means[t] >= 70 and theme_popular[t] >= 0.4]
    recommend_theme = sorted(recommend_theme, key=lambda t: theme_means[t], reverse=True)
    kpi_labels.append(("総合推奨", recommend_theme[0] if recommend_theme else None))
    for label, t in kpi_labels:
        if t:
            st.markdown(f"<div style='background:#eaf4ff;padding:0.7em 1em 0.7em 1em;border-radius:8px;margin-bottom:0.5em;'><b>{label}：</b> {THEME_LABELS_ALPHA_MAP[t]}（平均{theme_means[t]:.1f}点, 80点以上率{theme_popular[t]*100:.0f}%）</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='background:#eaf4ff;padding:0.7em 1em 0.7em 1em;border-radius:8px;margin-bottom:0.5em;'><b>{label}：</b> - </div>", unsafe_allow_html=True)
    # --- 組織レーダーチャート ---
    st.subheader("組織スコア（レーダーチャート）")
    n_respondents = len(df)
    org_radar_df = pd.DataFrame({
        "テーマ": THEME_LABELS_ALPHA,
        "平均スコア": [theme_means[t] for t in THEME_ORDER]
    })
    org_radar_df = pd.concat([org_radar_df, org_radar_df.iloc[[0]]], ignore_index=True)
    org_radar_df["テーマ"] = org_radar_df["テーマ"].astype(str)
    org_radar = px.line_polar(org_radar_df, r="平均スコア", theta="テーマ", line_close=True, range_r=[0,100], markers=True, color_discrete_sequence=["#2a7bbd"])
    org_radar.update_layout(title=f"回答者数: {n_respondents}人  平均値: {sum(theme_means.values())/len(theme_means):.1f}点" if n_respondents else "",
        font=dict(size=16), legend=dict(font=dict(size=14)))
    st.plotly_chart(org_radar, use_container_width=True)
    # --- 組織スコア縦棒グラフ（各回答者ごと） ---
    st.subheader("組織スコア（回答者別・縦棒グラフ）")
    if n_respondents > 0:
        respondent_labels = [f'R{i+1}' for i in range(n_respondents)]
        respondent_scores = []
        for i in range(n_respondents):
            respondent_scores.append([ (df.iloc[i][f'{t}_Q1'] + df.iloc[i][f'{t}_Q2']) / 2 for t in THEME_ORDER])
        bar_df = pd.DataFrame(respondent_scores, columns=THEME_LABELS_ALPHA, index=respondent_labels)
        bar_df = bar_df.transpose()
        org_bar = px.bar(bar_df, x=bar_df.index, y=bar_df.columns, barmode='group',
                        labels={'value':'スコア','x':'テーマ','variable':'回答者'},
                        color_discrete_sequence=px.colors.qualitative.Pastel)
        org_bar.update_layout(font=dict(size=16), legend=dict(font=dict(size=14)))
        st.plotly_chart(org_bar, use_container_width=True)
    # --- 優先候補テーマカード ---
    st.subheader("優先候補テーマ")
    if recommend_theme:
        for t in recommend_theme:
            info = THEME_INFO[t]
            st.markdown(f"""
            <div style='background:#f0f6ff;padding:1em 1.5em 1em 1.5em;border-radius:10px;margin-bottom:1em;'>
            <span style='font-size:1.1em;font-weight:bold;color:#1a4b7a;'>候補テーマ：{THEME_INFO[t]['label']}（{THEME_ALPHA[t]}）</span><br>
            <span style='color:#333'><b>問題:</b> {info['problem']}<br>
            <b>課題:</b> {info['task']}<br>
            <b>アプローチ:</b> {info['approach']}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("現時点で合意形成に必要な条件を満たすテーマはありません")
    if st.button("最新データで更新", key="refresh_dash"):
        st.rerun()
    if st.button("アンケートに戻る", key="back_to_q2"):
        go_page(1)

# --- P3: 管理者画面 ---
def page_3():
    st.header("回答一覧・管理者専用")
    if not admin_gate():
        st.stop()
    # 最新データを必ずロード
    df = load_data()
    st.dataframe(df)
    st.download_button("CSVダウンロード", df.to_csv(index=False, encoding='utf-8-sig'), file_name="responses.csv")
    # レコード削除
    st.markdown("---")
    st.subheader("レコード削除（行番号指定）")
    if len(df) > 0:
        idx = st.number_input("削除したい行番号 (0～%d)" % (len(df)-1), min_value=0, max_value=len(df)-1, step=1, key="del_idx")
        if st.button("この行を削除", key="del_btn"):
            df = df.drop(df.index[idx]).reset_index(drop=True)
            df.to_csv('data/responses.csv', index=False, encoding='utf-8')
            st.success(f"行 {idx} を削除しました。最新状態で再表示します。")
            st.rerun()
    if st.button("アンケートに戻る", key="back_to_q3"):
        go_page(1)

# --- ページ描画 ---
page_funcs = [page_0, page_1, page_2, page_3]
page_funcs[st.session_state['page']]()

# --- サイドバー ---
st.sidebar.title("ページ移動")
page_names = ["アンケート開始", "質問入力", "診断・ダッシュボード", "管理者"]
for i, p in enumerate(page_names):
    if st.sidebar.button(p, key=f"side_{i}"):
        go_page(i)
        st.rerun()
