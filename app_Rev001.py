import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import yfinance as yf

st.title("My METΔPLΔNET Trading History")

DEFAULT_CSV_PATH = "data/3350 - default.csv"

# -------------------------
# ヘルパー関数
# -------------------------
def load_default_csv():
    try:
        df = pd.read_csv(DEFAULT_CSV_PATH)
        df.rename(columns={'Date': 'DateLabel', 'End Value': 'EndV'}, inplace=True)
    except Exception:
        df = pd.DataFrame(columns=['DateLabel', 'EndV', 'Sell', 'Buy'])
    for c in ['DateLabel', 'EndV', 'Sell', 'Buy']:
        if c not in df.columns:
            df[c] = ""
    return df[['DateLabel', 'EndV', 'Sell', 'Buy']].fillna("").astype(str)

def fetch_stock_history():
    try:
        ticker = yf.Ticker("3350.T")
        df = ticker.history(period="3mo")
        df.reset_index(inplace=True)
        df['DateLabel'] = df['Date'].dt.strftime('%Y-%m-%d')
        df['Sell'] = ""
        df['Buy'] = ""
        return df[['DateLabel', 'Close', 'Sell', 'Buy']].rename(columns={'Close': 'EndV'}).astype(str)
    except Exception:
        return pd.DataFrame(columns=['DateLabel', 'EndV', 'Sell', 'Buy']).astype(str)

# -------------------------
# 初期ロード
# -------------------------
if "meta_df" not in st.session_state:
    base_df = load_default_csv()
    stock_df = fetch_stock_history()
    existing_dates = set(base_df['DateLabel'])
    new_dates_df = stock_df[~stock_df['DateLabel'].isin(existing_dates)].copy()
    combined_df = pd.concat([base_df, new_dates_df], ignore_index=True)
    st.session_state.meta_df = combined_df.fillna("").astype(str)

meta_df = st.session_state.meta_df.copy()

# -------------------------
# CSVアップロード
# -------------------------
uploaded_file = st.file_uploader("📂 Upload CSV File（Optional）", type="csv")
if uploaded_file:
    try:
        up = pd.read_csv(uploaded_file)
        up.rename(columns={'Date': 'DateLabel', 'End Value': 'EndV'}, inplace=True)
        for c in ['DateLabel', 'EndV', 'Sell', 'Buy']:
            if c not in up.columns:
                up[c] = ""
        up = up[['DateLabel', 'EndV', 'Sell', 'Buy']].fillna("").astype(str)
        meta_df['DateLabel'] = meta_df['DateLabel'].astype(str)
        up['DateLabel'] = up['DateLabel'].astype(str)
        merged = pd.merge(meta_df, up, on='DateLabel', how='outer', suffixes=('', '_u'))
        for c in ['EndV', 'Sell', 'Buy']:
            merged[c] = merged[f"{c}_u"].combine_first(merged[c])
            merged.drop(columns=[f"{c}_u"], inplace=True)
        merged = merged[['DateLabel', 'EndV', 'Sell', 'Buy']].fillna("").astype(str)
        st.session_state.meta_df = merged
        meta_df = merged.copy()
        st.success("✅ CSVを反映しました")
    except Exception as e:
        st.error(f"CSV読み込み中にエラー: {e}")

# -------------------------
# 表データ編集
# -------------------------
st.subheader("📋 Edit Data Table")

# st.data_editor に key をつけてセッション状態に直接紐付け
edited_df = st.data_editor(
    "編集可能なテーブル",
    st.session_state.meta_df,
    key="editable_meta_df",
    num_rows="dynamic",
    use_container_width=True
)

# 編集された結果をセッション状態に反映
st.session_state.meta_df = edited_df.copy()
tmp_df = edited_df.copy()


# -------------------------
# UIコントロール
# -------------------------
marker_size_mode = st.selectbox(
    "マーカーサイズのモード / Marker Size Mode",
    ["固定サイズ Fix size", "段階サイズ Step size", "比例サイズ Proportional size"],
    index=1
)

chart_title = st.text_input("グラフタイトル / Chart Title",
                            value="My METΔPLΔNET Trading History")

# -------------------------
# CSVダウンロード
# -------------------------
csv_bytes = tmp_df.to_csv(index=False).encode("utf-8")
st.download_button("💾 Export CSV", data=csv_bytes, file_name="MetaplanetTradingData.csv", mime="text/csv")

# -------------------------
# グラフ描画用に安全に数値変換
# -------------------------
plot_df = tmp_df.copy()
plot_df['DateLabel_dt'] = pd.to_datetime(plot_df['DateLabel'], errors='coerce')

ev = pd.to_numeric(plot_df.get('EndV', 0), errors='coerce').fillna(0)
buy = pd.to_numeric(plot_df.get('Buy', 0), errors='coerce').fillna(0)
sell = pd.to_numeric(plot_df.get('Sell', 0), errors='coerce').fillna(0)

plot_df['Value_Buy'] = ev * buy
total_value_buy = plot_df['Value_Buy'].sum()
st.metric(label="💰 EndV × Buy 合計", value=f"{total_value_buy:,.0f}")

filtered_buy = plot_df[buy != 0]
filtered_sell = plot_df[sell != 0]

def get_marker_size(volume):
    try:
        volume = float(volume)
    except:
        return 60
    if marker_size_mode == "固定サイズ Fix size":
        return 50
    elif marker_size_mode == "段階サイズ Step size":
        if volume < 1000: return 100
        elif volume < 2000: return 140
        elif volume < 10000: return 180
        else: return 220
    else:  # 比例サイズ
        return max(volume * 0.02, 20)

# -------------------------
# プロット
# -------------------------
fig, ax = plt.subplots(figsize=(12, 6))
fig.patch.set_facecolor('black')
ax.set_facecolor('black')

ax.plot(plot_df['DateLabel_dt'], ev, label='End Value', color='orange', alpha=0.6)

for i in range(len(filtered_buy)):
    ax.scatter(filtered_buy['DateLabel_dt'].iloc[i], ev[filtered_buy.index[i]],
               s=get_marker_size(buy[filtered_buy.index[i]]), color='lightgreen',
               marker='^', alpha=0.8, label='Buy' if i == 0 else "")

for i in range(len(filtered_sell)):
    ax.scatter(filtered_sell['DateLabel_dt'].iloc[i], ev[filtered_sell.index[i]],
               s=get_marker_size(sell[filtered_sell.index[i]]), color='red',
               marker='v', alpha=0.8, label='Sell' if i == 0 else "")

ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
fig.autofmt_xdate()

ax.set_title(chart_title, color='white')
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
