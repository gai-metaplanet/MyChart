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

        # ↓ 表形式で表示・編集可能に（ここを追加）
        st.subheader("📋 表データの編集")
        edited_df = st.data_editor(meta_df, num_rows="dynamic", use_container_width=True)

        # 「保存」ボタンでCSVファイルとしてダウンロード（ここを追加）
        csv = edited_df.to_csv(index=False).encode("utf-8")
        st.download_button("💾 編集後CSVをダウンロード", data=csv, file_name="edited_data.csv", mime="text/csv")

        # 以下はグラフ描画用に使う DataFrame として edited_df を使用
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
        ax.plot(edited_df['DateLabel'], edited_df['EndV'], label='終値', color='blue', alpha=0.6)
        ax.plot(edited_df['DateLabel'], edited_df['mNAV'], label='mNAV', color='orange', linestyle='--')

        for i in range(len(buy_dates)):
            ax.scatter(buy_dates[i], filtered_buy['EndV'].iloc[i], s=get_marker_size(buy_volumes[i]),
                       color='green', alpha=0.5, label='買い' if i == 0 else "")

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
