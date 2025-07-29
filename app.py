import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import yfinance as yf
import os

st.title("My METΔPLΔNET Trading History")

DEFAULT_CSV_PATH = "data/3350 - default.csv"

# デフォルトCSV読み込み関数
def load_default_csv():
    try:
        df = pd.read_csv(DEFAULT_CSV_PATH)
        df.rename(columns={'Date': 'DateLabel', 'End Value': 'EndV'}, inplace=True)
        return df
    except Exception as e:
        st.error(f"デフォルトCSVの読み込みに失敗しました: {e}")
        return pd.DataFrame(columns=['DateLabel', 'EndV', 'Sell', 'Buy'])

# 🔹 株価をyfinanceから取得
def fetch_stock_history():
    ticker = yf.Ticker("3350.T")
    df = ticker.history(period="1y")
    df.reset_index(inplace=True)
    df['DateLabel'] = df['Date'].dt.strftime('%Y-%m-%d')
    return df[['DateLabel', 'Close']].rename(columns={'Close': 'EndV'})

# 🔹 デフォルト読み込み
meta_df = load_default_csv()

# 🔹 yfinanceデータ取得
stock_df = fetch_stock_history()

# 🔹 defaultに存在しない日付を補完（EndVだけ埋める）
existing_dates = set(meta_df['DateLabel'])
new_dates_df = stock_df[~stock_df['DateLabel'].isin(existing_dates)].copy()

new_dates_df['Sell'] = 0
new_dates_df['Buy'] = 0
# new_dates_df['mNAV'] = 0

# 🔹 結合（古い＋新しい日付）
meta_df = pd.concat([meta_df, new_dates_df], ignore_index=True)

# ソート・整形
meta_df.sort_values('DateLabel', inplace=True)
meta_df.reset_index(drop=True, inplace=True)

meta_df['Sell'] = meta_df['Sell'].astype(str).str.replace(',', '').astype(float).fillna(0)
meta_df['Buy'] = meta_df['Buy'].astype(str).str.replace(',', '').astype(float).fillna(0)
# meta_df['mNAV'] = meta_df['mNAV'].astype(float).fillna(0)


# 🔹 CSVアップロード対応（あれば上書き）
uploaded_file = st.file_uploader("📂 CSVファイルをアップロード（任意）", type="csv")
if uploaded_file:
    try:
        uploaded_df = pd.read_csv(uploaded_file)
        uploaded_df.rename(columns={'Date': 'DateLabel', 'End Value': 'EndV'}, inplace=True)
        uploaded_df['DateLabel'] = uploaded_df['DateLabel'].astype(str)
        # 日付で上書きマージ
        meta_df = pd.merge(meta_df, uploaded_df, on='DateLabel', how='left', suffixes=('', '_u'))
        for col in ['EndV', 'Sell', 'Buy']:
            meta_df[col] = meta_df[f"{col}_u"].combine_first(meta_df[col])
            meta_df.drop(columns=[f"{col}_u"], inplace=True)
        st.success("✅ アップロードCSVを反映しました")
    except Exception as e:
        st.error(f"アップロードCSVの読み込み中にエラー: {e}")

meta_df['Sell'] = meta_df['Sell'].astype(str).str.replace(',', '').astype(float).fillna(0)
meta_df['Buy'] = meta_df['Buy'].astype(str).str.replace(',', '').astype(float).fillna(0)
# meta_df['mNAV'] = meta_df['mNAV'].astype(float).fillna(0)


# ===== 編集 & 保存 =====
st.subheader("📋 表データの編集 / Edit Data Table")
edited_df = st.data_editor(meta_df, num_rows="dynamic", use_container_width=True)

# 🔘 マーカーサイズの固定切り替え
fixed_marker_size = st.toggle("📏 マーカーサイズを固定する", value=False)

csv = edited_df.to_csv(index=False).encode("utf-8")
st.download_button("💾 編集後CSVをダウンロード", data=csv, file_name="edited_data.csv", mime="text/csv")

# ===== グラフ描画 =====
edited_df['DateLabel'] = pd.to_datetime(edited_df['DateLabel'])

# 編集後データの型変換も必要
for col in ['Sell', 'Buy']:
    edited_df[col] = (
        edited_df[col]
        .astype(str)
        .str.replace(',', '')
        .astype(float)
        .fillna(0)
    )


filtered_buy = edited_df[edited_df['Buy'] != 0]
filtered_sell = edited_df[edited_df['Sell'] != 0]

# 🔧 マーカーサイズ関数（トグル対応）
def get_marker_size(volume):
    if fixed_marker_size:
        return 50  # 固定サイズ
    try:
        volume = float(volume)
    except:
        return 60
    if volume < 1000:
        return 100
    elif volume < 2000:
        return 140
    elif volume < 10000:
        return 180
    else:
        return 220



fig, ax = plt.subplots(figsize=(12, 6))
fig.patch.set_facecolor('black')
ax.set_facecolor('black')

ax.plot(edited_df['DateLabel'], edited_df['EndV'], label='End Value', color='orange', alpha=0.6)

for i in range(len(filtered_buy)):
    ax.scatter(filtered_buy['DateLabel'].iloc[i], filtered_buy['EndV'].iloc[i],
               s=get_marker_size(filtered_buy['Buy'].iloc[i]), color='lightgreen',
               marker='^', alpha=0.8, label='Buy' if i == 0 else "")

for i in range(len(filtered_sell)):
    ax.scatter(filtered_sell['DateLabel'].iloc[i], filtered_sell['EndV'].iloc[i],
               s=get_marker_size(filtered_sell['Sell'].iloc[i]), color='red',
               marker='v', alpha=0.8, label='Sell' if i == 0 else "")

ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
fig.autofmt_xdate()

ax.set_title("My 3350 Trade History", color='white')
ax.set_xlabel("Date", color='white')
ax.set_ylabel("Value", color='white')
ax.legend()
ax.grid(True, color='gray', linestyle='--', alpha=0.3)
ax.tick_params(colors='white', which='both')

st.pyplot(fig)