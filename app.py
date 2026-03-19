import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, date, timedelta
import random
import os
from PIL import Image
import base64

# --- 1. 页面配置与合照图标强制加载 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(current_dir, "app_icon.png")

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

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
    .stButton>button { background-color: var(--tiffany-blue); color: white; border-radius: 12px; width: 100%; border: none; }
    h2, h3 { color: #088F8A; font-size: 1.1rem !important; }
    .stMetricValue { font-size: 1.2rem !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. Supabase 初始化 ---
SUPABASE_URL = "https://hjrvdusefkjtmucsreeq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhqcnZkdXNlZmtqdG11Y3NyZWVxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3Mzg0MzM2MiwiZXhwIjoyMDg5NDE5MzYyfQ.n7TPfrBJYeo9ZKIIEoOEPIRscmR2joGqHwqNw5-Yqsk"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 4. 核心计算公式 ---
def get_metrics(w, h, age, gender):
    bmi = round(w / ((h/100)**2), 1)
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
        st.subheader("🎨 开启双人打卡基地")
        role = st.selectbox("👤 你是谁？", ["不差儿", "花大爷"])
        age = st.number_input("年龄", 1, 100, 24)
        h = st.number_input("身高(cm)", 100, 250, 165)
        w = st.number_input("初始体重(kg)", 30.0, 200.0, 60.0)
        if st.form_submit_button("🚀 进入系统"):
            try:
                # 存入基础表
                supabase.table("users").upsert({
                    "name": role, "age": age, "height": h, "weight": w, "gender": "女"
                }, on_conflict="name").execute()
                st.session_state.user_role = role
                st.session_state.u_age = age
                st.session_state.u_height = h
                st.rerun()
            except Exception as e:
                st.error(f"保存失败，请检查 Supabase 权限 (RLS): {e}")
    st.stop()

# --- 6. 首页对垒展示 ---
role_me = st.session_state.user_role
view_date = st.date_input("📅 选择日期", date.today())

col_left, col_right = st.columns(2)

def render_side(name, col, is_me):
    with col:
        st.markdown(f"<div style='text-align:center;'><h3>{'👩‍𝓠' if name=='不差儿' else '👨‍🦳'} {name}</h3></div>", unsafe_allow_html=True)
        
        # 读取个人基础信息计算 BMR
        u_info = supabase.table("users").select("*").eq("name", name).execute()
        u_base = u_info.data[0] if u_info.data else {"weight":60, "height":165, "age":24, "gender":"女"}
        
        # 读取每日打卡数据 (使用 user_name 字段)
        res = supabase.table("daily_logs").select("*").eq("user_name", name).eq("date", str(view_date)).execute()
        day_data = res.data[0] if res.data else {}
        
        # 自动计算指标
        current_w = day_data.get('weight', u_base['weight'])
        bmi, bmr = get_metrics(current_w, u_base['height'], u_base['age'], u_base['gender'])

        # 身体卡片
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        st.write("📊 **身体指标**")
        st.metric("体重", f"{current_w} kg")
        st.metric("BMI", bmi)
        st.caption(f"体脂: {day_data.get('body_fat', 0)}% | 基代: {bmr}")
        
        if is_me:
            with st.expander("📝 录入"):
                nw = st.number_input("今日体重", value=float(current_w), key=f"w_{name}")
                nf = st.number_input("体脂率(%)", value=0.0, key=f"f_{name}")
                if st.button("同步更新", key=f"btn_{name}"):
                    supabase.table("daily_logs").upsert({
                        "user_name": name, "date": str(view_date), "weight": nw, "body_fat": nf
                    }, on_conflict="user_name,date").execute()
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # 饮食卡片
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        st.write("🍱 **饮食 & 水**")
        st.write(f"💧 饮水: {day_data.get('water', 0)} ml")
        st.write(f"🍎 摄入: {day_data.get('calorie_intake', 0)} kcal")
        st.markdown("</div>", unsafe_allow_html=True)

        # 留言
        st.info(day_data.get('note', "TA还没留言..."))
        if is_me:
            note = st.text_input("想对TA说", key=f"n_{name}")
            if st.button("发布留言", key=f"btn_n_{name}"):
                supabase.table("daily_logs").upsert({
                    "user_name": name, "date": str(view_date), "note": note
                }, on_conflict="user_name,date").execute()
                st.rerun()

# 左右对垒
render_side("不差儿", col_left, is_me=(role_me == "不差儿"))
render_side("花大爷", col_right, is_me=(role_me == "花大爷"))
