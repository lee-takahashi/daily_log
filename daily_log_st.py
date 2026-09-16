import streamlit as st
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import json
import io
import zipfile

SCRIPT_VER = 'ver.260915_01'

# ---------- 設定 & データ準備 ----------
DATA_DIR = 'data'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)

FILES_PATH = {
    '健康記録': os.path.join(DATA_DIR, 'health_log.csv'),
    '読書記録': os.path.join(DATA_DIR, 'reading_log.csv'),
    '夕食記録': os.path.join(DATA_DIR, 'dinner_log.csv'),
    'ビデオ記録': os.path.join(DATA_DIR, 'video_log.csv'),
    '読書情報': os.path.join(DATA_DIR, 'book_info.json')
}

def save_to_csv(filename, data_list):
    record = ",".join(map(str, data_list)) + "\n"
    with open(filename, "a", encoding="utf-8") as f:
        f.write(record)

def load_book_info():
    with open(FILES_PATH['読書情報'], 'r') as f:
        return json.load(f)

def save_book_info(b_info):
    with open(FILES_PATH['読書情報'], 'w') as f:
        json.dump(b_info, f, ensure_ascii=False, indent=2)

# セッション状態の初期化（保存完了フラグ）
if "submitted_id" not in st.session_state:
    st.session_state.submitted_id = None

# 今日の日付表示
week_jp = ['月', '火', '水', '木', '金', '土', '日']
# now = datetime.now()
now_jst = datetime.now(ZoneInfo("Asia/Tokyo"))
youbi = week_jp[now_jst.weekday()]
today_str = now_jst.strftime(f"%Y年%m月%d日（{youbi}）")
today_yymmdd = now_jst.strftime(f"%y%m%d")

# ---------- UI構築 ----------
st.set_page_config(page_title='日々記録', layout="centered")

# サイドメニュー
#menu = st.sidebar.selectbox("機能を選択", ["メニュー", "健康記録", "読書記録", "夕食記録", "記録一覧"])
st.subheader('🏠 日々記録メニュー')
st.text(SCRIPT_VER)
st.write(f"今日は **{today_str}** です。")
menu = st.selectbox('メニュー', ['健康記録', '読書記録', '夕食記録', '記録一覧', 'ダウンロード'])
st.text('')

# メニューを切り替えたら保存フラグをリセット
if "prev_menu" not in st.session_state or st.session_state.prev_menu != menu:
    st.session_state.submitted_id = None
    st.session_state.prev_menu = menu

# ---------- 各画面の処理 ----------

if menu == '健康記録':
    st.subheader('健康記録')
    if st.session_state.submitted_id != "health":
        with st.form("health_form"):
            date_val = st.date_input('日付', now_jst)
            weight = st.text_input('体重 (kg)')
            bfp = st.text_input('体脂肪率 (%)')
            muscle = st.text_input('筋肉量 (kg)')
            bp_h = st.text_input('最高血圧')
            bp_l = st.text_input('最低血圧')
            pulse = st.text_input('脈拍数')
            if st.form_submit_button("保存"):
                youbi_1 = week_jp[date_val.weekday()]
                data = [date_val, youbi_1, weight, bfp, muscle, bp_h, bp_l, pulse]
                save_to_csv(FILES_PATH['健康記録'], data)
                st.session_state.last_data = data
                st.session_state.submitted_id = "health"
                st.rerun()
    else:
        st.success("✅ 健康データを保存しました！")
        st.dataframe(pd.DataFrame([st.session_state.last_data], columns=["日付", "曜日", "体重", "体脂肪率", "筋肉量", "最高血圧", "最低血圧", "脈拍"]).T)
        if st.button('終了'):
            st.session_state.submitted_id = None
            st.rerun()

elif menu == "読書記録":
    st.subheader('読書記録')
    if st.session_state.submitted_id != "reading":
        with st.form("reading_form"):
            date_val = st.date_input('日付', now_jst)
            read_mode = st.radio('入手区分', ('Audible', 'Book'), horizontal=True)
            book_info = load_book_info()
            st.text(book_info['Audible']['書名'] + '    ／    ' + book_info['Book']['書名'])
            rank = st.radio('ランク（1:中止、0:中断）', ('5', '4', '3', '2', '1', '0'), horizontal=True)
            st.markdown("<h3 style='color:blue;'>次の書籍</h3>", unsafe_allow_html=True)
            new_book = st.text_input('書名')
            get_from = st.text_input('図書館')
            if st.form_submit_button("保存"):
                if book_info[read_mode]['書名'] !=  "（なし）":
                    if rank != '1':
                        data = [book_info[read_mode]['書名'], book_info[read_mode]['入手'], book_info[read_mode]['開始日'], date_val, rank]
                    else:
                        data = [book_info[read_mode]['書名'], book_info[read_mode]['入手'], book_info[read_mode]['開始日'], '中止', rank]
                    save_to_csv(FILES_PATH['読書記録'], data)
                else:
                    data = ["（なし）",'','','','']
                if new_book != '':
                    book_info[read_mode]['書名'] = new_book
                    if read_mode == 'Audible':
                        get_from = 'Audible'
                    elif get_from == '':
                        get_from = 'BOOKOFF'
                    book_info[read_mode]['入手'] = get_from
                    book_info[read_mode]['開始日'] = date_val.strftime('%Y-%m-%d')
                else:
                    book_info[read_mode]['書名'] = "（なし）"
                    book_info[read_mode]['入手'] = ''
                    book_info[read_mode]['開始日'] = ''
                st.text(book_info)
                save_book_info(book_info)
                st.session_state.last_data = data
                st.session_state.submitted_id = "reading"
                st.rerun()
    else:
        st.success("✅ 読書記録を保存しました！")
        st.dataframe(pd.DataFrame([st.session_state.last_data], columns=['書名', '入手区分', '開始日', '終了日', 'ランク']).T)
        if st.button('終了'):
            st.session_state.submitted_id = None
            st.rerun()

elif menu == "夕食記録":
    st.subheader("夕食記録")
    if st.session_state.submitted_id != "dinner":
        with st.form("dinner_form"):
            date_val = st.date_input("日付", now_jst)
            cls = st.text_input("分類")
            main = st.text_input("主菜")
            sub1 = st.text_input("副菜1")
            sub2 = st.text_input("副菜2")
            sub3 = st.text_input("副菜3")
            if st.form_submit_button("保存"):
                youbi_1 = week_jp[date_val.weekday()]
                data = [date_val, youbi_1, cls, main, sub1, sub2, sub3]
                save_to_csv(FILES_PATH['夕食記録'], data)
                st.session_state.last_data = data
                st.session_state.submitted_id = "dinner"
                st.rerun()
    else:
        st.success("✅ 夕食の記録を保存しました！")
        st.dataframe(pd.DataFrame([st.session_state.last_data], columns=["日付", "曜日", "分類", "主菜", "副菜1", "副菜2", "副菜3"]).T)
        if st.button('終了'):
            st.session_state.submitted_id = None
            st.rerun()

elif menu == "記録一覧":
    st.title("記録一覧")
    tab1, tab2, tab3 = st.tabs(["健康", "読書", "夕食"])
    
    with tab1:
        if os.path.exists(FILES_PATH['健康記録']):
            df = pd.read_csv(FILES_PATH['健康記録'], names=["日付", "曜日", "体重", "体脂肪率", "筋肉量", "最高血圧", "最低血圧", "脈拍"])
#            st.dataframe(df.iloc[::-1], use_container_width=True)
            st.dataframe(df.iloc[::-1], width='stretch')
        else:
            st.write("データがありません。")

    with tab2:
        if os.path.exists(FILES_PATH['読書記録']):

            book_info = load_book_info()
            st.text('読書中： ' + book_info['Audible']['書名'] + '    ／    ' + book_info['Book']['書名'])

            df = pd.read_csv(FILES_PATH['読書記録'], names=["書名", "入手区分", "開始日", "終了日", "ランク"])
#            st.dataframe(df.iloc[::-1], use_container_width=True)
            st.dataframe(df.iloc[::-1], width='stretch')
        else:
            st.write("データがありません。")

    with tab3:
        if os.path.exists(FILES_PATH['夕食記録']):
            df = pd.read_csv(FILES_PATH['夕食記録'], names=["日付", "曜日", "分類", "主菜", "副菜1", "副菜2", "副菜3"])
#            st.dataframe(df.iloc[::-1], use_container_width=True)
            st.dataframe(df.iloc[::-1], width='stretch')
        else:
            st.write("データがありません。")

elif menu == "ダウンロード":
    st.subheader("データダウンロード")
    if st.session_state.submitted_id != "download":
        with open(FILES_PATH['健康記録'], 'r', encoding='utf-8') as f_in:
            health_log = f_in.read()
        with open(FILES_PATH['読書記録'], 'r', encoding='utf-8') as f_in:
            reading_log = f_in.read()
        with open(FILES_PATH['夕食記録'], 'r', encoding='utf-8') as f_in:
            dinner_log = f_in.read()
        with open(FILES_PATH['ビデオ記録'], 'r', encoding='utf-8') as f_in:
            video_log = f_in.read()
        with open(FILES_PATH['読書情報'], 'r', encoding='utf-8') as f_in:
            book_info = f_in.read()
        zip_buffer = io.BytesIO() # メモリ上にZIPファイルを作成
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr("health_log_" + today_yymmdd + ".csv", health_log)
            zip_file.writestr("reading_log_" + today_yymmdd + ".csv", reading_log)
            zip_file.writestr("dinner_log_" + today_yymmdd + ".csv", dinner_log)
            zip_file.writestr("video_log_" + today_yymmdd + ".csv", video_log)
            zip_file.writestr("book_info_" + today_yymmdd + ".json", book_info)
        zip_buffer.seek(0) # バッファのポインタを先頭に戻す
        if st.download_button(label="ダウンロード（zip）", data=zip_buffer, file_name="daily_log_" + today_yymmdd + ".zip"):
            st.session_state.submitted_id = "download"
            st.rerun()
    else:
        st.success("✅ データをダウンロードしました！")
        if st.button('終了'):
            st.session_state.submitted_id = None
            st.rerun()

#2026-04-09 07:11:35.543 Please replace `use_container_width` with `width`.
#`use_container_width` will be removed after 2025-12-31.
#For `use_container_width=True`, use `width='stretch'`. For `use_container_width=False`, use `width='content'`.

