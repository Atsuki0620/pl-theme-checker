# Streamlit チェックシートアプリ

## 起動手順

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app/main.py
```

- `data/responses.csv` は自動生成されます。
- 管理者ページのパスワードは `.streamlit/secrets.toml` で設定してください。
