import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("売買タイミング可視化ツール")

# ファイルアップロード
uploaded_file = st.file_uploader("CSVファイルをアップロードしてください", type="csv")

if uploaded_file is not None:
    try:
        meta = pd.read_csv(uploaded_file)

        meta_index = {
            'DateLabel': meta['日付'].tolist(),
            'EndV': meta['終値'].tolist(),
            '売り': meta['売り'].tolist(),
            '買い': meta['買い'].tolist(),
            'mNAV': meta['mNAV'].tolist(),
        }

        meta_df = pd.DataFrame(meta_index)

        meta_df['売り'] = meta_df['売り'].astype(str).str.replace(',', '').astype(float)
        meta_df['買い'] = meta_df['買い'].astype(str).str.replace(',', '').astype(float)
        meta_df['mNAV'] = meta_df['mNAV'].fillna(0)

        meta_df['売り'] = meta_df['売り'].fillna(0)
        meta_df['買い'] = meta_df['買い'].fillna(0)

        filtered_buy = meta_df[meta_df['買い'] != 0]
        filtered_sell = meta_df[meta_df['売り'] != 0]

        buy_dates = filtered_buy['DateLabel'].tolist()
        buy_volumes = filtered_buy['買い'].tolist()

        sell_dates = filtered_sell['DateLabel'].tolist()
        sell_volumes = filtered_sell['売り'].tolist()

        # マーカーサイズ関数
        def get_marker_size(volume):
            if volume < 1000:
                return 60
            elif volume < 2000:
                return 100
            elif volume < 10000:
                return 140
            else:
                return 180

        # 描画
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(meta_df['DateLabel'], meta_df['EndV'], label='終値', color='blue', alpha=0.6)
        ax.plot(meta_df['DateLabel'], meta_df['mNAV'], label='mNAV', color='orange', linestyle='--')

        # 買いマーカー
        for i in range(len(buy_dates)):
            ax.scatter(buy_dates[i], filtered_buy['EndV'].iloc[i], s=get_marker_size(buy_volumes[i]),
                       color='green', alpha=0.5, label='買い' if i == 0 else "")

        # 売りマーカー
        for i in range(len(sell_dates)):
            ax.scatter(sell_dates[i], filtered_sell['EndV'].iloc[i], s=get_marker_size(sell_volumes[i]),
                       color='red', alpha=0.5, label='売り' if i == 0 else "")

        ax.set_title("売買とmNAVの推移")
        ax.set_xlabel("日付")
        ax.set_ylabel("価格")
        ax.legend()
        ax.grid(True)

        st.pyplot(fig)

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
