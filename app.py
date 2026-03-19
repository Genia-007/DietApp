# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, date
import random
import os
from PIL import Image

# --- 1. 基础配置与图标 ---
icon_path = "app_icon.png"
try:
    if os.path.exists(icon_path):
        st.set_page_config(page_title="花大爷 × 不差儿", page_icon=Image.open(icon_path), layout="wide")
    else:
        st.set_page_config(page_title="花大爷 × 不差儿", layout="wide")
except:
    st.set_page_config(page_title="花大爷 × 不差儿", layout="wide")

# --- 2. 数据库配置与工具函数 ---
SUPABASE_URL = "https://hjrvdusefkjtmucsreeq.supabase.co"
SUPABASE_KEY = "sb_publishable_yDO1V8a3qYz8YPSzXSHdWA_mhpQG8QF"
TIFFANY_BLUE = "#0ABAB5"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

def safe_float(v, default=0.0):
    try:
        if v is None or str(v).strip() == "" or str(v).lower() == "none":
            return float(default)
        return float(v)
    except: return float(default)

# --- 3. 核心 CSS：强制移动端并排 + 深色文字 ---
st.markdown(f"""
    <style>
    /* 1. 强制手机端并排：阻止自动换行 */
    [data-testid="stHorizontalBlock"] {{
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: flex-start !important;
        gap: 0.5rem !important;
    }}
    
    [data-testid="column"] {{
        width: 50% !important;
        flex: 1 1 50% !important;
        min-width: 50% !important;
    }}

    /* 2. 强制锁定黑字，防止手机深色模式乱码 */
    html, body, [data-testid="stAppViewContainer"], .stMarkdown, p, span, label, div, .stMetricValue {{
        color: #1A1A1A !important;
        font-family: sans-serif !important;
    }}

    .stApp {{ background-color: #F0F9F9; }}
    
    .card {{
        background-color: white; padding: 12px; border-radius: 12px;
        border-top: 4px solid {TIFFANY_BLUE}; box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }}
    
    .stButton>button {{
        background-color: {TIFFANY_BLUE}; color: white !important;
        border-radius: 8px; width: 100%; border: none; font-size: 14px;
    }}

    /* 手机端专门微调 */
    @media (max-width: 640px) {{
        .card {{ padding: 8px; }}
        h3 {{ font-size: 14px !important; }}
        .stMetricValue {{ font-size: 18px !important; }}
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. 身份登录 ---
if 'user_role' not in st.session_state:
    if os.path.exists(icon_path):
        st.image(icon_path, width=100)
    st.markdown('<div class="card"><h3>👤 确认身份进入</h3>', unsafe_allow_html=True)
    role = st.radio("选择我是：", ["不差儿", "花大爷"], horizontal=True)
    if st.button("进入系统"):
        st.session_state.user_role = role
        st.rerun()
    st.stop()

my_name = st.session_state.user_role
other_name = "花大爷" if my_name == "不差儿" else "不差儿"

# --- 5. 统一渲染函数 ---
def render_column(name, col, editable, base_info):
    try:
        l_res = supabase.table("daily_logs").select("*").eq("user_name", name).eq("log_date", str(date.today())).execute()
        log = l_res.data[0] if l_res.data else {}
        # 累计打卡天数
        all_logs = supabase.table("daily_logs").select("log_date").eq("user_name", name).execute()
        streak = len({item['log_date'] for item in all_logs.data}) if all_logs.data else 0
    except: log, streak = {}, 0

    with col:
        st.markdown(f"### {'👩‍𝓠' if name=='不差儿' else '👨‍🦳'} {name}")
        st.markdown(f"<p style='text-align:center; font-size:12px;'>🔥 打卡 {streak} 天</p>", unsafe_allow_html=True)
        
        if not base_info:
            st.info("尚未初始化")
            return

        # 身体维度卡
        st.markdown('<div class="card"><b>📊 身体维度</b>', unsafe_allow_html=True)
        w = safe_float(log.get("weight", base_info.get("weight", 60.0)))
        weight = st.number_input("体重", value=w, key=f"w_{name}", disabled=not editable)
        
        # 缩小围度布局
        g1, g2 = st.columns(2)
        waist = g1.number_input("腰", value=safe_float(log.get("waist")), key=f"wa_{name}", disabled=not editable)
        thigh = g2.number_input("腿", value=safe_float(log.get("thigh")), key=f"th_{name}", disabled=not editable)
        
        if st.button("💾 保存", key=f"sv_{name}", disabled=not editable):
            try:
                supabase.table("daily_logs").upsert({
                    "user_name": name, "log_date": str(date.today()),
                    "weight": weight, "waist": waist, "thigh": thigh
                }, on_conflict="user_name,log_date").execute()
                st.rerun()
            except Exception as e: st.error(f"保存报错: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

        # 运动消耗卡
        st.markdown('<div class="card"><b>🏃 运动</b>', unsafe_allow_html=True)
        ex_burn = safe_float(log.get('calorie_burn', 0.0))
        st.metric("消耗", f"{int(ex_burn)} kcal")
        ex_d = st.number_input("时长(min)", value=int(safe_float(log.get('ex_duration'))), key=f"exd_{name}", disabled=not editable)
        if st.button("⚡ 同步", key=f"exb_{name}", disabled=not editable):
            burnt = safe_float(ex_d * 7.5) # 模拟计算
            supabase.table("daily_logs").upsert({"user_name": name, "log_date": str(date.today()), "calorie_burn": burnt, "ex_duration": ex_d}, on_conflict="user_name,log_date").execute()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- 6. 首页逻辑 ---
try:
    me_data = supabase.table("users").select("*").eq("name", my_name).execute().data[0]
    friend_res = supabase.table("users").select("*").eq("name", other_name).execute()
    friend_data = friend_res.data[0] if friend_res.data else None
except:
    st.error("请先完成资料初始化")
    st.stop()

st.image(icon_path, width=80) if os.path.exists(icon_path) else None

# 渲染左右分栏 (强制并排)
col_l, col_r = st.columns(2)
render_column("不差儿", col_l, editable=(my_name == "不差儿"), base_info=friend_data)
render_column("花大爷", col_r, editable=(my_name == "花大爷"), base_info=me_data)

if st.sidebar.button("退出登录"):
    st.session_state.clear()
    st.rerun()
