import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
import matplotlib.font_manager as fm
import matplotlib.dates as mdates

st.title("My 3350 Trade History")

# ファイルアップロード
uploaded_file = st.file_uploader("CSVファイルをアップロードしてください / Upload your CSV file", type="csv")

# データ読み込み
if uploaded_file is not None:
    try:
        # アップロードされたCSV読み込み
        meta = pd.read_csv(uploaded_file)

        meta_index = {
            'DateLabel': meta['日付'].tolist(),
            'EndV': meta['終値'].tolist(),
            '売り': meta['売り'].tolist(),
            '買い': meta['買い'].tolist(),
            'mNAV': meta['mNAV'].tolist(),
        }
        meta_df = pd.DataFrame(meta_index)

        # 日付補完用に株価取得
        ticker = yf.Ticker("3350.T")
        df = ticker.history(period="1y")
        df_close = df[['Close']].copy()
        df_close.reset_index(inplace=True)
        df_close['DateLabel'] = df_close['Date'].dt.strftime('%Y-%m-%d')

        # CSVに存在しない日付を追加
        existing_dates = set(meta_df['DateLabel'])
        new_dates_df = df_close[~df_close['DateLabel'].isin(existing_dates)]

        for _, row in new_dates_df.iterrows():
            new_row = {
                'DateLabel': row['DateLabel'],
                'EndV': row['Close'],
                '売り': 0,
                '買い': 0,
                'mNAV': 0
            }
            meta_df = pd.concat([meta_df, pd.DataFrame([new_row])], ignore_index=True)

        # 株価補完
        meta_df = pd.merge(meta_df, df_close[['DateLabel', 'Close']], on='DateLabel', how='left')
        meta_df['EndV'] = meta_df['Close'].combine_first(meta_df['EndV'])
        meta_df.drop(columns=['Close'], inplace=True)

    except Exception as e:
        st.error(f"CSV読み込み中にエラーが発生しました: {e}")
        st.stop()

else:
    st.info("📈 デフォルトモードでデータを取得中（3350.T, 過去1年）")
    ticker = yf.Ticker("3350.T")
    df = ticker.history(period="1y")
    df.reset_index(inplace=True)
    df['DateLabel'] = df['Date'].dt.strftime('%Y-%m-%d')

    meta_df = pd.DataFrame({
        'DateLabel': df['DateLabel'],
        'EndV': df['Close'],
        '売り': 0,
        '買い': 0,
        'mNAV': 0
    })

# データ型の整備
meta_df.sort_values('DateLabel', inplace=True)
meta_df.reset_index(drop=True, inplace=True)

meta_df['売り'] = meta_df['売り'].astype(str).str.replace(',', '').astype(float).fillna(0)
meta_df['買い'] = meta_df['買い'].astype(str).str.replace(',', '').astype(float).fillna(0)
meta_df['mNAV'] = meta_df['mNAV'].astype(float).fillna(0)

# ===== 表編集 & 保存 =====
st.subheader("📋 表データの編集 / Edit Data Table")
edited_df = st.data_editor(meta_df, num_rows="dynamic", use_container_width=True)

# ダウンロードボタン
csv = edited_df.to_csv(index=False).encode("utf-8")
st.download_button("💾 編集後CSVをダウンロード / Download Edited CSV", data=csv, file_name="edited_data.csv", mime="text/csv")

# ===== グラフ描画 =====
edited_df['DateLabel'] = pd.to_datetime(edited_df['DateLabel'])

filtered_buy = edited_df[edited_df['買い'] != 0]
filtered_sell = edited_df[edited_df['売り'] != 0]

buy_dates = filtered_buy['DateLabel'].tolist()
buy_volumes = filtered_buy['買い'].tolist()
sell_dates = filtered_sell['DateLabel'].tolist()
sell_volumes = filtered_sell['売り'].tolist()

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

# 買いマーカー
for i in range(len(buy_dates)):
    ax.scatter(buy_dates[i], filtered_buy['EndV'].iloc[i], s=get_marker_size(buy_volumes[i]),
               color='green', alpha=0.8, label='Buy' if i == 0 else "")

# 売りマーカー
for i in range(len(sell_dates)):
    ax.scatter(sell_dates[i], filtered_sell['EndV'].iloc[i], s=get_marker_size(sell_volumes[i]),
               color='red', alpha=0.8, label='Sell' if i == 0 else "")

# 横軸日付整形
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
fig.autofmt_xdate()

# ラベル・デザイン調整
ax.set_title("My 3350 Trade History", color='white')
ax.set_xlabel("Date", color='white')
ax.set_ylabel("Value", color='white')
ax.legend()
ax.grid(True, color='gray', linestyle='--', alpha=0.3)
ax.tick_params(colors='white', which='both')

st.pyplot(fig)
