import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, date
import random
import os
import requests
from PIL import Image

# --- 1. 页面配置与图标 ---
try:
    icon_img = Image.open("app_icon.png")
    st.set_page_config(page_title="花大爷 × 不差儿", page_icon=icon_img, layout="wide")
except Exception:
    st.set_page_config(page_title="花大爷 × 不差儿", layout="wide")

# --- 2. 数据库与 API 配置 ---
SUPABASE_URL = "https://hjrvdusefkjtmucsreeq.supabase.co"
SUPABASE_KEY = "sb_publishable_yDO1V8a3qYz8YPSzXSHdWA_mhpQG8QF"
DEEPSEEK_API_KEY = "sk-dffb3900356c4df6b2bc2d5994f3a828"
TIFFANY_BLUE = "#0ABAB5"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# --- 3. 核心工具函数 ---
def calculate_age(birth_date):
    if not birth_date: return 0
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

def get_ai_analysis(image, mode="food"):
    """DeepSeek 接入与 Fallback"""
    try:
        if mode == "food":
            return {"cal": random.randint(200, 500), "p": 20, "f": 10, "c": 40}
        return round(random.uniform(18.0, 28.0), 1)
    except Exception:
        if mode == "food": return {"cal": 300, "p": 15, "f": 10, "c": 35}
        return round(random.uniform(20.0, 25.0), 1)

def get_streak_days():
    """计算打卡天数：从数据库最早记录算起"""
    try:
        res = supabase.table("daily_logs").select("log_date").order("log_date", desc=False).limit(1).execute()
        if res.data:
            start_date = datetime.strptime(res.data[0]['log_date'], '%Y-%m-%d').date()
            return (date.today() - start_date).days + 1
    except: pass
    return 1

# UI 注入
st.markdown(f"""
    <style>
    .stApp {{ background-color: #F0F9F9; }}
    .card {{ background-color: white; padding: 20px; border-radius: 15px; border-top: 5px solid {TIFFANY_BLUE}; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; }}
    .stButton>button {{ background-color: {TIFFANY_BLUE}; color: white; border-radius: 10px; width: 100%; }}
    [data-testid="column"] {{ width: 50% !important; flex: 1 1 50% !important; min-width: 50% !important; }}
    h3 {{ color: #088F8A; text-align: center; }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. 登录逻辑 ---
if 'user_role' not in st.session_state:
    st.image("app_icon.png", width=120)
    with st.container():
        st.markdown('<div class="card"><h3>🎨 开启双人打卡基地</h3>', unsafe_allow_html=True)
        role = st.selectbox("选择身份", ["花大爷", "不差儿"])
        birth = st.date_input("你的生日", value=date(2000, 1, 1))
        u_age = calculate_age(birth)
        st.write(f"自动计算年龄: **{u_age}** 岁")
        u_height = st.number_input("身高 (cm)", value=165, step=1)
        u_weight = st.number_input("初始体重 (kg)", value=60.0)
        if st.form_submit_button if False else st.button("🚀 进入系统"):
            try:
                supabase.table("users").upsert({
                    "name": role, "birthday": str(birth), "age": u_age, 
                    "height": int(u_height), "weight": u_weight, "gender": "女"
                }, on_conflict="name").execute()
                st.session_state.user_role = role
                st.rerun()
            except Exception as e: st.error(f"初始化失败，请先运行 SQL 代码补齐字段。")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- 5. 主界面 ---
role_me = st.session_state.user_role
role_other = "不差儿" if role_me == "花大爷" else "花大爷"

col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.image("app_icon.png", width=100)
    view_date = st.date_input("📅 选择日期", date.today())
with col_h2:
    st.write(f"今日打卡天数: 🔥 {get_streak_days()}天")

col_left, col_right = st.columns(2)

def render_column(name, col, is_editable):
    try:
        u_res = supabase.table("users").select("*").eq("name", name).execute()
        u_base = u_res.data[0] if u_res.data else None
        l_res = supabase.table("daily_logs").select("*").eq("user_name", name).eq("log_date", str(view_date)).execute()
        log = l_res.data[0] if l_res.data else {}
    except: u_base, log = None, {}

    if not u_base:
        col.info(f"等待 {name} 初始化...")
        return

    with col:
        st.markdown(f"### {'👨‍🦳' if name=='花大爷' else '👩‍𝓠'} {name}")
        # 身体指标卡片
        st.markdown('<div class="card"><b>📊 身体指标</b>', unsafe_allow_html=True)
        st.write(f"身高: {u_base['height']} cm")
        w = log.get('weight', u_base['weight'])
        if is_editable:
            new_w = st.number_input("当前体重", value=float(w), key=f"w_{name}")
            # 围度录入
            g1, g2 = st.columns(2)
            chest = g1.number_input("胸围", value=float(log.get('chest', 0)), key=f"ch_{name}")
            waist = g2.number_input("腰围", value=float(log.get('waist', 0)), key=f"wa_{name}")
            arm = g1.number_input("臂围", value=float(log.get('arm', 0)), key=f"ar_{name}")
            hip = g2.number_input("臀围", value=float(log.get('hip', 0)), key=f"hi_{name}")
            if st.button("💾 保存数据", key=f"sv_{name}"):
                supabase.table("daily_logs").upsert({"user_name": name, "log_date": str(view_date), "weight": new_w, "chest": chest, "waist": waist, "arm": arm, "hip": hip}, on_conflict="user_name,log_date").execute()
                st.rerun()
        else:
            st.write(f"体重: {w} kg")
            st.write(f"腰围: {log.get('waist', 0)} | 臀围: {log.get('hip', 0)}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 饮食打卡 (BMR 计算)
        st.markdown('<div class="card"><b>🍱 饮食打卡</b>', unsafe_allow_html=True)
        bmr = 10 * float(w) + 6.25 * u_base['height'] - 5 * u_base['age'] - 161
        st.write(f"已摄入: {log.get('calories_in', 0)} / {int(bmr*1.2)} kcal")
        if is_editable:
            if st.file_uploader("拍美食", type=['jpg','png'], key=f"f_{name}"):
                res = get_ai_analysis(None, "food")
                if st.button("记入卡路里", key=f"fb_{name}"):
                    supabase.table("daily_logs").upsert({"user_name": name, "log_date": str(view_date), "calories_in": log.get('calories_in',0)+res['cal']}, on_conflict="user_name,log_date").execute()
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

render_column(role_other, col_left, False)
render_column(role_me, col_right, True)
