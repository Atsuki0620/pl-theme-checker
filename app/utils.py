from typing import Tuple, Dict, Any
import pandas as pd
import streamlit as st
import os

CSV_PATH = 'data/responses.csv'
THEMES = ['①', '②', '③', '⑥', '⑧', '⑨', '⑩']
THEME_QUESTIONS = {t: [f'{t}_Q1', f'{t}_Q2'] for t in THEMES}
COMMON_QUESTIONS = [f'common_Q{i+1}' for i in range(6)]
ALL_COLUMNS = ['user_name'] + COMMON_QUESTIONS + sum(THEME_QUESTIONS.values(), [])


def load_data() -> pd.DataFrame:
    if not os.path.exists(CSV_PATH):
        df = pd.DataFrame(columns=ALL_COLUMNS)
        df.to_csv(CSV_PATH, index=False, encoding='utf-8')
    return pd.read_csv(CSV_PATH, encoding='utf-8')


def append_row(row: Dict[str, Any]) -> None:
    df = load_data()
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(CSV_PATH, index=False, encoding='utf-8')


def calc_scores(row: Dict[str, Any]) -> Tuple[float, Dict[str, float], float]:
    common_scores = [row[q] for q in COMMON_QUESTIONS]
    common_avg = sum(common_scores) / len(common_scores)
    signal_scores = {}
    for t, qs in THEME_QUESTIONS.items():
        signal_scores[t] = sum([row[q] for q in qs]) / 2
    # 仮: ①テーマを signal として合成
    total = 0.4 * common_avg + 0.6 * signal_scores['①']
    return common_avg, signal_scores, total


def admin_gate() -> bool:
    pw = st.text_input('管理者パスワード', type='password')
    if st.button('認証'):
        if pw == st.secrets['admin_pass']:
            st.session_state['admin_ok'] = True
        else:
            st.error('パスワードが違います')
    return st.session_state.get('admin_ok', False)
