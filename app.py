import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os

st.title("My 3350 Trade History")

DEFAULT_CSV_PATH = "data/default.csv"

# デフォルトCSV読み込み関数
def load_default_csv():
    try:
        df = pd.read_csv(DEFAULT_CSV_PATH)
        df.rename(columns={'日付': 'DateLabel', '終値': 'EndV'}, inplace=True)
        return df
    except Exception as e:
        st.error(f"デフォルトCSVの読み込みに失敗しました: {e}")
        return pd.DataFrame(columns=['DateLabel', 'EndV', '売り', '買い', 'mNAV'])

# アップロードファイル取得
uploaded_file = st.file_uploader("📂 CSVファイルをアップロードしてください（任意）", type="csv")

# データ読み込み処理
if uploaded_file is not None:
    try:
        user_df = pd.read_csv(uploaded_file)
        user_df.rename(columns={'日付': 'DateLabel', '終値': 'EndV'}, inplace=True)
        meta_df = user_df
        st.success("✅ アップロードCSVを読み込みました")
    except Exception as e:
        st.error(f"CSV読み込み中にエラーが発生しました: {e}")
        st.stop()
else:
    st.info("📈 デフォルトデータ（default.csv）を読み込んでいます")
    meta_df = load_default_csv()

# データ整形
meta_df.sort_values('DateLabel', inplace=True)
meta_df.reset_index(drop=True, inplace=True)

# データ型変換（念のため）
for col in ['売り', '買い', 'mNAV']:
    meta_df[col] = pd.to_numeric(meta_df[col], errors='coerce').fillna(0)

# ===== 表編集 & 保存 =====
st.subheader("📋 表データの編集 / Edit Data Table")
edited_df = st.data_editor(meta_df, num_rows="dynamic", use_container_width=True)

# ダウンロードボタン
csv = edited_df.to_csv(index=False).encode("utf-8")
st.download_button("💾 編集後CSVをダウンロード", data=csv, file_name="edited_data.csv", mime="text/csv")

# ===== グラフ描画 =====
edited_df['DateLabel'] = pd.to_datetime(edited_df['DateLabel'])

filtered_buy = edited_df[edited_df['買い'] != 0]
filtered_sell = edited_df[edited_df['売り'] != 0]

def get_marker_size(volume):
    if volume < 1000:
        return 60
    elif volume < 2000:
        return 100
    elif volume < 10000:
        return 140
    else:
        return 180

fig, ax = plt.subplots(figsize=(12, 6))
fig.patch.set_facecolor('black')
ax.set_facecolor('black')

ax.plot(edited_df['DateLabel'], edited_df['EndV'], label='End Value', color='orange', alpha=0.6)

for i in range(len(filtered_buy)):
    ax.scatter(filtered_buy['DateLabel'].iloc[i], filtered_buy['EndV'].iloc[i],
               s=get_marker_size(filtered_buy['買い'].iloc[i]), color='green',
               marker='^', alpha=0.8, label='Buy' if i == 0 else "")

for i in range(len(filtered_sell)):
    ax.scatter(filtered_sell['DateLabel'].iloc[i], filtered_sell['EndV'].iloc[i],
               s=get_marker_size(filtered_sell['売り'].iloc[i]), color='red',
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
