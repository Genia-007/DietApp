# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, date
import random
import os
import base64
from PIL import Image

# --- 1. 页面配置与苹果/安卓主屏幕图标强制注入 (修复 Logo 问题) ---
icon_path = "app_icon.png"

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

try:
    if os.path.exists(icon_path):
        img_b64 = get_base64_of_bin_file(icon_path)
        # 这里的 HTML 注入是为了让“添加到主屏幕”时识别你的自定义 Logo
        st.markdown(f"""
            <head>
                <link rel="apple-touch-icon" href="data:image/png;base64,{img_b64}">
                <link rel="icon" type="image/png" href="data:image/png;base64,{img_b64}">
                <meta name="apple-mobile-web-app-capable" content="yes">
                <meta name="apple-mobile-web-app-status-bar-style" content="default">
            </head>
            """, unsafe_allow_html=True)
        st.set_page_config(page_title="花大爷 × 不差儿", page_icon=Image.open(icon_path), layout="wide")
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

# --- 3. 核心 CSS：极致压缩空间、防止拖拽、强制并排、黑字锁定 ---
st.markdown(f"""
    <style>
    /* 1. 强制手机端并排且不溢出，允许内容极度压缩 */
    [data-testid="stHorizontalBlock"] {{
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        width: 100% !important;
        gap: 0.1rem !important;
    }}
    
    [data-testid="column"] {{
        width: 50% !important;
        flex: 1 1 50% !important;
        min-width: 0 !important;
        overflow: hidden !important;
    }}

    /* 2. 锁定文字颜色，无视系统主题 */
    html, body, [data-testid="stAppViewContainer"], .stMarkdown, p, span, label, div, .stMetricValue {{
        color: #1A1A1A !important;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif !important;
    }}

    .stApp {{ background-color: #F0F9F9; overflow-x: hidden !important; }}
    
    /* 3. 极简卡片与输入框缩小 */
    .card {{
        background-color: white; padding: 6px; border-radius: 8px;
        border-top: 3px solid {TIFFANY_BLUE}; box-shadow: 0 1px 4px rgba(0,0,0,0.05);
        margin-bottom: 6px;
    }}
    
    /* 缩小所有输入框、按钮、间距 */
    .stNumberInput input {{ padding: 2px 5px !important; height: 28px !important; font-size: 11px !important; }}
    .stTextInput input {{ height: 28px !important; font-size: 11px !important; }}
    .stButton>button {{
        background-color: {TIFFANY_BLUE}; color: white !important;
        border-radius: 6px; width: 100%; border: none; font-size: 10px !important; 
        padding: 2px !important; min-height: 24px !important;
    }}

    /* 4. 针对小屏幕的极致字体缩放 */
    @media (max-width: 640px) {{
        .stMetricValue {{ font-size: 14px !important; }}
        .stMarkdown p, label {{ font-size: 10px !important; line-height: 1.1 !important; }}
        h3 {{ font-size: 12px !important; margin: 2px 0 !important; }}
        .stImage {{ width: 60px !important; }} /* 缩略图变小 */
        [data-testid="stMetricLabel"] p {{ font-size: 9px !important; }}
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. 身份登录 ---
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

# --- 5. 顶栏逻辑 ---
if os.path.exists(icon_path):
    st.image(icon_path, width=60)

try:
    total_res = supabase.table("daily_logs").select("log_date").execute()
    total_days = len({item['log_date'] for item in total_res.data}) if total_res.data else 1
except: total_days = 1

view_date = st.date_input("📅 日期", date.today())
st.markdown(f"<p style='font-size:10px; text-align:center;'>🔥 打卡: {total_days}天 | {view_date}</p>", unsafe_allow_html=True)

# --- 6. 统一渲染函数 (所有功能保留，极致压缩空间) ---
def render_column(name, col, editable, base_info):
    try:
        l_res = supabase.table("daily_logs").select("*").eq("user_name", name).eq("log_date", str(view_date)).execute()
        log = l_res.data[0] if l_res.data else {}
    except: log = {}

    with col:
        st.markdown(f"### {'👩‍' if name=='不差儿' else '👨'} {name}")
        if not base_info:
            st.info("待初始化")
            return

        h = safe_float(base_info.get('height', 165.0))
        w_init = safe_float(base_info.get('weight', 60.0))
        age = safe_float(base_info.get('age', 24.0))

        # (1) 指标与维度 - 紧凑型
        st.markdown('<div class="card"><b>📊 维度</b>', unsafe_allow_html=True)
        w = st.number_input("体重", value=safe_float(log.get("weight", w_init)), key=f"w_{name}", disabled=not editable)
        
        c1, c2 = st.columns(2)
        waist = c1.number_input("腰", value=safe_float(log.get("waist")), key=f"wa_{name}", disabled=not editable)
        hip = c2.number_input("臀", value=safe_float(log.get("hip")), key=f"hi_{name}", disabled=not editable)
        thigh = c1.number_input("腿", value=safe_float(log.get("thigh")), key=f"th_{name}", disabled=not editable)
        calf = c2.number_input("小", value=safe_float(log.get("calf")), key=f"ca_{name}", disabled=not editable)
        arm = c1.number_input("臂", value=safe_float(log.get("arm")), key=f"ar_{name}", disabled=not editable)
        chest = c2.number_input("胸", value=safe_float(log.get("chest")), key=f"ch_{name}", disabled=not editable)

        if st.button("💾 保存", key=f"sv_{name}", disabled=not editable):
            try:
                supabase.table("daily_logs").upsert({
                    "user_name": name, "log_date": str(view_date), "weight": w,
                    "waist": waist, "hip": hip, "thigh": thigh, "calf": calf, "arm": arm, "chest": chest
                }, on_conflict="user_name,log_date").execute()
                st.rerun()
            except: st.error("！")
        
        m_opt = st.selectbox("趋势", ["weight", "waist", "thigh"], key=f"opt_{name}")
        if st.button("📈 图表", key=f"tr_{name}"):
            hist = supabase.table("daily_logs").select("*").eq("user_name", name).order("log_date").execute()
            df = pd.DataFrame(hist.data)
            if not df.empty: st.line_chart(df.set_index("log_date")[m_opt])
        st.markdown('</div>', unsafe_allow_html=True)

        # (2) 饮食与 AI
        st.markdown('<div class="card"><b>🍱 饮食</b>', unsafe_allow_html=True)
        consumed = safe_float(log.get('calorie_intake', 0))
        st.metric("摄入", f"{int(consumed)}k", label_visibility="collapsed")
        
        f_img = st.file_uploader("📷", type=['jpg','png'], key=f"fd_{name}", disabled=not editable, label_visibility="collapsed")
        if f_img: st.image(f_img, width=50)
        if st.button("🚀 AI", key=f"ai_{name}", disabled=not editable):
            add_c = float(random.randint(300, 600))
            supabase.table("daily_logs").upsert({"user_name": name, "log_date": str(view_date), "calorie_intake": consumed + add_c}, on_conflict="user_name,log_date").execute()
            st.rerun()

        burn = safe_float(log.get('calorie_burn', 0))
        st.metric("消耗", f"{int(burn)}k", label_visibility="collapsed")
        ex_d = st.number_input("时长", value=int(safe_float(log.get('ex_duration'))), key=f"exd_{name}", disabled=not editable)
        if st.button("⚡ 计算", key=f"exb_{name}", disabled=not editable):
            burnt = ex_d * random.uniform(6.0, 9.0)
            supabase.table("daily_logs").upsert({"user_name": name, "log_date": str(view_date), "calorie_burn": burnt, "ex_duration": ex_d}, on_conflict="user_name,log_date").execute()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # (3) 心得
        st.markdown('<div class="card"><b>💭 心得</b>', unsafe_allow_html=True)
        note = st.text_area("...", value=str(log.get('note', '')), key=f"nt_{name}", disabled=not editable, height=40)
        if st.button("发布", key=f"ntb_{name}", disabled=not editable):
            supabase.table("daily_logs").upsert({"user_name": name, "log_date": str(view_date), "note": note}, on_conflict="user_name,log_date").execute()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- 7. 渲染对垒布局 ---
try:
    me_data = supabase.table("users").select("*").eq("name", my_name).execute().data[0]
    friend_res = supabase.table("users").select("*").eq("name", other_name).execute()
    friend_data = friend_res.data[0] if friend_res.data else None
except:
    st.info("请初始化")
    st.stop()

col_l, col_r = st.columns(2)
render_column("不差儿", col_l, editable=(my_name == "不差儿"), base_info=friend_data)
render_column("花大爷", col_r, editable=(my_name == "花大爷"), base_info=me_data)

if st.sidebar.button("登出"):
    st.session_state.clear()
    st.rerun()
