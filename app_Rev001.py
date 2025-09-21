import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import yfinance as yf

st.title("My METΔPLΔNET Trading History")

DEFAULT_CSV_PATH = "data/3350 - default.csv"

# ===============================
# デフォルトCSV読み込み関数
# ===============================
def load_default_csv():
    try:
        df = pd.read_csv(DEFAULT_CSV_PATH)
        df.rename(columns={'Date': 'DateLabel', 'End Value': 'EndV'}, inplace=True)
    except:
        df = pd.DataFrame(columns=['DateLabel', 'EndV', 'Sell', 'Buy'])
    return df

# ===============================
# 株価をyfinanceから取得
# ===============================
def fetch_stock_history():
    try:
        ticker = yf.Ticker("3350.T")
        df = ticker.history(period="3mo")
        df.reset_index(inplace=True)
        df['DateLabel'] = df['Date'].dt.strftime('%Y-%m-%d')  # ←文字列にする
        return df[['DateLabel', 'Close']].rename(columns={'Close': 'EndV'})
    except:
        return pd.DataFrame(columns=['DateLabel', 'EndV'])

# ===============================
# 初期ロード（session_stateで保持）
# ===============================
if "meta_df" not in st.session_state:
    default_df = load_default_csv()
    stock_df = fetch_stock_history()

    existing_dates = set(default_df['DateLabel'])
    new_dates_df = stock_df[~stock_df['DateLabel'].isin(existing_dates)].copy()
    new_dates_df['Sell'] = 0
    new_dates_df['Buy'] = 0

    combined_df = pd.concat([default_df, new_dates_df], ignore_index=True)
    combined_df = combined_df[['DateLabel', 'EndV', 'Sell', 'Buy']]
    combined_df['Sell'] = pd.to_numeric(combined_df['Sell'], errors='coerce').fillna(0)
    combined_df['Buy'] = pd.to_numeric(combined_df['Buy'], errors='coerce').fillna(0)

    # 🔹内部は文字列として保持
    combined_df['DateLabel'] = combined_df['DateLabel'].astype(str)

    st.session_state.meta_df = combined_df.copy()

# ここから先は session_state を使う
meta_df = st.session_state.meta_df.copy()

# ===============================
# CSVアップロード対応（任意）
# ===============================
uploaded_file = st.file_uploader("📂 Upload CSV File（任意 / Optional）", type="csv")
if uploaded_file:
    try:
        uploaded_df = pd.read_csv(uploaded_file)
        uploaded_df.rename(columns={'Date': 'DateLabel', 'End Value': 'EndV'}, inplace=True)
        uploaded_df = uploaded_df[['DateLabel', 'EndV', 'Sell', 'Buy']]
        uploaded_df['Sell'] = pd.to_numeric(uploaded_df['Sell'], errors='coerce').fillna(0)
        uploaded_df['Buy'] = pd.to_numeric(uploaded_df['Buy'], errors='coerce').fillna(0)

        # 🔹内部は文字列に統一
        uploaded_df['DateLabel'] = uploaded_df['DateLabel'].astype(str)
        meta_df['DateLabel'] = meta_df['DateLabel'].astype(str)

        merged_df = pd.merge(meta_df, uploaded_df, on='DateLabel', how='outer', suffixes=('', '_u'))
        for c in ['EndV', 'Sell', 'Buy']:
            merged_df[c] = merged_df[f"{c}_u"].combine_first(merged_df[c])
            if f"{c}_u" in merged_df:
                merged_df.drop(columns=f"{c}_u", inplace=True)

        st.session_state.meta_df = merged_df
        meta_df = merged_df.copy()
        st.success("✅ アップロードCSVを反映しました")
    except Exception as e:
        st.error(f"アップロードCSVの読み込み中にエラー: {e}")

# ===============================
# 表データ編集
# ===============================
st.subheader("📋 表データの編集 / Edit Data Table")
tmp_df = st.data_editor(meta_df, num_rows="dynamic", use_container_width=True)

# 編集結果をsession_stateに反映
st.session_state.meta_df = tmp_df.copy()

# ===============================
# マーカーサイズモード
# ===============================
marker_size_mode = st.selectbox(
    "マーカーサイズのモードを選択 / Marker Size Mode",
    ["固定サイズ Fix size", "段階サイズ Step size", "比例サイズ Proportional size"],
    index=1
)

# ===============================
# ダウンロードボタン
# ===============================
csv = tmp_df.to_csv(index=False).encode("utf-8")
st.download_button("💾 編集後CSVをダウンロード / Export the updated CSV",
                   data=csv, file_name="MetaplanetTradingData.csv", mime="text/csv")

# ===============================
# グラフ描画
# ===============================
plot_df = tmp_df.copy()

# グラフ描画の直前だけdatetimeに変換
plot_df['DateLabel'] = pd.to_datetime(plot_df['DateLabel'], errors='coerce')
plot_df['Sell'] = pd.to_numeric(plot_df['Sell'], errors='coerce').fillna(0)
plot_df['Buy'] = pd.to_numeric(plot_df['Buy'], errors='coerce').fillna(0)

filtered_buy = plot_df[plot_df['Buy'] != 0]
filtered_sell = plot_df[plot_df['Sell'] != 0]

def get_marker_size(volume):
    try:
        volume = float(volume)
    except:
        return 60

    if marker_size_mode == "固定サイズ Fix size":
        return 50
    elif marker_size_mode == "段階サイズ Step size":
        if volume < 1000:
            return 100
        elif volume < 2000:
            return 140
        elif volume < 10000:
            return 180
        else:
            return 220
    elif marker_size_mode == "比例サイズ Proportional size":
        scale = 0.02
        return max(volume * scale, 20)

fig, ax = plt.subplots(figsize=(12, 6))
fig.patch.set_facecolor('black')
ax.set_facecolor('black')

ax.plot(plot_df['DateLabel'], plot_df['EndV'], label='End Value', color='orange', alpha=0.6)

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

ax.set_title("My METΔPLΔNET Trading History", color='white')
ax.set_xlabel("Date", color='white')
ax.set_ylabel("Value", color='white')
legend = ax.legend()
for text in legend.get_texts():
    text.set_color('white')
legend.get_frame().set_facecolor('none')
legend.get_frame().set_edgecolor('white')

ax.grid(True, color='gray', linestyle='--', alpha=0.3)
ax.tick_params(colors='white', which='both')

st.pyplot(fig)
