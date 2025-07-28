import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.dates as mdates

# フォントパス
font_path = "fonts/IPAexGothic.ttf"
font_prop = fm.FontProperties(fname=font_path)
plt.rcParams['font.family'] = font_prop.get_name()


st.title("売買タイミング可視化ツール")

# ファイルアップロード
uploaded_file = st.file_uploader("CSVファイルをアップロードしてください", type="csv")

if uploaded_file is not None:
    try:
        # アップロードされたCSV読み込み
        meta = pd.read_csv(uploaded_file)

        # 初期整形
        meta_index = {
            'DateLabel': meta['日付'].tolist(),
            'EndV': meta['終値'].tolist(),
            '売り': meta['売り'].tolist(),
            '買い': meta['買い'].tolist(),
            'mNAV': meta['mNAV'].tolist(),
        }
        meta_df = pd.DataFrame(meta_index)

        # ======= 🔽 株価データ補完処理 🔽 =======
        ticker = yf.Ticker("3350.T")
        df = ticker.history(period="1y")
        df_close = df[['Close']].copy()
        df_close.reset_index(inplace=True)
        df_close['DateLabel'] = df_close['Date'].dt.strftime('%Y-%m-%d')

        # CSVに存在しない日付を抽出し、空の行で追加
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

        # Close列を一時的にマージして EndV を補完
        meta_df = pd.merge(meta_df, df_close[['DateLabel', 'Close']], on='DateLabel', how='left')
        meta_df['EndV'] = meta_df['Close'].combine_first(meta_df['EndV'])
        meta_df.drop(columns=['Close'], inplace=True)

        # ソートして並び替え
        meta_df.sort_values('DateLabel', inplace=True)
        meta_df.reset_index(drop=True, inplace=True)

        # 欠損除去（基本整備）
        # meta_df = meta_df.dropna(subset=["DateLabel", "EndV", "売り", "買い", "mNAV"])
        meta_df['売り'] = meta_df['売り'].str.replace(',', '').astype(float)
        meta_df['買い'] = meta_df['買い'].str.replace(',', '').astype(float)
        meta_df['売り'] = meta_df['売り'].fillna(0)
        meta_df['買い'] = meta_df['買い'].fillna(0)
        
        # ======= 🔽 表編集 & 保存 🔽 =======
        st.subheader("📋 表データの編集")
        edited_df = st.data_editor(meta_df, num_rows="dynamic", use_container_width=True)

        # ダウンロードボタン
        csv = edited_df.to_csv(index=False).encode("utf-8")
        st.download_button("💾 編集後CSVをダウンロード", data=csv, file_name="edited_data.csv", mime="text/csv")

        edited_df['DateLabel'] = pd.to_datetime(edited_df['DateLabel'])

        # ======= 🔽 グラフ描画 🔽 =======
        edited_df['売り'] = edited_df['売り'].astype(str).str.replace(',', '').astype(float)
        edited_df['買い'] = edited_df['買い'].astype(str).str.replace(',', '').astype(float)
        edited_df['mNAV'] = edited_df['mNAV'].fillna(0)
        edited_df['売り'] = edited_df['売り'].fillna(0)
        edited_df['買い'] = edited_df['買い'].fillna(0)

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
        # 背景を黒に
        fig.patch.set_facecolor('black')
        ax.set_facecolor('black')
        ax.plot(edited_df['DateLabel'], edited_df['EndV'], label='終値', color='orange', alpha=0.6)
        # ax.plot(edited_df['DateLabel'], edited_df['mNAV'], label='mNAV', color='orange', linestyle='--')

        for i in range(len(buy_dates)):
            ax.scatter(buy_dates[i], filtered_buy['EndV'].iloc[i], s=get_marker_size(buy_volumes[i]),
                       color='green', alpha=0.5, label='買い' if i == 0 else "")

        for i in range(len(sell_dates)):
            ax.scatter(sell_dates[i], filtered_sell['EndV'].iloc[i], s=get_marker_size(sell_volumes[i]),
                       color='red', alpha=0.5, label='売り' if i == 0 else "")

        # 日付の形式を整える（横軸）
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))  # ← 月ごと
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        fig.autofmt_xdate()
        ax.set_title("売買とmNAVの推移")
        ax.set_xlabel("日付")
        ax.set_ylabel("価格")
        ax.legend()
        ax.grid(True)

        st.pyplot(fig)

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
