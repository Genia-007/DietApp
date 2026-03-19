import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, date
import random
import os
from PIL import Image

# --- 1. 基础配置 ---
try:
    icon_img = Image.open("app_icon.png")
    st.set_page_config(page_title="花大爷 × 不差儿", page_icon=icon_img, layout="wide")
except:
    st.set_page_config(page_title="花大爷 × 不差儿", layout="wide")

# --- 2. 数据库配置 ---
SUPABASE_URL = "https://hjrvdusefkjtmucsreeq.supabase.co"
SUPABASE_KEY = "sb_publishable_yDO1V8a3qYz8YPSzXSHdWA_mhpQG8QF"
TIFFANY_BLUE = "#0ABAB5"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# --- 3. 工具函数 ---
def calculate_age(birth_date):
    if not birth_date: return 0
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

def get_streak_days():
    """从最早的一笔打卡记录开始计算天数"""
    try:
        res = supabase.table("daily_logs").select("log_date").order("log_date", desc=False).limit(1).execute()
        if res.data:
            start_date = datetime.strptime(res.data[0]['log_date'], '%Y-%m-%d').date()
            return (date.today() - start_date).days + 1
    except: pass
    return 1

# CSS 注入
st.markdown(f"""
    <style>
    .stApp {{ background-color: #F0F9F9; }}
    .card {{ background: white; padding: 20px; border-radius: 15px; border-top: 5px solid {TIFFANY_BLUE}; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; }}
    .stButton>button {{ background: {TIFFANY_BLUE}; color: white; border-radius: 10px; width: 100%; border: none; }}
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
        
        if st.button("🚀 进入系统"):
            try:
                # 存入初始资料
                supabase.table("users").upsert({
                    "name": role, "birthday": str(birth), "age": u_age, 
                    "height": int(u_height), "weight": u_weight, "gender": "女"
                }, on_conflict="name").execute()
                st.session_state.user_role = role
                st.rerun()
            except Exception as e:
                st.error("初始化存入失败！请确保你已经在 Supabase 运行了添加 birthday 字段的 SQL。")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- 5. 主界面内容 ---
role_me = st.session_state.user_role
role_other = "不差儿" if role_me == "花大爷" else "花大爷"

col_top1, col_top2 = st.columns([3, 1])
with col_top1:
    st.image("app_icon.png", width=100)
    view_date = st.date_input("📅 选择日期", date.today())
with col_top2:
    st.write(f"今日打卡天数: 🔥 {get_streak_days()}天")

col_left, col_right = st.columns(2)

def render_column(name, col, is_editable):
    try:
        # 查基础资料
        u_res = supabase.table("users").select("*").eq("name", name).execute()
        u_base = u_res.data[0] if u_res.data else None
        # 查今日记录
        l_res = supabase.table("daily_logs").select("*").eq("user_name", name).eq("log_date", str(view_date)).execute()
        log = l_res.data[0] if l_res.data else {}
    except: u_base, log = None, {}

    if not u_base:
        col.info(f"等待 {name} 初始化...")
        return

    with col:
        st.markdown(f"### {'👨‍🦳' if name=='花大爷' else '👩‍𝓠'} {name}")
        
        # 指标卡
        st.markdown('<div class="card"><b>📊 身体指标</b>', unsafe_allow_html=True)
        st.write(f"身高: {u_base['height']} cm")
        w = log.get('weight', u_base['weight'])
        
        if is_editable:
            curr_w = st.number_input("今日体重", value=float(w), key=f"nw_{name}")
            st.write(f"BMI: {round(curr_w/((u_base['height']/100)**2),1)}")
            
            # 围度录入 (补齐所有字段)
            g1, g2 = st.columns(2)
            waist = g1.number_input("腰围", value=float(log.get('waist',0)), key=f"wa_{name}")
            hip = g2.number_input("臀围", value=float(log.get('hip',0)), key=f"hi_{name}")
            arm = g1.number_input("臂围", value=float(log.get('arm',0)), key=f"ar_{name}")
            chest = g2.number_input("胸围", value=float(log.get('chest',0)), key=f"ch_{name}")
            
            if st.button("💾 同步今日数据", key=f"sv_{name}"):
                supabase.table("daily_logs").upsert({
                    "user_name": name, "log_date": str(view_date), 
                    "weight": curr_w, "waist": waist, "hip": hip, "arm": arm, "chest": chest
                }, on_conflict="user_name,log_date").execute()
                st.rerun()
        else:
            st.write(f"体重: {w} kg")
            st.write(f"腰围: {log.get('waist', 0)} | 臀围: {log.get('hip', 0)}")
        st.markdown('</div>', unsafe_allow_html=True)

render_column(role_other, col_left, False)
render_column(role_me, col_right, True)

if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()
