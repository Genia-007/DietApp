import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, date, timedelta
import random
import os
import base64
from PIL import Image

# --- 1. 页面配置与合照图标强制加载 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(current_dir, "app_icon.png")

def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    except: return None

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
except:
    st.set_page_config(page_title="花大爷 × 不差儿", layout="wide")

# --- 2. 蒂芙尼蓝 & 移动端强制并排 CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #F0F9F9; }
    :root { --tiffany-blue: #0ABAB5; }
    
    /* 强制手机端列不折叠，保持 50/50 比例 */
    [data-testid="column"] {
        width: 50% !important;
        flex: 1 1 50% !important;
        min-width: 50% !important;
        padding: 5px !important;
    }
    
    .main-card {
        background: white; border-radius: 20px; padding: 15px;
        border-top: 5px solid var(--tiffany-blue);
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }
    .stButton>button { 
        background-color: var(--tiffany-blue); 
        color: white; 
        border-radius: 12px; 
        width: 100%; 
        border: none;
        font-weight: bold;
    }
    h2, h3 { color: #088F8A; font-size: 1.1rem !important; margin-bottom: 10px !important; }
    .stMetricValue { font-size: 1.2rem !important; color: #0ABAB5 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 从 Streamlit Secrets 安全读取钥匙 ---
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error(f"❌ 钥匙读取失败！请检查 Streamlit Secrets 配置: {e}")
    st.stop()

# --- 4. 核心计算公式 ---
def get_metrics(w, h, age, gender):
    bmi = round(w / ((h/100)**2), 1)
    # Mifflin-St Jeor 公式
    if gender == "女":
        bmr = 10 * w + 6.25 * h - 5 * age - 161
    else:
        bmr = 10 * w + 6.25 * h - 5 * age + 5
    return bmi, int(bmr)

# --- 5. 登录初始化 ---
if 'user_role' not in st.session_state:
    if os.path.exists(icon_path):
        st.image(Image.open(icon_path), width=120)
    with st.form("login"):
        st.markdown("<h3 style='text-align:center;'>🎨 开启双人打卡基地</h3>", unsafe_allow_html=True)
        role = st.selectbox("👤 你是谁？", ["不差儿", "花大爷"])
        age = st.number_input("年龄", 1, 100, 24)
        h = st.number_input("身高(cm)", 100, 250, 163)
        w = st.number_input("初始体重(kg)", 30.0, 200.0, 61.5)
        if st.form_submit_button("🚀 进入系统"):
            try:
                # 存入基础资料
                supabase.table("users").upsert({
                    "name": role, "age": age, "height": h, "weight": w, "gender": "女"
                }, on_conflict="name").execute()
                st.session_state.user_role = role
                st.rerun()
            except Exception as e:
                st.error(f"❌ 破门失败: {e}")
    st.stop()

# --- 6. 首页展示 ---
role_me = st.session_state.user_role
view_date = st.date_input("📅 历史回顾", date.today())

col_left, col_right = st.columns(2)

def render_side(name, col, is_me):
    with col:
        st.markdown(f"<div style='text-align:center;'><h3>{'👩‍𝓠' if name=='不差儿' else '👨‍🦳'} {name}</h3></div>", unsafe_allow_html=True)
        
        # 获取基础信息
        u_info = supabase.table("users").select("*").eq("name", name).execute()
        u_base = u_info.data[0] if u_info.data else {"weight":60, "height":165, "age":24, "gender":"女"}
        
        # 获取每日打卡数据
        res = supabase.table("daily_logs").select("*").eq("user_name", name).eq("date", str(view_date)).execute()
        day_data = res.data[0] if res.data else {}
        
        # 实时计算
        current_w = day_data.get('weight', u_base['weight'])
        bmi, bmr = get_metrics(current_w, u_base['height'], u_base['age'], u_base['gender'])

        # 指标卡
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        st.metric("体重", f"{current_w} kg")
        st.metric("BMI", bmi)
        st.caption(f"基代: {bmr} kcal | 体脂: {day_data.get('body_fat', 0)}%")
        
        if is_me:
            with st.expander("📝 录入"):
                nw = st.number_input("体重", value=float(current_w), key=f"w_{name}")
                if st.button("同步", key=f"btn_{name}"):
                    supabase.table("daily_logs").upsert({
                        "user_name": name, "date": str(view_date), "weight": nw
                    }, on_conflict="user_name,date").execute()
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # 留言
        st.info(day_data.get('note', "TA还没说话..."))
        if is_me:
            note = st.text_input("给TA留言", key=f"n_{name}")
            if st.button("发送", key=f"btn_n_{name}"):
                supabase.table("daily_logs").upsert({
                    "user_name": name, "date": str(view_date), "note": note
                }, on_conflict="user_name,date").execute()
                st.rerun()

# 渲染对垒
render_side("不差儿", col_left, is_me=(role_me == "不差儿"))
render_side("花大爷", col_right, is_me=(role_me == "花大爷"))
