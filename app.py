import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, date
import random
import os
import base64
from PIL import Image

# --- 1. 强制 Web Clip 图标注入 (修复 P1) ---
current_dir = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(current_dir, "app_icon.png")

def get_base64(file_path):
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

try:
    if os.path.exists(icon_path):
        img_b64 = get_base64(icon_path)
        # 注入 Apple Touch Icon (手机主屏幕图标)
        st.markdown(f"""
            <head>
                <link rel="apple-touch-icon" href="data:image/png;base64,{img_b64}">
                <link rel="apple-touch-icon-precomposed" href="data:image/png;base64,{img_b64}">
            </head>
            """, unsafe_allow_html=True)
        st.set_page_config(page_title="花大爷 × 不差儿", page_icon=Image.open(icon_path), layout="wide")
    else:
        st.set_page_config(page_title="花大爷 × 不差儿", layout="wide")
except:
    st.set_page_config(page_title="花大爷 × 不差儿", layout="wide")

# --- 2. 强力 CSS 注入 (修复 P2 颜色和两列布局) ---
st.markdown(f"""
    <style>
    /* 强制锁定文字颜色为深色，背景为淡色，无视系统深色模式 */
    html, body, [data-testid="stAppViewContainer"], .stMarkdown, p, span, label, div {{
        color: #1A1A1A !important;
        background-color: #F0F9F9 !important;
    }}
    
    /* 强制手机端不折叠，保持左右并排 */
    [data-testid="column"] {{
        width: 50% !important;
        flex: 1 1 50% !important;
        min-width: 50% !important;
        padding: 5px !important;
    }}

    /* 输入框和卡片样式优化 */
    .stNumberInput, .stTextInput, .stSelectbox {{
        background-color: #FFFFFF !important;
    }}
    .card {{
        background-color: #FFFFFF !important;
        padding: 15px;
        border-radius: 15px;
        border-top: 5px solid #0ABAB5;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }}
    .stButton>button {{
        background-color: #0ABAB5 !important;
        color: white !important;
        border-radius: 12px !important;
        width: 100%;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. 数据库初始化 ---
URL = "https://hjrvdusefkjtmucsreeq.supabase.co"
KEY = "sb_publishable_yDO1V8a3qYz8YPSzXSHdWA_mhpQG8QF"
supabase: Client = create_client(URL, KEY)

# --- 4. 身份判定与初始化逻辑 ---
if 'user_role' not in st.session_state:
    st.image(icon_path, width=120) if os.path.exists(icon_path) else st.title("🎨")
    with st.form("login"):
        role = st.selectbox("👤 你是谁？", ["花大爷", "不差儿"])
        if st.form_submit_button("进入基地"):
            st.session_state.user_role = role
            st.rerun()
    st.stop()

my_name = st.session_state.user_role
other_name = "不差儿" if my_name == "花大爷" else "花大爷"

# 检查是否初始化
res = supabase.table("users").select("*").eq("name", my_name).execute()
if not res.data:
    with st.form("init"):
        st.subheader(f"🐣 {my_name}，请完成初始化")
        h = st.number_input("身高(cm)", 100, 250, 165)
        w = st.number_input("初始体重(kg)", 30.0, 200.0, 60.0)
        age = st.number_input("年龄", 1, 100, 24)
        if st.form_submit_button("完成"):
            supabase.table("users").insert({"name": my_name, "height": h, "weight": w, "age": age}).execute()
            st.rerun()
    st.stop()

# --- 5. 主页面布局 ---
col_left, col_right = st.columns(2)

def render_user(name, col, is_me):
    # 获取数据
    base = supabase.table("users").select("*").eq("name", name).execute().data
    base = base[0] if base else None
    log_res = supabase.table("daily_logs").select("*").eq("user_name", name).eq("log_date", str(date.today())).execute()
    log = log_res.data[0] if log_res.data else {}

    with col:
        st.markdown(f"<h3 style='text-align:center;'>{'👩‍𝓠' if name=='不差儿' else '👨‍🦳'} {name}</h3>", unsafe_allow_html=True)
        if not base:
            st.info("尚未初始化")
            return

        # 身体指标卡
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.write(f"📏 身高: {base['height']} cm")
        w_val = log.get('weight', base['weight'])
        
        if is_me:
            new_w = st.number_input("今日体重", value=float(w_val), key=f"nw_{name}")
            # 围度
            waist = st.number_input("腰围", value=float(log.get('waist', 0)), key=f"waist_{name}")
            if st.button("保存今日数据", key=f"btn_{name}"):
                supabase.table("daily_logs").upsert({
                    "user_name": name, "log_date": str(date.today()), "weight": new_w, "waist": waist
                }, on_conflict="user_name,log_date").execute()
                st.rerun()
        else:
            st.metric("今日体重", f"{w_val} kg")
            st.write(f"腰围: {log.get('waist', 0)} cm")
        st.markdown('</div>', unsafe_allow_html=True)

# 渲染
render_user("不差儿", col_left, my_name == "不差儿")
render_user("花大爷", col_right, my_name == "花大爷")
