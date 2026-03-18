import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, date, timedelta
import plotly.graph_objects as go
import random
import base64
from PIL import Image

# --- 1. 页面配置与图标 ---
def get_base64_img(file_path):
    try:
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except: return None

img_b64 = get_base64_img("app_icon.png")
icon_data = f"data:image/jpeg;base64,{img_b64}" if img_b64 else "🎨"

st.set_page_config(
    page_title="花大爷 × 不差儿",
    page_icon=icon_data,
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 🎨 蒂芙尼蓝 UI 注入 (包含移动端强制双栏 CSS)
st.markdown("""
    <style>
    .stApp { background-color: #F0F9F9; }
    :root { --tiffany-blue: #0ABAB5; --deep-teal: #088F8A; }
    
    /* 强制手机端列不折叠 */
    [data-testid="column"] {
        width: 50% !important;
        flex: 1 1 50% !important;
        min-width: 50% !important;
        padding: 5px !important;
        background: white;
        border-radius: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }
    
    .main-card {
        border-top: 5px solid var(--tiffany-blue);
        padding: 10px;
        margin-bottom: 15px;
    }
    
    .stButton>button {
        background-color: var(--tiffany-blue);
        color: white;
        border-radius: 12px;
        border: none;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. Supabase 配置 ---
SUPABASE_URL = "https://hjrvdusefkjtmucsreeq.supabase.co"
SUPABASE_KEY = "sb_publishable_yDO1V8a3qYz8YPSzXSHdWA_mhpQG8QF"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 3. AI 模拟函数 ---
def mock_calorie_analyze(image):
    return random.randint(300, 700) if image else 0

def mock_fat_analyze(image):
    return round(random.uniform(15.0, 25.0), 1) if image else 0

# --- 4. 登录初始化 ---
if 'user_role' not in st.session_state:
    st.image("app_icon.png" if img_b64 else "🎨", width=120)
    with st.form("login"):
        st.markdown("<h2 style='text-align:center; color:#0ABAB5;'>开启双人打卡基地</h2>", unsafe_allow_html=True)
        role = st.selectbox("👤 你是谁？", ["不差儿", "花大爷"])
        age = st.number_input("🎂 年龄", 1, 100, 24)
        height = st.number_input("📏 身高 (cm)", 100, 250, 165)
        gender = st.selectbox("🚻 性别", ["女", "男"], index=0)
        weight = st.number_input("⚖️ 体重 (kg)", 30.0, 200.0, 60.0)
        
        if st.form_submit_button("🚀 进入系统"):
            user_data = {"name": role, "age": age, "height": height, "gender": gender, "weight": weight}
            try:
                supabase.table("users").upsert(user_data, on_conflict="name").execute()
                st.session_state.user_role = role
                st.session_state.bmr = 10*weight + 6.25*height - 5*age + (5 if gender=="男" else -161)
                st.rerun()
            except Exception as e:
                st.error(f"登录失败，请检查 Supabase 表权限: {e}")
    st.stop()

# --- 5. 首页逻辑 ---
role_me = st.session_state.user_role
view_date = st.date_input("📅 日历回顾", date.today())

def get_data(name):
    res = supabase.table("daily_logs").select("*").eq("user_name", name).eq("date", str(view_date)).execute()
    return res.data[0] if res.data else {}

# 渲染对垒
col_left, col_right = st.columns(2)

def render_side(name, col, is_me):
    with col:
        st.markdown(f"<h3 style='text-align:center; color:#088F8A;'>{'👩‍𝓠' if name=='不差儿' else '👨‍🦳'} {name}</h3>", unsafe_allow_html=True)
        data = get_data(name)
        
        # 身体指标
        with st.expander("📊 指标", expanded=True):
            st.write(f"W: {data.get('weight', 0)}kg | H: 165cm")
            st.metric("BMI", round(data.get('weight', 60)/((1.65)**2), 1) if data.get('weight') else 0)
            if is_me:
                img = st.file_uploader("体脂分析", key=f"f_{name}", type=['jpg','png'])
                if st.button("分析", key=f"btn_f_{name}"):
                    supabase.table("daily_logs").upsert({"user_name":name, "date":str(view_date), "body_fat":mock_fat_analyze(img)}, on_conflict="user_name,date").execute()
                    st.rerun()
            st.write(f"体脂: {data.get('body_fat', 0)}%")

        # 饮食
        with st.expander("🥗 饮食", expanded=True):
            st.write(f"摄入: {data.get('calorie_intake', 0)} kcal")
            if is_me:
                meal = st.file_uploader("传餐食", key=f"m_{name}")
                if st.button("同步", key=f"btn_m_{name}"):
                    cal = mock_calorie_analyze(meal)
                    supabase.table("daily_logs").upsert({"user_name":name, "date":str(view_date), "calorie_intake": data.get('calorie_intake', 0) + cal}, on_conflict="user_name,date").execute()
                    st.rerun()

        # 心得
        if is_me:
            note = st.text_input("留言", key=f"n_{name}")
            if st.button("发布", key=f"btn_n_{name}"):
                supabase.table("daily_logs").upsert({"user_name":name, "date":str(view_date), "note": note}, on_conflict="user_name,date").execute()
                st.rerun()
        else:
            st.info(data.get('note', "暂无心得"))

# 渲染
render_side("不差儿", col_left, is_me=(role_me == "不差儿"))
render_side("花大爷", col_right, is_me=(role_me == "花大爷"))
