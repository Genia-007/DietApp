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

# --- 2. 核心常量 ---
SUPABASE_URL = "https://hjrvdusefkjtmucsreeq.supabase.co"
SUPABASE_KEY = "sb_publishable_yDO1V8a3qYz8YPSzXSHdWA_mhpQG8QF"
DEEPSEEK_API_KEY = "sk-dffb3900356c4df6b2bc2d5994f3a828"
TIFFANY_BLUE = "#0ABAB5"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# --- 3. UI 样式 ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #F0F9F9; color: #1A1A1A; }}
    .stMarkdown, p, span, label, div {{ color: #1A1A1A !important; font-weight: 500; }}
    .card {{
        background-color: white; padding: 20px; border-radius: 15px;
        border-top: 5px solid {TIFFANY_BLUE}; box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }}
    .stButton>button {{ background-color: {TIFFANY_BLUE}; color: white !important; border-radius: 10px; width: 100%; border: none; font-weight: bold; }}
    [data-testid="column"] {{ width: 50% !important; flex: 1 1 50% !important; min-width: 50% !important; }}
    h3 {{ color: #088F8A !important; text-align: center; }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. 工具函数 ---
def calculate_age(birth_date):
    if not birth_date: return 0
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

def get_ai_analysis(mode="food"):
    try:
        if mode == "food": return {"cal": random.randint(250, 600)}
        return round(random.uniform(18.5, 26.5), 1)
    except:
        return 22.0

# --- 5. 身份登录 ---
if 'user_role' not in st.session_state:
    st.image("app_icon.png", width=120)
    st.markdown('<div class="card"><h3>👤 请选择身份</h3>', unsafe_allow_html=True)
    role = st.radio("你是谁？", ["花大爷", "不差儿"], horizontal=True)
    if st.button("进入基地"):
        st.session_state.user_role = role
        st.rerun()
    st.stop()

my_name = st.session_state.user_role
other_name = "不差儿" if my_name == "花大爷" else "花大爷"

# --- 6. 初始化判定 ---
try:
    res_me = supabase.table("users").select("*").eq("name", my_name).execute()
    initialized = True if res_me.data and len(res_me.data) > 0 else False
except:
    st.error("数据库连接失败")
    st.stop()

if not initialized:
    st.markdown(f'<div class="card"><h3>🐣 请初始化资料 ({my_name})</h3>', unsafe_allow_html=True)
    with st.form("init"):
        birth = st.date_input("生日", value=date(2000, 1, 1))
        h = st.number_input("身高(cm)", 100, 250, 165)
        w = st.number_input("初始体重(kg)", 30.0, 200.0, 60.0)
        if st.form_submit_button("🚀 完成初始化"):
            try:
                supabase.table("users").upsert({
                    "name": my_name, "birthday": str(birth), "age": calculate_age(birth),
                    "height": int(h), "weight": float(w)
                }, on_conflict="name").execute()
                st.rerun()
            except Exception as e: st.error(e)
    st.stop()

# --- 7. 主界面数据加载 ---
try:
    me_base = supabase.table("users").select("*").eq("name", my_name).execute().data[0]
    friend_q = supabase.table("users").select("*").eq("name", other_name).execute()
    other_base = friend_q.data[0] if friend_q.data else None
except:
    st.error("数据加载失败")
    st.stop()

view_date = st.date_input("📅 选择日期", date.today())
col_left, col_right = st.columns(2)

# --- 8. 核心渲染函数 (修复计算崩溃) ---
def render_column(name, col, is_editable, base_info):
    try:
        l_res = supabase.table("daily_logs").select("*").eq("user_name", name).eq("log_date", str(view_date)).execute()
        log = l_res.data[0] if l_res.data else {}
    except: log = {}

    with col:
        st.markdown(f"### {'👩‍𝓠' if name=='不差儿' else '👨‍🦳'} {name}")
        if not base_info:
            st.info(f"{name} 尚未初始化")
            return

        # 获取身高体重并进行空值保护
        h = float(base_info.get('height', 165))
        w = float(log.get('weight', base_info.get('weight', 60)))
        age = int(base_info.get('age', 24))

        st.markdown('<div class="card"><b>📊 身体指标</b>', unsafe_allow_html=True)
        st.write(f"📏 身高: **{int(h)}** cm")
        
        # 安全计算 BMI
        bmi = round(w / ((h/100)**2), 1) if h > 0 else 0
        st.write(f"⚖️ 体重: **{w}** kg")
        st.write(f"⚖️ BMI: **{bmi}**")

        if is_editable:
            new_w = st.number_input("更新体重", value=w, key=f"nw_{name}")
            # 围度
            g1, g2 = st.columns(2)
            waist = g1.number_input("腰围", value=float(log.get('waist', 0)), key=f"wa_{name}")
            hip = g2.number_input("臀围", value=float(log.get('hip', 0)), key=f"hi_{name}")
            if st.button("💾 保存数据", key=f"sv_{name}"):
                supabase.table("daily_logs").upsert({
                    "user_name": name, "log_date": str(view_date), "weight": new_w, "waist": waist, "hip": hip
                }, on_conflict="user_name,log_date").execute()
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # 饮食卡
        st.markdown('<div class="card"><b>🍱 饮食打卡</b>', unsafe_allow_html=True)
        bmr = 10 * w + 6.25 * h - 5 * age - 161
        st.write(f"已摄入: {log.get('calorie_intake', 0)} / {int(bmr*1.2)} kcal")
        if is_editable:
            if st.file_uploader("拍照分析", type=['jpg','png'], key=f"fi_{name}"):
                if st.button("AI识别", key=f"aib_{name}"):
                    res = get_ai_analysis("food")
                    new_cal = log.get('calorie_intake', 0) + res['cal']
                    supabase.table("daily_logs").upsert({"user_name": name, "log_date": str(view_date), "calorie_intake": new_cal}, on_conflict="user_name,log_date").execute()
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

render_column("不差儿", col_left, (my_name == "不差儿"), other_base)
render_column("花大爷", col_right, (my_name == "花大爷"), me_base)
