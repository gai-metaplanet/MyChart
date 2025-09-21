import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import yfinance as yf

st.title("My METΔPLΔNET Trading History")

DEFAULT_CSV_PATH = "data/3350 - default.csv"

# -------------------------
# helpers
# -------------------------
def load_default_csv():
    try:
        df = pd.read_csv(DEFAULT_CSV_PATH)
        df.rename(columns={'Date': 'DateLabel', 'End Value': 'EndV'}, inplace=True)
    except Exception:
        # 必要な列が最低限ある空DFを返す
        df = pd.DataFrame(columns=['DateLabel', 'EndV', 'Sell', 'Buy'])
    # 内部は文字列で保持（編集しやすくするため）
    for c in ['DateLabel', 'EndV', 'Sell', 'Buy']:
        if c not in df.columns:
            df[c] = ""
    df = df[['DateLabel', 'EndV', 'Sell', 'Buy']]
    df = df.astype(str)
    return df

def fetch_stock_history():
    try:
        ticker = yf.Ticker("3350.T")
        df = ticker.history(period="3mo")
        df.reset_index(inplace=True)
        df['DateLabel'] = df['Date'].dt.strftime('%Y-%m-%d')  # 文字列で返す
        df = df[['DateLabel', 'Close']].rename(columns={'Close': 'EndV'})
        # Ensure columns exist and are strings
        df['Sell'] = ""
        df['Buy'] = ""
        return df.astype(str)
    except Exception:
        return pd.DataFrame(columns=['DateLabel', 'EndV', 'Sell', 'Buy']).astype(str)

# -------------------------
# 初期ロード（session_stateで保持）
# -------------------------
if "meta_df" not in st.session_state:
    base_df = load_default_csv()
    stock_df = fetch_stock_history()

    # defaultに存在しない日付を補完
    existing_dates = set(base_df['DateLabel'])
    new_dates_df = stock_df[~stock_df['DateLabel'].isin(existing_dates)].copy()

    combined = pd.concat([base_df, new_dates_df], ignore_index=True)
    combined = combined[['DateLabel', 'EndV', 'Sell', 'Buy']]
    # すべて文字列で保持（編集を優先）
    combined = combined.fillna("").astype(str)

    st.session_state.meta_df = combined

# 作業用コピー
meta_df = st.session_state.meta_df.copy()

# -------------------------
# CSVアップロード（文字列で統一してマージ）
# -------------------------
uploaded_file = st.file_uploader("📂 Upload CSV File（任意 / Optional）", type="csv")
if uploaded_file:
    try:
        up = pd.read_csv(uploaded_file)
        up.rename(columns={'Date': 'DateLabel', 'End Value': 'EndV'}, inplace=True)
        # 必要列を確保し、文字列化
        for c in ['DateLabel', 'EndV', 'Sell', 'Buy']:
            if c not in up.columns:
                up[c] = ""
        up = up[['DateLabel', 'EndV', 'Sell', 'Buy']].fillna("").astype(str)

        # 両方を文字列で統一してから merge
        meta_df['DateLabel'] = meta_df['DateLabel'].astype(str)
        up['DateLabel'] = up['DateLabel'].astype(str)

        merged = pd.merge(meta_df, up, on='DateLabel', how='outer', suffixes=('', '_u'))

        # アップロード側の値があれば優先（ただしすべて文字列）
        for c in ['EndV', 'Sell', 'Buy']:
            if f"{c}_u" in merged.columns:
                merged[c] = merged[f"{c}_u"].combine_first(merged[c])
                merged.drop(columns=[f"{c}_u"], inplace=True)
        # 欠損を空文字で埋めて文字列に
        merged = merged[['DateLabel', 'EndV', 'Sell', 'Buy']].fillna("").astype(str)

        st.session_state.meta_df = merged
        meta_df = merged.copy()
        st.success("✅ アップロードCSVを反映しました")
    except Exception as e:
        st.error(f"アップロードCSVの読み込み中にエラー: {e}")

# -------------------------
# 表データ編集（内部は文字列で渡す）
# -------------------------
st.subheader("📋 表データの編集 / Edit Data Table (編集はテキスト形式で行ってください)")
# 編集可能にするためにすべて文字列化してから渡す
editable_df = meta_df.copy().astype(str)
edited_df = st.data_editor(editable_df, num_rows="dynamic", use_container_width=True)
# 編集結果を session_state に反映（文字列のまま）
st.session_state.meta_df = edited_df.copy()
tmp_df = edited_df.copy()

# -------------------------
# UIコントロール
# -------------------------
marker_size_mode = st.selectbox(
    "マーカーサイズのモードを選択 / Marker Size Mode",
    ["固定サイズ Fix size", "段階サイズ Step size", "比例サイズ Proportional size"],
    index=1
)

chart_title = st.text_input("グラフタイトルを入力 / Enter chart title",
                            value="My METΔPLΔNET Trading History")

# ダウンロードボタン
csv_bytes = tmp_df.to_csv(index=False).encode("utf-8")
st.download_button("💾 編集後CSVをダウンロード / Export the updated CSV",
                   data=csv_bytes, file_name="MetaplanetTradingData.csv", mime="text/csv")

# -------------------------
# グラフ描画前：安全に数値化して計算
# -------------------------
plot_df = tmp_df.copy()

# DateLabel を datetime に変換（描画用）
plot_df['DateLabel_dt'] = pd.to_datetime(plot_df['DateLabel'], errors='coerce')

# EndV と Buy が無ければ列を作る（編集で消された場合に備える）
if 'EndV' not in plot_df.columns:
    plot_df['EndV'] = ""
if 'Buy' not in plot_df.columns:
    plot_df['Buy'] = ""

# 数値化（問題がある値は NaN → 0 に）
try:
    ev = pd.to_numeric(plot_df['EndV'], errors='coerce').fillna(0)
except Exception as e:
    st.error(f"EndV の数値変換でエラー: {e}")
    ev = pd.Series(0, index=plot_df.index)

try:
    buy = pd.to_numeric(plot_df['Buy'], errors='coerce').fillna(0)
except Exception as e:
    st.error(f"Buy の数値変換でエラー: {e}")
    buy = pd.Series(0, index=plot_df.index)

# 明示的に掛け算（ここで安全に計算できる）
try:
    plot_df['Value_Buy'] = ev * buy
except Exception as e:
    st.error(f"EndV×Buy の計算でエラー: {e}")
    plot_df['Value_Buy'] = 0

total_value_buy = float(plot_df['Value_Buy'].sum())

# 表示（metric）
st.metric(label="💰 EndV × Buy 合計", value=f"{total_value_buy:,.0f}")

# -------------------------
# プロット用に必要な列を plot_df に戻す
# -------------------------
# グラフには datetime 列と数値 EndV を使う
plot_df['EndV_num'] = ev
plot_df['Sell_num'] = pd.to_numeric(plot_df.get('Sell', 0), errors='coerce').fillna(0)
plot_df['Buy_num'] = buy

filtered_buy = plot_df[plot_df['Buy_num'] != 0]
filtered_sell = plot_df[plot_df['Sell_num'] != 0]

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
    else:  # 比例
        scale = 0.02
        return max(volume * scale, 20)

# -------------------------
# プロット
# -------------------------
fig, ax = plt.subplots(figsize=(12, 6))
fig.patch.set_facecolor('black')
ax.set_facecolor('black')

ax.plot(plot_df['DateLabel_dt'], plot_df['EndV_num'], label='End Value', color='orange', alpha=0.6)

# buy markers
for i in range(len(filtered_buy)):
    ax.scatter(filtered_buy['DateLabel_dt'].iloc[i], filtered_buy['EndV_num'].iloc[i],
               s=get_marker_size(filtered_buy['Buy_num'].iloc[i]), marker='^', alpha=0.8,
               label='Buy' if i == 0 else "")

# sell markers
for i in range(len(filtered_sell)):
    ax.scatter(filtered_sell['DateLabel_dt'].iloc[i], filtered_sell['EndV_num'].iloc[i],
               s=get_marker_size(filtered_sell['Sell_num'].iloc[i]), marker='v', alpha=0.8,
               label='Sell' if i == 0 else "")

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
