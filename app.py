import streamlit as st
from supabase import create_client, Client
import os

# 1. 页面配置
st.set_page_config(page_title="花大爷 × 不差儿", layout="wide")

# 2. 从 Secrets 读取配置
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("❌ Secrets 配置读取失败，请检查 Streamlit 后台设置")
    st.stop()

# 3. 登录逻辑
if 'user_role' not in st.session_state:
    with st.form("login_form"):
        st.subheader("🎨 开启双人打卡基地")
        role = st.selectbox("👤 你是谁？", ["不差儿", "花大爷"])
        age = st.number_input("年龄", 1, 100, 24)
        h = st.number_input("身高(cm)", 100, 250, 163)
        w = st.number_input("初始体重(kg)", 30.0, 200.0, 61.5)
        
        if st.form_submit_button("🚀 进入系统"):
            try:
                # 核心修复：先尝试插入，如果冲突则不报错（或改用简单 insert 测试）
                user_data = {
                    "name": role, 
                    "age": int(age), 
                    "height": int(h), 
                    "weight": float(w), 
                    "gender": "女"
                }
                # 这里我们改用 upsert，并确保 on_conflict 对应表的主键
                supabase.table("users").upsert(user_data).execute()
                
                st.session_state.user_role = role
                st.rerun()
            except Exception as e:
                # 打印出具体的错误内容，方便我们调试
                st.error(f"❌ 系统对接失败！错误详情：{e}")
    st.stop()

# 4. 进入系统后的界面
st.balloons() # 庆祝一下！
st.success(f"🎊 权限彻底解锁！欢迎进入：{st.session_state.user_role}")

if st.button("退出登录"):
    del st.session_state.user_role
    st.rerun()
