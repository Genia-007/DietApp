# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, date
import random
import os
import base64
from PIL import Image

# --- 1. 强制图标注入 (解决添加到主屏幕图标问题) ---
icon_path = "app_icon.png"
img_base64 = ""
if os.path.exists(icon_path):
    with open(icon_path, "rb") as img_file:
        img_base64 = base64.b64encode(img_file.read()).decode()

try:
    st.set_page_config(
        page_title="花大爷 × 不差儿",
        page_icon=Image.open(icon_path) if os.path.exists(icon_path) else "🎨",
        layout="wide"
    )
except:
    st.set_page_config(layout="wide")

# 注入 Apple Touch Icon
if img_base64:
    st.markdown(f'<head><link rel="apple-touch-icon" href="data:image/png;base64,{img_base64}"></head>', unsafe_allow_html=True)

# --- 2. 极致紧凑型 CSS (适配手机并排 + 缩小组件) ---
st.markdown(f"""
    <style>
    /* 强制手机并排且不溢出 */
    [data-testid="stHorizontalBlock"] {{
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        width: 100% !important;
        gap: 0.2rem !important;
    }}
    
    [data-testid="column"] {{
        width: 50% !important;
        flex: 1 1 50% !important;
        min-width: 0 !important; /* 核心：允许极度压缩 */
        overflow: hidden;
    }}

    /* 强制黑字对比度 */
    html, body, [data-testid="stAppViewContainer"], .stMarkdown, p, span, label, div {{
        color: #1A1A1A !important;
        font-family: -apple-system, sans-serif !important;
    }}

    .stApp {{ background-color: #F0F9F9; }}
    
    /* 缩小卡片与输入框 */
    .card {{
        background-color: white; padding: 8px; border-radius: 8px;
        border-top: 3px solid #0ABAB5; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 8px;
    }}
    
    .stButton>button {{
        background-color: #0ABAB5; color: white !important;
        border-radius: 6px; padding: 2px 5px; font-size: 11px !important;
    }}

    /* 手机端专用：缩小一切 */
    @media (max-width: 640px) {{
        .card {{ padding: 4px; }}
        .stMetricValue {{ font-size: 14px !important; }}
        .stMarkdown p, label {{ font-size: 10px !important; line-height: 1.1; }}
        h3 {{ font-size: 12px !important; margin: 5px 0 !important; }}
        input {{ height: 24px !important; font-size: 10px !important; padding: 2px !important; }}
        div[data-baseweb="input"] {{ min-height: 24px !important; }}
        .stSelectbox div {{ font-size: 10px !important; min-height: 24px !important; }}
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. 数据库与逻辑 ---
SUPABASE_URL = "https://hjrvdusefkjtmucsreeq.supabase.co"
SUPABASE_KEY = "sb_publishable_yDO1V8a3qYz8YPSzXSHdWA_mhpQG8QF"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def safe_float(v, default=0.0):
    try: return float(v) if v is not None else float(default)
    except: return float(default)

# --- 4. 身份登录 ---
if 'user_role' not in st.session_state:
    if os.path.exists(icon_path): st.image(icon_path, width=80)
    with st.form("login"):
        role = st.selectbox("是谁？", ["不差儿", "花大爷"])
        if st.form_submit_button("进入"):
            st.session_state.user_role = role
            st.rerun()
    st.stop()

my_name = st.session_state.user_role
other_name = "花大爷" if my_name == "不差儿" else "不差儿"

# --- 5. 顶栏 ---
c1, c2 = st.columns([1, 1])
with c1: 
    if os.path.exists(icon_path): st.image(icon_path, width=50)
with c2: 
    view_date = st.date_input("", date.today(), label_visibility="collapsed")

# --- 6. 统一渲染 (极致紧凑) ---
def render_col(name, col, editable, base_info):
    try:
        log = supabase.table("daily_logs").select("*").eq("user_name", name).eq("log_date", str(view_date)).execute().data[0]
    except: log = {}

    with col:
        st.markdown(f"### {'👩‍𝓠' if name=='不差儿' else '👨‍🦳'} {name}")
        if not base_info:
            st.info("待初始")
            return

        # 维度卡
        st.markdown('<div class="card">', unsafe_allow_html=True)
        w = st.number_input("重", value=safe_float(log.get("weight", base_info.get("weight"))), key=f"w_{name}", disabled=not editable)
        
        g1, g2 = st.columns(2)
        waist = g1.number_input("腰", value=safe_float(log.get("waist")), key=f"wa_{name}", disabled=not editable)
        thigh = g2.number_input("腿", value=safe_float(log.get("thigh")), key=f"th_{name}", disabled=not editable)
        
        if st.button("💾 存", key=f"s_{name}", disabled=not editable):
            supabase.table("daily_logs").upsert({
                "user_name": name, "log_date": str(view_date), "weight": w, "waist": waist, "thigh": thigh
            }, on_conflict="user_name,log_date").execute()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # 饮食卡
        st.markdown('<div class="card">', unsafe_allow_html=True)
        c_in = safe_float(log.get('calorie_intake'))
        st.metric("摄入", f"{int(c_in)}")
        f_img = st.file_uploader("", type=['jpg','png'], key=f"f_{name}", disabled=not editable, label_visibility="collapsed")
        if f_img: st.image(f_img, width=60)
        if st.button("🚀 AI", key=f"ai_{name}", disabled=not editable):
            supabase.table("daily_logs").upsert({"user_name": name, "log_date": str(view_date), "calorie_intake": c_in + 400}, on_conflict="user_name,log_date").execute()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# 渲染对垒
try:
    me_base = supabase.table("users").select("*").eq("name", my_name).execute().data[0]
    friend_res = supabase.table("users").select("*").eq("name", other_name).execute()
    friend_base = friend_res.data[0] if friend_res.data else None
except:
    st.stop()

cl, cr = st.columns(2)
render_col("不差儿", cl, (my_name == "不差儿"), friend_base)
render_col("花大爷", cr, (my_name == "花大爷"), me_base)
