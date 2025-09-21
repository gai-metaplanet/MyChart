import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import yfinance as yf

st.set_page_config(layout="wide")
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
# 初期ロード（session_state に1度だけ入れる）
# -------------------------
if "meta_df" not in st.session_state:
    base_df = load_default_csv()
    stock_df = fetch_stock_history()
    existing_dates = set(base_df['DateLabel'])
    new_dates_df = stock_df[~stock_df['DateLabel'].isin(existing_dates)].copy()
    combined_df = pd.concat([base_df, new_dates_df], ignore_index=True)
    combined_df = combined_df[['DateLabel', 'EndV', 'Sell', 'Buy']].fillna("").astype(str)
    st.session_state.meta_df = combined_df

# 編集用バッファ（編集中の内容はここだけ触る）
if "editable_meta_df" not in st.session_state:
    st.session_state.editable_meta_df = st.session_state.meta_df.copy()

# -------------------------
# CSVアップロード（アップロード時は saved と buffer を同期）
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

        # merge into saved meta_df
        merged = pd.merge(st.session_state.meta_df, up, on='DateLabel', how='outer', suffixes=('', '_u'))
        for c in ['EndV', 'Sell', 'Buy']:
            merged[c] = merged[f"{c}_u"].combine_first(merged[c])
            merged.drop(columns=[f"{c}_u"], inplace=True)
        merged = merged[['DateLabel', 'EndV', 'Sell', 'Buy']].fillna("").astype(str)

        st.session_state.meta_df = merged
        st.session_state.editable_meta_df = merged.copy()  # 編集バッファも同期
        st.success("✅ CSVを反映しました（保存済みデータにマージし、編集バッファも更新）")
    except Exception as e:
        st.error(f"CSV読み込み中にエラー: {e}")

# -------------------------
# 表データ編集（編集はバッファで行い、明示的に保存）
# -------------------------
st.subheader("📋 Edit Data Table (編集は下のボタンで保存してください)")

# st.data_editor の key は 'editable_meta_df' に固定（バッファと紐づけ）
edited_df = st.data_editor(
    st.session_state.editable_meta_df,
    key="editable_meta_df",
    num_rows="dynamic",
    use_container_width=True
)

# 保存 / 元に戻す ボタン
col1, col2, _ = st.columns([1,1,8])
if col1.button("💾 Save changes"):
    # Save: バッファ → meta_df（グラフ等は保存済みデータを参照）
    st.session_state.meta_df = st.session_state.editable_meta_df.copy()
    st.success("編集内容を保存しました（グラフ等に反映されます）")

if col2.button("↩️ Revert to last saved"):
    # Revert: meta_df → バッファ（編集内容を破棄）
    st.session_state.editable_meta_df = st.session_state.meta_df.copy()
    st.experimental_rerun()

# CSV エクスポート（保存済みデータをエクスポート）
csv_bytes = st.session_state.meta_df.to_csv(index=False).encode("utf-8")
st.download_button("💾 Export CSV (saved data)", data=csv_bytes, file_name="MetaplanetTradingData.csv", mime="text/csv")

# -------------------------
# グラフ描画用に安全に数値変換（保存済みデータを表示）
# -------------------------
tmp_df = st.session_state.meta_df.copy()
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

marker_size_mode = st.selectbox(
    "マーカーサイズのモード / Marker Size Mode",
    ["固定サイズ Fix size", "段階サイズ Step size", "比例サイズ Proportional size"],
    index=1
)

chart_title = st.text_input("グラフタイトル / Chart Title",
                            value="My METΔPLΔNET Trading History")

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
