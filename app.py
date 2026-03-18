import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, date, timedelta
import random
import os
from PIL import Image
import base64

# --- 1. 页面配置与图片路径优化 ---
# 获取当前文件所在的绝对路径，确保在 Streamlit Cloud 也能找到图片
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
else:
    st.warning("未找到 app_icon.png，请检查文件名和路径")

# --- 4. Supabase 初始化与操作封装 ---
SUPABASE_URL = "https://hjrvdusefkjtmucsreeq.supabase.co"
SUPABASE_KEY = "sb_publishable_yDO1V8a3qYz8YPSzXSHdWA_mhpQG8QF"

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"数据库连接初始化失败: {e}")
    st.stop()

def safe_db_operation(func):
    """数据库操作装饰器，增加 try-except 保护"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            st.error(f"⚠️ 数据库操作异常: {e}")
            return None
    return wrapper

@safe_db_operation
def upsert_user(data):
    return supabase.table("users").upsert(data, on_conflict="name").execute()

@safe_db_operation
def get_logs(name, log_date):
    res = supabase.table("daily_logs").select("*").eq("user_name", name).eq("date", str(log_date)).execute()
    return res.data[0] if res.data else {}

@safe_ai_op := lambda: random.randint(300, 700)

# --- 5. 登录初始化 ---
if 'user_role' not in st.session_state:
    with st.form("login"):
        st.subheader("🎨 身份初始化")
        role = st.selectbox("👤 你是谁？", ["不差儿", "花大爷"])
        age = st.number_input("年龄", 1, 100, 24)
        h = st.number_input("身高(cm)", 100, 250, 165)
        w = st.number_input("体重(kg)", 30, 200, 60)
        if st.form_submit_button("🚀 进入系统"):
            upsert_user({"name": role, "age": age, "height": h, "weight": w, "gender": "女"})
            st.session_state.user_role = role
            st.rerun()
    st.stop()

# --- 6. 首页布局 ---
role_me = st.session_state.user_role
view_date = st.date_input("📅 选择日期", date.today())

col_left, col_right = st.columns(2)

def render_side(name, col, is_me):
    with col:
        st.markdown(f"### {'👩‍𝓠' if name=='不差儿' else '👨‍🦳'} {name}")
        data = get_logs(name, view_date)
        
        # 身体指标卡片
        with st.container():
            st.write("**📊 身体指标**")
            st.metric("体重", f"{data.get('weight', '--')} kg")
            if is_me:
                with st.expander("录入数据"):
                    nw = st.number_input("今日体重", value=60, key=f"w_{name}")
                    if st.button("更新体重", key=f"btn_w_{name}"):
                        supabase.table("daily_logs").upsert({
                            "user_name": name, "date": str(view_date), "weight": nw
                        }, on_conflict="user_name,date").execute()
                        st.rerun()

        # 心得留言
        st.info(data.get('note', "暂无记录"))
        if is_me:
            new_note = st.text_input("给对方留言", key=f"n_{name}")
            if st.button("发布心得", key=f"btn_n_{name}"):
                supabase.table("daily_logs").upsert({
                    "user_name": name, "date": str(view_date), "note": new_note
                }, on_conflict="user_name,date").execute()
                st.rerun()

# 左右对垒渲染
render_side("不差儿", col_left, is_me=(role_me == "不差儿"))
render_side("花大爷", col_right, is_me=(role_me == "花大爷"))
