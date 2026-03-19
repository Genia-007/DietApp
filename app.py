import streamlit as st
from supabase import create_client, Client
import os
from PIL import Image

# 1. 基础配置
st.set_page_config(page_title="花大爷 × 不差儿", layout="wide")

# 2. 读取保险柜（重点！）
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("Secrets 没配对，请在 Streamlit 后台检查 SUPABASE_URL 和 SUPABASE_KEY")
    st.stop()

# 3. 登录逻辑
if 'user_role' not in st.session_state:
    with st.form("login"):
        st.subheader("🎨 开启双人打卡基地")
        role = st.selectbox("👤 你是谁？", ["不差儿", "花大爷"])
        age = st.number_input("年龄", 1, 100, 24)
        h = st.number_input("身高(cm)", 100, 250, 163)
        w = st.number_input("初始体重(kg)", 30.0, 200.0, 61.5)
        if st.form_submit_button("🚀 进入系统"):
            # 存入数据
            supabase.table("users").upsert({
                "name": role, "age": age, "height": h, "weight": w, "gender": "女"
            }, on_conflict="name").execute()
            st.session_state.user_role = role
            st.rerun()
    st.stop()

# 4. 进入系统后的内容
st.success(f"🎉 欢迎进入，{st.session_state.user_role}！权限已解锁。")
if st.button("重新登录"):
    del st.session_state.user_role
    st.rerun()
