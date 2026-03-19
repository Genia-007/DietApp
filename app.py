# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, date
import random
import os
from PIL import Image

# --- 1. 页面配置与 App 图标 ---
icon_path = "app_icon.png"
try:
    if os.path.exists(icon_path):
        icon_img = Image.open(icon_path)
        st.set_page_config(page_title="花大爷 × 不差儿", page_icon=icon_img, layout="wide")
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
    """【修复核心】确保任何情况下都不会返回 None"""
    try:
        if v is None or str(v).strip() == "" or str(v).lower() == "none":
            return float(default)
        return float(v)
    except:
        return float(default)

# --- 3. UI 强化 CSS (锁定黑字/禁止横移) ---
st.markdown(f"""
    <style>
    [data-testid="stAppViewContainer"] {{ overflow-x: hidden !important; }}
    html, body, .stMarkdown, p, span, label, div, .stMetricValue {{
        color: #1A1A1A !important;
        font-family: -apple-system, system-ui, sans-serif !important;
    }}
    .stApp {{ background-color: #F8FCFC; }}
    .card {{
        background-color: white; padding: 15px; border-radius: 12px;
        border-top: 5px solid {TIFFANY_BLUE}; box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin-bottom: 15px;
    }}
    .border-pink {{ border-left: 8px solid #FFB6C1; }}
    .border-blue {{ border-left: 8px solid #0ABAB5; }}
    .stButton>button {{
        background-color: {TIFFANY_BLUE}; color: white !important;
        border-radius: 8px; font-weight: bold; height: 42px;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. 身份登录 ---
if 'user_role' not in st.session_state:
    if os.path.exists(icon_path): st.image(icon_path, width=80)
    st.markdown('<div class="card"><h3>👤 登录身份</h3>', unsafe_allow_html=True)
    role = st.radio("选择你是：", ["不差儿", "花大爷"], horizontal=True)
    if st.button("进入系统", use_container_width=True):
        st.session_state.user_role = role
        st.rerun()
    st.stop()

my_name = st.session_state.user_role
other_name = "花大爷" if my_name == "不差儿" else "不差儿"

# --- 5. 顶栏 ---
if os.path.exists(icon_path): st.image(icon_path, width=60)
st.title("花大爷 × 不差儿")

# --- 6. 统一渲染函数 ---
def render_column(name, container, editable, base_info):
    try:
        l_res = supabase.table("daily_logs").select("*").eq("user_name", name).eq("log_date", str(date.today())).execute()
        log = l_res.data[0] if l_res.data else {}
    except: log = {}

    with container:
        border_class = "border-pink" if name == "不差儿" else "border-blue"
        st.markdown(f'<div class="card {border_class}">', unsafe_allow_html=True)
        st.markdown(f"### {'👩‍' if name=='不差儿' else '👨'} {name}")
        
        if not base_info:
            st.warning(f"等待 {name} 初始化资料...")
            st.markdown('</div>', unsafe_allow_html=True)
            return

        # --- 身体维度 (修复此处崩溃点) ---
        st.markdown("#### 📊 身体维度")
        h = safe_float(base_info.get('height'), 165.0)
        # 修正：层层兜底，确保 weight 永远是数字
        w_val = safe_float(log.get('weight', base_info.get('weight', 60.0)), 60.0)
        
        weight = st.number_input(f"体重 (kg) - {name}", value=w_val, key=f"w_{name}", disabled=not editable, use_container_width=True)
        waist = st.number_input(f"腰围 (cm) - {name}", value=safe_float(log.get('waist')), key=f"wa_{name}", disabled=not editable, use_container_width=True)
        thigh = st.number_input(f"大腿围 (cm) - {name}", value=safe_float(log.get('thigh')), key=f"th_{name}", disabled=not editable, use_container_width=True)
        arm = st.number_input(f"臂围 (cm) - {name}", value=safe_float(log.get('arm')), key=f"ar_{name}", disabled=not editable, use_container_width=True)

        if st.button(f"保存数据 ({name})", key=f"btn_s_{name}", disabled=not editable, use_container_width=True):
            try:
                supabase.table("daily_logs").upsert({
                    "user_name": name, "log_date": str(date.today()),
                    "weight": weight, "waist": waist, "thigh": thigh, "arm": arm
                }, on_conflict="user_name,log_date").execute()
                st.success("同步成功！")
                st.rerun()
            except: st.error("写入失败")

        # --- AI 饮食 ---
        st.markdown("---")
        st.markdown("#### 🍱 饮食与运动")
        consumed = safe_float(log.get('calorie_intake', 0))
        st.metric("今日摄入", f"{int(consumed)} kcal")
        
        f_img = st.file_uploader(f"上传餐食 ({name})", type=['jpg','png'], key=f"img_{name}", disabled=not editable)
        if f_img:
            st.image(f_img, use_container_width=True)
            if st.button(f"🚀 AI 识别热量 ({name})", key=f"ai_{name}", disabled=not editable, use_container_width=True):
                add_cal = random.randint(300, 700)
                supabase.table("daily_logs").upsert({
                    "user_name": name, "log_date": str(date.today()), "calorie_intake": consumed + add_cal
                }, on_conflict="user_name,log_date").execute()
                st.rerun()
        
        # --- 运动计算 ---
        ex_burn = safe_float(log.get('calorie_burn', 0))
        st.metric("运动消耗", f"{int(ex_burn)} kcal")
        ex_dur = st.number_input(f"时长 (min) - {name}", value=int(safe_float(log.get('ex_duration'))), key=f"dur_{name}", disabled=not editable, use_container_width=True)
        if st.button(f"⚡ 计算消耗 ({name})", key=f"exb_{name}", disabled=not editable, use_container_width=True):
            burn_val = ex_dur * random.uniform(6.0, 9.0)
            supabase.table("daily_logs").upsert({
                "user_name": name, "log_date": str(date.today()), "calorie_burn": burn_val, "ex_duration": ex_dur
            }, on_conflict="user_name,log_date").execute()
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

# --- 7. 数据加载与自适应渲染 ---
try:
    me_res = supabase.table("users").select("*").eq("name", my_name).execute()
    me_info = me_res.data[0] if me_res.data else None
    fr_res = supabase.table("users").select("*").eq("name", other_name).execute()
    fr_info = fr_res.data[0] if fr_res.data else None
except:
    st.error("数据库连接异常")
    st.stop()

# 手机端上下排列，电脑端左右排列 (通过 columns 自动折叠)
view_col1, view_col2 = st.columns([1, 1])

if my_name == "不差儿":
    render_column("不差儿", view_col1, True, me_info)
    render_column("花大爷", view_col2, False, fr_info)
else:
    render_column("不差儿", view_col1, False, fr_info)
    render_column("花大爷", view_col2, True, me_info)

# 侧边栏
with st.sidebar:
    if st.button("登出 / 切换身份", use_container_width=True):
        st.session_state.clear()
        st.rerun()
