# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, date
import random
import os
import base64
from PIL import Image

# --- 1. 基础配置与图标加载 (彻底修复开头乱码) ---
icon_path = "app_icon.png"
try:
    if os.path.exists(icon_path):
        icon_img = Image.open(icon_path)
        st.set_page_config(page_title="花大爷 × 不差儿", page_icon=icon_img, layout="wide")
    else:
        st.set_page_config(page_title="花大爷 × 不差儿", layout="wide")
except:
    st.set_page_config(page_title="花大爷 × 不差儿", layout="wide")

# --- 2. 数据库配置与安全转换 ---
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

# --- 3. 核心 CSS：强制并排 + 完美自适应屏幕 + 深色文字 ---
st.markdown(f"""
    <style>
    /* 1. 强制手机端并排且不溢出 */
    [data-testid="stHorizontalBlock"] {{
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        width: 100% !important;
        gap: 0.3rem !important;
    }}
    
    [data-testid="column"] {{
        width: 50% !important;
        flex: 1 1 50% !important;
        min-width: 0 !important; /* 关键：允许列收缩，不撑破屏幕 */
        overflow: hidden;
    }}

    /* 2. 锁定文字颜色，解决看不清问题 */
    html, body, [data-testid="stAppViewContainer"], .stMarkdown, p, span, label, div, .stMetricValue {{
        color: #1A1A1A !important;
        font-family: sans-serif !important;
    }}

    .stApp {{ background-color: #F0F9F9; }}
    
    .card {{
        background-color: white; padding: 10px; border-radius: 12px;
        border-top: 4px solid {TIFFANY_BLUE}; box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }}
    
    .stButton>button {{
        background-color: {TIFFANY_BLUE}; color: white !important;
        border-radius: 8px; width: 100%; border: none; font-size: 12px; font-weight: bold;
    }}

    /* 3. 手机端字体极简化适配 */
    @media (max-width: 640px) {{
        .card {{ padding: 5px; }}
        .stMetricValue {{ font-size: 16px !important; }}
        .stMarkdown p, label {{ font-size: 11px !important; }}
        h3 {{ font-size: 13px !important; }}
        .stNumberInput input {{ font-size: 12px !important; }}
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. 身份登录 ---
if 'user_role' not in st.session_state:
    if os.path.exists(icon_path):
        st.image(icon_path, width=100)
    st.markdown('<div class="card"><h3>👤 确认身份</h3>', unsafe_allow_html=True)
    role = st.radio("选择我是：", ["不差儿", "花大爷"], horizontal=True)
    if st.button("进入系统"):
        st.session_state.user_role = role
        st.rerun()
    st.stop()

my_name = st.session_state.user_role
other_name = "花大爷" if my_name == "不差儿" else "不差儿"

# --- 5. 顶栏逻辑：修复 st.image 乱码 ---
if os.path.exists(icon_path):
    st.image(icon_path, width=80)

# 计算累计打卡
try:
    total_res = supabase.table("daily_logs").select("log_date").execute()
    total_days = len({item['log_date'] for item in total_res.data}) if total_res.data else 1
except: total_days = 1

view_date = st.date_input("📅 日期", date.today())
st.write(f"🔥 打卡共计: {total_days} 天 | {view_date}")

# --- 6. 统一渲染函数 (功能完整恢复) ---
def render_column(name, col, editable, base_info):
    try:
        l_res = supabase.table("daily_logs").select("*").eq("user_name", name).eq("log_date", str(view_date)).execute()
        log = l_res.data[0] if l_res.data else {}
    except: log = {}

    with col:
        st.markdown(f"### {'👩‍𝓠' if name=='不差儿' else '👨‍🦳'} {name}")
        if not base_info:
            st.info("待初始化")
            return

        h = safe_float(base_info.get('height', 165.0))
        w_init = safe_float(base_info.get('weight', 60.0))
        age = safe_float(base_info.get('age', 24.0))

        # (1) 维度模块 - 恢复 7 个维度
        st.markdown('<div class="card"><b>📊 维度</b>', unsafe_allow_html=True)
        w = st.number_input("体重", value=safe_float(log.get("weight", w_init)), key=f"w_{name}", disabled=not editable)
        
        # 左右对齐的维度
        c1, c2 = st.columns(2)
        waist = c1.number_input("腰", value=safe_float(log.get("waist")), key=f"wa_{name}", disabled=not editable)
        hip = c2.number_input("臀", value=safe_float(log.get("hip")), key=f"hi_{name}", disabled=not editable)
        thigh = c1.number_input("腿", value=safe_float(log.get("thigh")), key=f"th_{name}", disabled=not editable)
        calf = c2.number_input("小", value=safe_float(log.get("calf")), key=f"ca_{name}", disabled=not editable)
        arm = c1.number_input("臂", value=safe_float(log.get("arm")), key=f"ar_{name}", disabled=not editable)
        chest = c2.number_input("胸", value=safe_float(log.get("chest")), key=f"ch_{name}", disabled=not editable)

        if st.button("💾 保存资料", key=f"sv_{name}", disabled=not editable):
            try:
                supabase.table("daily_logs").upsert({
                    "user_name": name, "log_date": str(view_date), "weight": w,
                    "waist": waist, "hip": hip, "thigh": thigh, "calf": calf, "arm": arm, "chest": chest
                }, on_conflict="user_name,log_date").execute()
                st.rerun()
            except Exception as e: st.error(f"失败: {e}")
        
        # 趋势功能回归
        m_opt = st.selectbox("趋势", ["weight", "waist", "thigh"], key=f"opt_{name}")
        if st.button("查看图表 📈", key=f"tr_{name}"):
            hist = supabase.table("daily_logs").select("*").eq("user_name", name).order("log_date").execute()
            df = pd.DataFrame(hist.data)
            if not df.empty: st.line_chart(df.set_index("log_date")[m_opt])
        st.markdown('</div>', unsafe_allow_html=True)

        # (2) 饮食与运动消耗回归
        st.markdown('<div class="card"><b>🍱 饮食/运动</b>', unsafe_allow_html=True)
        consumed = safe_float(log.get('calorie_intake', 0))
        st.metric("已摄入", f"{int(consumed)} kcal")
        
        f_img = st.file_uploader("📷 饮食", type=['jpg','png'], key=f"fd_{name}", disabled=not editable, label_visibility="collapsed")
        if f_img: st.image(f_img, width=80)
        if st.button("🚀 AI 识别", key=f"ai_{name}", disabled=not editable):
            add_c = float(random.randint(300, 600))
            supabase.table("daily_logs").upsert({"user_name": name, "log_date": str(view_date), "calorie_intake": consumed + add_c}, on_conflict="user_name,log_date").execute()
            st.rerun()

        st.divider()
        burn = safe_float(log.get('calorie_burn', 0))
        st.metric("运动消耗", f"{int(burn)} kcal")
        ex_d = st.number_input("时长(min)", value=int(safe_float(log.get('ex_duration'))), key=f"exd_{name}", disabled=not editable)
        if st.button("⚡ 计算消耗", key=f"exb_{name}", disabled=not editable):
            burnt = ex_d * random.uniform(6.0, 9.0)
            supabase.table("daily_logs").upsert({"user_name": name, "log_date": str(view_date), "calorie_burn": burnt, "ex_duration": ex_d}, on_conflict="user_name,log_date").execute()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # (3) 健康心得回归
        st.markdown('<div class="card"><b>💭 心得</b>', unsafe_allow_html=True)
        note = st.text_area("记录...", value=str(log.get('note', '')), key=f"nt_{name}", disabled=not editable, height=80)
        if st.button("💾 发布", key=f"ntb_{name}", disabled=not editable):
            supabase.table("daily_logs").upsert({"user_name": name, "log_date": str(view_date), "note": note}, on_conflict="user_name,log_date").execute()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- 7. 渲染对垒布局 ---
try:
    me_data = supabase.table("users").select("*").eq("name", my_name).execute().data[0]
    friend_res = supabase.table("users").select("*").eq("name", other_name).execute()
    friend_data = friend_res.data[0] if friend_res.data else None
except:
    st.info("请先初始化资料")
    st.stop()

col_l, col_r = st.columns(2)
render_column("不差儿", col_l, editable=(my_name == "不差儿"), base_info=friend_data)
render_column("花大爷", col_r, editable=(my_name == "花大爷"), base_info=me_data)

if st.sidebar.button("登出"):
    st.session_state.clear()
    st.rerun()
