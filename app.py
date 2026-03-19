import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, date
import os

# --- 1. 基础页面配置 ---
st.set_page_config(page_title="花大爷 × 不差儿", layout="wide", initial_sidebar_state="collapsed")

# --- 2. 数据库连接 (写死 Key 确保权限) ---
URL = "https://hjrvdusefkjtmucsreeq.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhqcnZkdXNlZmtqdG11Y3NyZWVxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3Mzg0MzM2MiwiZXhwIjoyMDg5NDE5MzYyfQ.n7TPfrBJYeo9ZKIIEoOEPIRscmR2joGqHwqNw5-Yqsk"

try:
    supabase: Client = create_client(URL, KEY)
except:
    st.error("数据库连接失败")

# --- 3. 强制手机端双列 & 蒂芙尼蓝 UI ---
st.markdown("""
    <style>
    .stApp { background-color: #F0F9F9; }
    /* 核心：强制移动端不折叠列 */
    [data-testid="column"] {
        width: 50% !important;
        flex: 1 1 50% !important;
        min-width: 50% !important;
        padding: 5px !important;
    }
    .main-card {
        background: white; border-radius: 15px; padding: 12px;
        border-top: 5px solid #0ABAB5;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }
    .stMetric { background: #f8fefd; padding: 10px; border-radius: 10px; }
    .stButton>button { background-color: #0ABAB5; color: white; border-radius: 10px; width: 100%; }
    h3 { font-size: 1.1rem !important; color: #088F8A; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. 辅助计算工具 ---
def calc_metrics(w, h, age):
    bmi = round(w / ((h/100)**2), 1)
    bmr = int(10 * w + 6.25 * h - 5 * age - 161) # 女性公式
    return bmi, bmr

# --- 5. 登录逻辑 ---
if 'user_role' not in st.session_state:
    with st.form("login"):
        st.subheader("🎨 开启双人基地")
        role = st.selectbox("👤 你是谁？", ["不差儿", "花大爷"])
        age = st.number_input("年龄", 1, 100, 24)
        h = st.number_input("身高(cm)", 100, 250, 163)
        w = st.number_input("体重(kg)", 30.0, 200.0, 61.5)
        if st.form_submit_button("🚀 进入系统"):
            # 尝试同步基础资料
            try:
                supabase.table("users").upsert({"name":role, "age":age, "height":h, "weight":w, "gender":"女"}).execute()
            except: pass
            st.session_state.user_role = role
            st.session_state.u_info = {"age":age, "h":h}
            st.rerun()
    st.stop()

# --- 6. 首页内容 ---
role_me = st.session_state.user_role
view_date = st.date_input("📅 选择日期", date.today())

col_left, col_right = st.columns(2)

def render_user_column(name, col, is_me):
    with col:
        st.markdown(f"<h3>{'👩‍𝓠' if name=='不差儿' else '👨‍🦳'} {name}</h3>", unsafe_allow_html=True)
        
        # 获取该用户该日期的数据
        try:
            res = supabase.table("daily_logs").select("*").eq("user_name", name).eq("date", str(view_date)).execute()
            log = res.data[0] if res.data else {}
        except: log = {}

        # 身体指标卡片
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        w_val = log.get('weight', "--")
        f_val = log.get('body_fat', "--")
        st.metric("体重 (kg)", w_val)
        st.caption(f"体脂率: {f_val}%")
        
        if is_me:
            with st.expander("📝 录入今日"):
                new_w = st.number_input("体重", value=60.0, key=f"w_{name}")
                new_f = st.number_input("体脂", value=20.0, key=f"f_{name}")
                if st.button("更新数据", key=f"b_{name}"):
                    supabase.table("daily_logs").upsert({
                        "user_name": name, "date": str(view_date), "weight": new_w, "body_fat": new_f
                    }).execute()
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # 留言板
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        st.write("💬 **TA的留言**")
        st.info(log.get('note', "暂无留言"))
        if is_me:
            msg = st.text_input("给对方留言", key=f"m_{name}")
            if st.button("发布", key=f"mb_{name}"):
                supabase.table("daily_logs").upsert({
                    "user_name": name, "date": str(view_date), "note": msg
                }).execute()
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# 渲染左右两列
render_user_column("不差儿", col_left, is_me=(role_me == "不差儿"))
render_user_column("花大爷", col_right, is_me=(role_me == "花大爷"))

if st.button("退出登录"):
    del st.session_state.user_role
    st.rerun()
