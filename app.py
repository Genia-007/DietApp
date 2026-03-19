# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, date
import random
import os
import base64
from PIL import Image

# --- 1. 页面配置与 Logo 注入 ---
icon_path = "app_icon.png"

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

try:
    if os.path.exists(icon_path):
        img_b64 = get_base64_of_bin_file(icon_path)
        st.markdown(f"""
            <head>
                <link rel="apple-touch-icon" href="data:image/png;base64,{img_b64}">
                <link rel="icon" type="image/png" href="data:image/png;base64,{img_b64}">
                <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
            </head>
            """, unsafe_allow_html=True)
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

# --- 3. 终极 CSS：解决横向溢出，强制适应屏幕 ---
st.markdown(f"""
    <style>
    /* 核心：禁止全局左右滑动 */
    html, body, [data-testid="stAppViewContainer"] {{
        overflow-x: hidden !important;
        width: 100vw !important;
        margin: 0 !important;
        padding: 0 !important;
    }}

    /* 强制列容器 100% 宽度且不换行 */
    [data-testid="stHorizontalBlock"] {{
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        width: 100% !important;
        gap: 4px !important;
        padding: 0 4px !important;
    }}
    
    /* 强制每一列只占一半，且绝对不允许撑开 */
    [data-testid="column"] {{
        flex: 1 1 50% !important;
        min-width: 0 !important;
        max-width: 50% !important;
        overflow: hidden !important;
    }}

    /* 文字与背景 */
    html, body, .stMarkdown, p, span, label, div, .stMetricValue {{
        color: #1A1A1A !important;
        font-family: -apple-system, system-ui, sans-serif !important;
    }}
    .stApp {{ background-color: #F0F9F9; }}
    
    /* 卡片压缩 */
    .card {{
        background-color: white; padding: 8px; border-radius: 8px;
        border-top: 3px solid {TIFFANY_BLUE}; box-shadow: 0 1px 4px rgba(0,0,0,0.05);
        margin-bottom: 8px;
        width: 100% !important;
    }}
    
    /* 控件极致缩小：防止撑破容器 */
    .stNumberInput, .stTextInput, .stSelectbox {{
        width: 100% !important;
    }}
    .stNumberInput input {{ height: 26px !important; font-size: 11px !important; padding: 2px !important; }}
    .stButton>button {{
        background-color: {TIFFANY_BLUE}; color: white !important;
        border-radius: 6px; font-size: 10px !important; 
        padding: 0 !important; min-height: 24px !important;
    }}

    /* 手机端字体适配 */
    @media (max-width: 640px) {{
        h3 {{ font-size: 12px !important; }}
        [data-testid="stMetricValue"] {{ font-size: 14px !important; }}
        label {{ font-size: 10px !important; }}
        .stImage {{ width: 50px !important; }}
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. 登录逻辑 ---
if 'user_role' not in st.session_state:
    if os.path.exists(icon_path):
        st.image(icon_path, width=80)
    st.markdown('<div class="card"><h3>👤 确认身份</h3>', unsafe_allow_html=True)
    role = st.radio("选择我是：", ["不差儿", "花大爷"], horizontal=True)
    if st.button("进入系统"):
        st.session_state.user_role = role
        st.rerun()
    st.stop()

my_name = st.session_state.user_role
other_name = "花大爷" if my_name == "不差儿" else "不差儿"

# --- 5. 顶栏与统计 ---
if os.path.exists(icon_path):
    st.image(icon_path, width=50)

try:
    total_res = supabase.table("daily_logs").select("log_date").execute()
    total_days = len({item['log_date'] for item in total_res.data}) if total_res.data else 1
except: total_days = 1

view_date = st.date_input("📅 日期", date.today())
st.markdown(f"<p style='font-size:10px; text-align:center;'>🔥 累计打卡: {total_days}天</p>", unsafe_allow_html=True)

# --- 6. 统一渲染函数 (全维度、全功能、左右对齐) ---
def render_column(name, col, editable, base_info):
    try:
        l_res = supabase.table("daily_logs").select("*").eq("user_name", name).eq("log_date", str(view_date)).execute()
        log = l_res.data[0] if l_res.data else {}
    except: log = {}

    with col:
        st.markdown(f"### {'👩' if name=='不差儿' else '👨'} {name}")
        if not base_info:
            st.info("待初始化")
            return

        h = safe_float(base_info.get('height', 165.0))
        w_init = safe_float(base_info.get('weight', 60.0))
        age = safe_float(base_info.get('age', 24.0))

        # (1) 身体维度
        st.markdown('<div class="card"><b>📊 维度</b>', unsafe_allow_html=True)
        w = st.number_input("体重", value=safe_float(log.get("weight", w_init)), key=f"w_{name}", disabled=not editable)
        
        c1, c2 = st.columns(2)
        waist = c1.number_input("腰", value=safe_float(log.get("waist")), key=f"wa_{name}", disabled=not editable)
        hip = c2.number_input("臀", value=safe_float(log.get("hip")), key=f"hi_{name}", disabled=not editable)
        thigh = c1.number_input("腿", value=safe_float(log.get("thigh")), key=f"th_{name}", disabled=not editable)
        calf = c2.number_input("小", value=safe_float(log.get("calf")), key=f"ca_{name}", disabled=not editable)
        arm = c1.number_input("臂", value=safe_float(log.get("arm")), key=f"ar_{name}", disabled=not editable)
        chest = c2.number_input("胸", value=safe_float(log.get("chest")), key=f"ch_{name}", disabled=not editable)

        if st.button("💾 保存", key=f"sv_{name}", disabled=not editable, use_container_width=True):
            try:
                supabase.table("daily_logs").upsert({
                    "user_name": name, "log_date": str(view_date), "weight": w,
                    "waist": waist, "hip": hip, "thigh": thigh, "calf": calf, "arm": arm, "chest": chest
                }, on_conflict="user_name,log_date").execute()
                st.rerun()
            except: st.error("保存失败")
        
        m_opt = st.selectbox("趋势", ["weight", "waist", "thigh"], key=f"opt_{name}")
        if st.button("📈 图表", key=f"tr_{name}", use_container_width=True):
            hist = supabase.table("daily_logs").select("*").eq("user_name", name).order("log_date").execute()
            df = pd.DataFrame(hist.data)
            if not df.empty: st.line_chart(df.set_index("log_date")[m_opt])
        st.markdown('</div>', unsafe_allow_html=True)

        # (2) 饮食打卡 (带图片缩略图)
        st.markdown('<div class="card"><b>🍱 饮食</b>', unsafe_allow_html=True)
        consumed = safe_float(log.get('calorie_intake', 0))
        st.metric("摄入", f"{int(consumed)} kcal")
        
        f_img = st.file_uploader("📷", type=['jpg','png'], key=f"fd_{name}", disabled=not editable, label_visibility="collapsed")
        if f_img: st.image(f_img, width=40)
        if st.button("🚀 AI 分析", key=f"ai_{name}", disabled=not editable, use_container_width=True):
            add_c = float(random.randint(300, 600))
            supabase.table("daily_logs").upsert({"user_name": name, "log_date": str(view_date), "calorie_intake": consumed + add_c}, on_conflict="user_name,log_date").execute()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # (3) 运动消耗
        st.markdown('<div class="card"><b>🏃 运动</b>', unsafe_allow_html=True)
        burn = safe_float(log.get('calorie_burn', 0))
        st.metric("消耗", f"{int(burn)} kcal")
        ex_d = st.number_input("时长", value=int(safe_float(log.get('ex_duration'))), key=f"exd_{name}", disabled=not editable)
        if st.button("⚡ 计算", key=f"exb_{name}", disabled=not editable, use_container_width=True):
            burnt = ex_d * random.uniform(6.0, 9.0)
            supabase.table("daily_logs").upsert({"user_name": name, "log_date": str(view_date), "calorie_burn": burnt, "ex_duration": ex_d}, on_conflict="user_name,log_date").execute()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # (4) 健康心得
        st.markdown('<div class="card"><b>💭 心得</b>', unsafe_allow_html=True)
        note = st.text_area("记录...", value=str(log.get('note', '')), key=f"nt_{name}", disabled=not editable, height=60)
        if st.button("💾 发布", key=f"ntb_{name}", disabled=not editable, use_container_width=True):
            supabase.table("daily_logs").upsert({"user_name": name, "log_date": str(view_date), "note": note}, on_conflict="user_name,log_date").execute()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- 7. 渲染对垒布局 (左右分栏) ---
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
