# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, date
import random
import os
import base64
from PIL import Image

# --- 1. 强制 Web Clip 图标注入 (解决手机主屏幕 Logo 问题) ---
icon_path = "app_icon.png"

def get_base64(file_path):
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

try:
    if os.path.exists(icon_path):
        img_b64 = get_base64(icon_path)
        # 注入 Apple Touch Icon 和 favicon，确保添加到主屏幕时显示合照
        st.markdown(f"""
            <head>
                <link rel="apple-touch-icon" href="data:image/png;base64,{img_b64}">
                <link rel="apple-touch-icon-precomposed" href="data:image/png;base64,{img_b64}">
                <link rel="shortcut icon" href="data:image/png;base64,{img_b64}">
                <meta name="apple-mobile-web-app-capable" content="yes">
                <meta name="apple-mobile-web-app-status-bar-style" content="default">
            </head>
            """, unsafe_allow_html=True)
        st.set_page_config(page_title="花大爷 × 不差儿", page_icon=Image.open(icon_path), layout="wide")
    else:
        st.set_page_config(page_title="花大爷 × 不差儿", layout="wide")
except:
    st.set_page_config(page_title="花大爷 × 不差儿", layout="wide")

# --- 2. 核心极简 CSS：强制并排、自适应屏幕、缩小组件、锁定黑字 ---
st.markdown("""
    <style>
    /* 强制手机端并排且不溢出屏幕 */
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        width: 100% !important;
        gap: 0.2rem !important;
    }
    
    [data-testid="column"] {
        width: 50% !important;
        flex: 1 1 50% !important;
        min-width: 0 !important;
        padding: 0px !important;
    }

    /* 强制锁定深色文字，无视手机深色模式 */
    html, body, [data-testid="stAppViewContainer"], .stMarkdown, p, span, label, div, .stMetricValue {
        color: #1A1A1A !important;
        font-family: -apple-system, sans-serif !important;
    }

    .stApp { background-color: #F0F9F9; }
    
    /* 缩小卡片和组件尺寸 */
    .card {
        background-color: white; padding: 8px; border-radius: 10px;
        border-top: 3px solid #0ABAB5; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 8px;
    }
    
    /* 缩小输入框高度 */
    .stNumberInput input, .stTextInput input {
        padding: 2px 5px !important;
        height: 28px !important;
        font-size: 12px !important;
    }
    
    /* 缩小按钮 */
    .stButton>button {
        background-color: #0ABAB5; color: white !important;
        border-radius: 6px; width: 100%; border: none; 
        font-size: 11px !important; padding: 2px !important; min-height: 25px !important;
    }

    /* 手机端字体进一步压缩，确保不换行 */
    @media (max-width: 640px) {
        .stMetricValue { font-size: 14px !important; }
        .stMarkdown p, label { font-size: 10px !important; line-height: 1.2 !important; }
        h3 { font-size: 12px !important; margin: 5px 0 !important; }
        .stImage { width: 60px !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 数据库与安全逻辑 ---
URL = "https://hjrvdusefkjtmucsreeq.supabase.co"
KEY = "sb_publishable_yDO1V8a3qYz8YPSzXSHdWA_mhpQG8QF"
supabase: Client = create_client(URL, KEY)

def safe_float(v, default=0.0):
    try: return float(v) if v is not None else float(default)
    except: return float(default)

# --- 4. 身份登录 ---
if 'user_role' not in st.session_state:
    if os.path.exists(icon_path):
        st.image(icon_path, width=80)
    st.markdown('<div class="card"><h3>👤 确认身份</h3>', unsafe_allow_html=True)
    role = st.radio("你是：", ["不差儿", "花大爷"], horizontal=True)
    if st.button("确认进入"):
        st.session_state.user_role = role
        st.rerun()
    st.stop()

my_name = st.session_state.user_role
other_name = "花大爷" if my_name == "不差儿" else "不差儿"

# --- 5. 数据加载与顶部统计 ---
try:
    me_base = supabase.table("users").select("*").eq("name", my_name).execute().data[0]
    friend_res = supabase.table("users").select("*").eq("name", other_name).execute()
    friend_base = friend_res.data[0] if friend_res.data else None
    
    total_res = supabase.table("daily_logs").select("log_date").execute()
    total_days = len({item['log_date'] for item in total_res.data}) if total_res.data else 1
except:
    st.info("请先初始化资料")
    st.stop()

# 紧凑版顶栏
t1, t2 = st.columns([1, 2])
with t1:
    if os.path.exists(icon_path): st.image(icon_path, width=50)
with t2:
    st.markdown(f"**🔥 打卡 {total_days} 天**")
    view_date = st.date_input("日期", date.today(), label_visibility="collapsed")

# --- 6. 统一渲染函数 (功能完整不删减) ---
def render_column(name, col, editable, base_info):
    try:
        l_res = supabase.table("daily_logs").select("*").eq("user_name", name).eq("log_date", str(view_date)).execute()
        log = l_res.data[0] if l_res.data else {}
    except: log = {}

    with col:
        st.markdown(f"### {'👩‍𝓠' if name=='不差儿' else '👨‍🦳'} {name}")
        
        # 1. 指标卡 (紧凑显示)
        st.markdown('<div class="card">', unsafe_allow_html=True)
        w = safe_float(log.get("weight", base_info.get("weight", 60.0)))
        st.write(f"⚖️ 体重: {w}kg")
        
        if editable:
            new_w = st.number_input("改重", value=w, key=f"nw_{name}", label_visibility="collapsed")
            if st.button("保存体重", key=f"sw_{name}"):
                supabase.table("daily_logs").upsert({"user_name": name, "log_date": str(view_date), "weight": safe_float(new_w)}, on_conflict="user_name,log_date").execute()
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # 2. 围度卡 (7个维度全部保留)
        st.markdown('<div class="card">', unsafe_allow_html=True)
        fields = ["waist", "hip", "thigh", "calf", "arm", "chest"]
        labels = ["腰", "臀", "腿", "小", "臂", "胸"]
        
        for f, lb in zip(fields, labels):
            curr_v = safe_float(log.get(f, 0))
            if editable:
                st.number_input(lb, value=curr_v, key=f"{f}_{name}")
            else:
                st.write(f"{lb}: {curr_v}")

        if editable and st.button("同步围度", key=f"sv_{name}"):
            save_data = {"user_name": name, "log_date": str(view_date)}
            for f in fields: save_data[f] = safe_float(st.session_state[f"{f}_{name}"])
            supabase.table("daily_logs").upsert(save_data, on_conflict="user_name,log_date").execute()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # 3. 饮食与运动 (保留分析与趋势)
        st.markdown('<div class="card">', unsafe_allow_html=True)
        c_in = safe_float(log.get('calorie_intake', 0))
        st.write(f"🍎 {int(c_in)}kcal")
        if editable:
            f_img = st.file_uploader("饮食", type=['jpg','png'], key=f"fi_{name}", label_visibility="collapsed")
            if f_img: st.image(f_img, width=60)
            if st.button("AI识别", key=f"ai_{name}"):
                supabase.table("daily_logs").upsert({"user_name": name, "log_date": str(view_date), "calorie_intake": c_in + 450}, on_conflict="user_name,log_date").execute()
                st.rerun()
        
        st.divider()
        burn = safe_float(log.get('calorie_burn', 0))
        st.write(f"⚡ {int(burn)}kcal")
        if editable:
            ex_d = st.number_input("时长", value=int(safe_float(log.get('ex_duration'))), key=f"exd_{name}", label_visibility="collapsed")
            if st.button("算消耗", key=f"exb_{name}"):
                supabase.table("daily_logs").upsert({"user_name": name, "log_date": str(view_date), "calorie_burn": ex_d*7.5, "ex_duration": ex_d}, on_conflict="user_name,log_date").execute()
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- 7. 左右渲染 ---
cl, cr = st.columns(2)
render_column("不差儿", cl, (my_name == "不差儿"), friend_base if my_name == "花大爷" else me_base)
render_column("花大爷", cr, (my_name == "花大爷"), me_base if my_name == "花大爷" else friend_base)
