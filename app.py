import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, date, timedelta
import random
import os
from PIL import Image
import base64

# --- 1. 页面配置 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
# 确保这里名字和你 GitHub 里的图片名一致
icon_filename = "app_icon.png" 
icon_path = os.path.join(current_dir, icon_filename)

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

try:
    if os.path.exists(icon_path):
        img_b64 = get_base64_of_bin_file(icon_path)
        st.set_page_config(page_title="花大爷 × 不差儿", page_icon=f"data:image/png;base64,{img_b64}", layout="wide")
    else:
        st.set_page_config(page_title="花大爷 × 不差儿", page_icon="🎨", layout="wide")
except:
    st.set_page_config(page_title="花大爷 × 不差儿", layout="wide")

# --- 2. Supabase 初始化 ---
SUPABASE_URL = "https://hjrvdusefkjtmucsreeq.supabase.co"
SUPABASE_KEY = "sb_publishable_yDO1V8a3qYz8YPSzXSHdWA_mhpQG8QF"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 3. 登录与初始化 ---
# 注意：这里就是你报错的地方，确保它左边没有多余空格
if 'user_role' not in st.session_state:
    if os.path.exists(icon_path):
        st.image(Image.open(icon_path), width=100)
    with st.form("login"):
        st.subheader("🎨 身份初始化")
        role = st.selectbox("👤 你是谁？", ["不差儿", "花大爷"])
        age = st.number_input("年龄", 1, 100, 24)
        h = st.number_input("身高(cm)", 100, 250, 165)
        w = st.number_input("体重(kg)", 30, 200, 60)
        if st.form_submit_button("🚀 进入系统"):
            supabase.table("users").upsert({"name": role, "age": age, "height": h, "weight": w, "gender": "女"}).execute()
            st.session_state.user_role = role
            st.rerun()
    st.stop()

# --- 4. 首页渲染 ---
role_me = st.session_state.user_role
view_date = st.date_input("📅 选择日期", date.today())
col_left, col_right = st.columns(2)

def render_side(name, col, is_me):
    with col:
        st.markdown(f"### {'👩‍𝓠' if name=='不差儿' else '👨‍🦳'} {name}")
        res = supabase.table("daily_logs").select("*").eq("user_name", name).eq("date", str(view_date)).execute()
        data = res.data[0] if res.data else {}
        
        st.metric("体重", f"{data.get('weight', '--')} kg")
        if is_me:
            with st.expander("录入"):
                nw = st.number_input("今日体重", value=60, key=f"w_{name}")
                if st.button("更新", key=f"btn_{name}"):
                    supabase.table("daily_logs").upsert({"user_name": name, "date": str(view_date), "weight": nw}, on_conflict="user_name,date").execute()
                    st.rerun()
        else:
            st.info(data.get('note', "暂无记录"))

render_side("不差儿", col_left, is_me=(role_me == "不差儿"))
render_side("花大爷", col_right, is_me=(role_me == "花大爷"))
