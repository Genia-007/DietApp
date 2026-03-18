import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, date, timedelta
import random
import os
from PIL import Image
import base64

# --- 1. 页面配置与图片路径优化 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(current_dir, "app_icon.png")

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# 设置页面
try:
    if os.path.exists(icon_path):
        img_b64 = get_base64_of_bin_file(icon_path)
        st.set_page_config(
            page_title="花大爷 × 不差儿",
            page_icon=f"data:image/png;base64,{img_b64}",
            layout="wide"
        )
    else:
        st.set_page_config(page_title="花大爷 × 不差儿", page_icon="🎨", layout="wide")
except Exception:
    # 修复：确保即使图片读取失败，页面配置也能正常初始化
    st.set_page_config(page_title="花大爷 × 不差儿", layout="wide")

# --- 2. 蒂芙尼蓝 UI 注入 ---
st.markdown("""
    <style>
    .stApp { background-color: #F0F9F9; }
    [data-testid="column"] { 
        background: white; border-radius: 15px; padding: 15px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .main-card { border-top: 5px solid #0ABAB5; padding: 10px; }
    .stButton>button { background-color: #0ABAB5; color: white; border-radius: 10px; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 顶部显示图标 ---
if os.path.exists(icon_path):
    try:
        image = Image.open(icon_path)
        st.image(image, width=100)
    except Exception as e:
        st.error(f"图片加载失败: {e}")

# --- 4. Supabase 初始化与操作封装 ---
SUPABASE_URL = "https://hjrvdusefkjtmucsreeq.supabase.co"
SUPABASE_KEY = "sb_publishable_yDO1V8a3qYz8YPSzXSHdWA_mhpQG8QF"

try:
    # 修复：确保 create_client 括号闭合完整
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"数据库连接初始化失败: {e}")
    st.stop()

# --- 5. 登录初始化 ---
# 修复：确认此 if 语句前没有任何未闭合的括号或缩进错误
if 'user_role' not in st.session_state:
    with st.form("login"):
        st.subheader("🎨 身份初始化")
        role = st.selectbox("👤 你是谁？", ["不差儿", "花大爷"])
        age = st.number_input("年龄", 1, 100, 24)
        h = st.number_input("身高(cm)", 100, 250, 165)
        w = st.number_input("体重(kg)", 30, 200, 60)
        
        if st.form_submit_button("🚀 进入系统"):
            # 修复：upsert 内部的字典大括号和函数括号必须成对
            try:
                supabase.table("users").upsert({
                    "name": role, 
                    "age": age, 
                    "height": h, 
                    "weight": w, 
                    "gender": "女"
                }, on_conflict="name").execute()
                st.session_state.user_role = role
                st.rerun()
            except Exception as e:
                st.error(f"保存失败: {e}")
    st.stop()

# --- 6. 首页布局 ---
role_me = st.session_state.user_role
view_date = st.date_input("📅 选择日期", date.today())

col_left, col_right = st.columns(2)

def render_side(name, col, is_me):
    with col:
        st.markdown(f"### {'👩‍𝓠' if name=='不差儿' else '👨‍🦳'} {name}")
        
        # 修复：查询语句末尾的 .execute() 括号
        try:
            res = supabase.table("daily_logs").select("*").eq("user_name", name).eq("date", str(view_date)).execute()
            data = res.data[0] if res.data else {}
        except:
            data = {}
        
        st.metric("体重", f"{data.get('weight', '--')} kg")
        
        if is_me:
            with st.expander("录入数据"):
                nw = st.number_input("今日体重", value=60, key=f"w_{name}")
                if st.button("更新体重", key=f"btn_w_{name}"):
                    # 修复：upsert 函数调用括号闭合
                    supabase.table("daily_logs").upsert({
                        "user_name": name, 
                        "date": str(view_date), 
                        "weight": nw
                    }, on_conflict="user_name,date").execute()
                    st.rerun()
        else:
            st.info(data.get('note', "暂无记录"))

# 渲染对垒
render_side("不差儿", col_left, is_me=(role_me == "不差儿"))
render_side("花大爷", col_right, is_me=(role_me == "花大爷"))
