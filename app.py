import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, date, timedelta
import plotly.graph_objects as go
import random
import base64
from PIL import Image

# --- 1. 专属图标与页面配置 (Base64 强制加载) ---
def get_base64_img(file_path):
    try:
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except: return None

img_base64 = get_base64_img("6af1af85193fb5400cc2503413532cbe.jpg")
if img_base64:
    favicon = f"data:image/jpeg;base64,{img_base64}"
    st.set_page_config(layout="wide", page_title="花大爷 × 不差儿", page_icon=favicon)
else:
    st.set_page_config(layout="wide", page_title="花大爷 × 不差儿", page_icon="🎨")

# --- 2. 蒂芙尼蓝移动端优化 CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #F0F9F9; }
    :root { --tiffany-blue: #0ABAB5; --deep-teal: #088F8A; }
    
    /* 强制手机端列不折叠：50/50 分布 */
    [data-testid="column"] {
        width: 50% !important;
        flex: 1 1 50% !important;
        min-width: 50% !important;
        padding: 5px !important;
    }
    
    @media (max-width: 640px) {
        .main-card { padding: 10px !important; border-radius: 15px !important; margin-bottom: 10px !important; }
        h2 { font-size: 1rem !important; }
        .stMetricValue { font-size: 1.1rem !important; }
        label { font-size: 0.8rem !important; }
    }

    .main-card { 
        background: white; padding: 20px; border-radius: 25px; 
        border-top: 5px solid var(--tiffany-blue); 
        box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 15px; 
    }
    .stButton>button { background-color: var(--tiffany-blue); color: white; border-radius: 12px; width: 100%; border: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. Supabase 客户端封装 ---
# 🔑 确认这里的 URL 和 Key 是正确的
SUPABASE_URL = "https://hjrvdusefkjtmucsreeq.supabase.co"
SUPABASE_KEY = "sb_publishable_yDO1V8a3qYz8YPSzXSHdWA_mhpQG8QF"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 4. 核心逻辑与 AI 模拟 ---
def mock_ai_analyze(type="food"):
    if type == "food": return random.randint(300, 600)
    return round(random.uniform(18.0, 25.0), 1)

def calculate_bmr(w, h, age, gender):
    # Mifflin-St Jeor 公式
    if gender == "女":
        return 10 * w + 6.25 * h - 5 * age - 161
    return 10 * w + 6.25 * h - 5 * age + 5

# --- 5. 登录与初始化 ---
if 'user_role' not in st.session_state:
    with st.form("login_form"):
        st.markdown("<h3 style='text-align:center; color:#0ABAB5;'>🎨 开启双人对垒之旅</h3>", unsafe_allow_html=True)
        role = st.selectbox("👤 你是谁？", ["不差儿", "花大爷"])
        c1, c2, c3 = st.columns(3)
        age = c1.number_input("🎂 年龄", value=24, step=1)
        height = c2.number_input("📏 身高 (厘米)", value=165, step=1)
        gender = c3.selectbox("🚻 性别", ["女", "男"], index=0)
        weight = st.number_input("⚖️ 当前体重 (kg)", value=60, step=1)
        
        if st.form_submit_button("🚀 进入基地"):
            # 保存基础资料到 users 表
            user_data = {"name": role, "age": age, "height": height, "gender": gender, "weight": weight}
            try:
                supabase.table("users").upsert(user_data, on_conflict="name").execute()
                st.session_state.user_role = role
                st.session_state.bmr = calculate_bmr(weight, height, age, gender)
                st.rerun()
            except Exception as e:
                st.error(f"登录失败，请检查 Supabase 表结构或权限: {e}")
    st.stop()

# --- 6. 数据加载 ---
user_role = st.session_state.user_role
view_date = st.date_input("📅 历史回顾", date.today())

# 获取最新打卡数据 (注意这里使用的是 user_name)
def get_data(name):
    res = supabase.table("daily_logs").select("*").eq("user_name", name).eq("date", str(view_date)).execute()
    return res.data[0] if res.data else None

# --- 7. 渲染对垒区 ---
st.markdown(f"<div class='main-card' style='text-align:center;'>🦾 欢迎回来，{user_role}！今日基代：{st.session_state.bmr:.0f} kcal</div>", unsafe_allow_html=True)

col_left, col_right = st.columns(2)

def render_side(name, col, is_me):
    with col:
        st.markdown(f"<div style='text-align:center;'><h2>{'👩‍𝓠' if name=='不差儿' else '👨‍🦳'} {name}</h2></div>", unsafe_allow_html=True)
        data = get_data(name)
        
        # 身体指标卡片
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        st.write("📊 **身体指标**")
        m1, m2 = st.columns(2)
        m1.metric("体重", f"{data['weight'] if data else '--'} kg")
        m2.metric("体脂", f"{data['body_fat'] if data else '--'} %")
        
        if is_me:
            with st.expander("📝 录入指标"):
                with st.form(f"body_{name}"):
                    nw = st.number_input("体重", value=60); nf = st.number_input("体脂", value=20)
                    if st.form_submit_button("保存"):
                        supabase.table("daily_logs").upsert({"user_name":name, "date":str(view_date), "weight":nw, "body_fat":nf}, on_conflict="user_name,date").execute()
                        st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # 饮食卡片
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        in_cal = data['calorie_intake'] if data else 0
        st.metric("已摄入", f"{in_cal} kcal")
        if is_me:
            with st.expander("🍱 饮食打卡"):
                with st.form(f"diet_{name}"):
                    img = st.file_uploader("上传照片 AI 识别")
                    if st.form_submit_button("识别并发布"):
                        new_cal = mock_ai_analyze("food")
                        supabase.table("daily_logs").upsert({"user_name":name, "date":str(view_date), "calorie_intake": in_cal + new_cal}, on_conflict="user_name,date").execute()
                        st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # 心得卡片
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        st.write(f"💬 心得: {data['note'] if data else '暂无记录'}")
        if is_me:
            with st.form(f"note_{name}"):
                nt = st.text_input("留言...")
                if st.form_submit_button("同步"):
                    supabase.table("daily_logs").upsert({"user_name":name, "date":str(view_date), "note": nt}, on_conflict="user_name,date").execute()
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# 渲染对垒 (左不差儿，右花大爷)
render_side("不差儿", col_left, is_me=(user_role == "不差儿"))
render_side("花大爷", col_right, is_me=(user_role == "花大爷"))
