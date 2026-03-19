# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, date
import random
import os
from PIL import Image

# --- 1. 页面配置与 App 图标修复 (最高优先级) ---
icon_path = "app_icon.png"
try:
    if os.path.exists(icon_path):
        icon_img = Image.open(icon_path)
        st.set_page_config(
            page_title="花大爷 × 不差儿",
            page_icon=icon_img,
            layout="centered" # 移动端适配：强制居中布局
        )
    else:
        st.set_page_config(page_title="花大爷 × 不差儿", layout="centered")
except:
    st.set_page_config(page_title="花大爷 × 不差儿", layout="centered")

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

# --- 3. 移动端 UI 强化 CSS (禁止横向滚动) ---
st.markdown(f"""
    <style>
    /* 强制禁止横向溢出 */
    html, body, [data-testid="stAppViewContainer"] {{
        overflow-x: hidden !important;
        width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
    }}
    
    /* 锁定深色文字与背景 */
    .stApp {{ background-color: #F5FBFB; }}
    html, body, .stMarkdown, p, span, label, div, .stMetricValue {{
        color: #1A1A1A !important;
        font-family: -apple-system, system-ui, sans-serif !important;
    }}

    /* 移动端卡片样式 */
    .mobile-card {{
        background-color: white; 
        padding: 15px; 
        border-radius: 12px;
        border-left: 5px solid {TIFFANY_BLUE}; 
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }}
    
    /* 控件自适应宽度 */
    .stButton>button {{
        background-color: {TIFFANY_BLUE}; 
        color: white !important;
        border-radius: 8px; 
        width: 100%; 
        font-weight: bold;
        height: 45px;
    }}
    
    h3 {{ color: #088F8A !important; margin-top: 10px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. 身份登录逻辑 ---
if 'user_role' not in st.session_state:
    if os.path.exists(icon_path):
        st.image(icon_path, width=80)
    st.markdown('<div class="mobile-card"><h3>👤 身份登录</h3>', unsafe_allow_html=True)
    role = st.radio("请选择您的身份：", ["不差儿", "花大爷"], horizontal=True)
    if st.button("进入基地"):
        st.session_state.user_role = role
        st.rerun()
    st.stop()

my_name = st.session_state.user_role
other_name = "花大爷" if my_name == "不差儿" else "不差儿"

# --- 5. 顶栏信息 ---
if os.path.exists(icon_path):
    st.image(icon_path, width=80)

# 统计打卡天数
try:
    log_res = supabase.table("daily_logs").select("log_date").eq("user_name", my_name).execute()
    streak = len({item['log_date'] for item in log_res.data}) if log_res.data else 0
except: streak = 0

st.title("花大爷 × 不差儿")
st.write(f"📅 今日：{date.today()} | 🔥 已打卡：{streak}天")

# --- 6. 核心渲染逻辑 (纵向适配版) ---
def render_user_section(name, editable):
    # 获取数据
    try:
        u_res = supabase.table("users").select("*").eq("name", name).execute()
        base_info = u_res.data[0] if u_res.data else None
        l_res = supabase.table("daily_logs").select("*").eq("user_name", name).eq("log_date", str(date.today())).execute()
        log = l_res.data[0] if l_res.data else {}
    except: base_info, log = None, {}

    st.markdown(f"## {'👩‍𝓠' if name=='不差儿' else '👨‍🦳'} {name} 的面板")
    
    if not base_info:
        st.warning(f"等待 {name} 初始化...")
        return

    # (1) 身体指标 - 纵向排列
    with st.container():
        st.markdown('<div class="mobile-card">', unsafe_allow_html=True)
        st.markdown("### 📊 身体指标")
        
        h = safe_float(base_info.get('height', 165.0))
        w_val = safe_float(log.get('weight', base_info.get('weight', 60.0)))
        
        weight = st.number_input(f"体重 (kg) - {name}", value=w_val, key=f"w_{name}", disabled=not editable)
        chest = st.number_input(f"胸围 (cm) - {name}", value=safe_float(log.get('chest')), key=f"ch_{name}", disabled=not editable)
        arm = st.number_input(f"臂围 (cm) - {name}", value=safe_float(log.get('arm')), key=f"ar_{name}", disabled=not editable)
        waist = st.number_input(f"腰围 (cm) - {name}", value=safe_float(log.get('waist')), key=f"wa_{name}", disabled=not editable)
        hip = st.number_input(f"臀围 (cm) - {name}", value=safe_float(log.get('hip')), key=f"hi_{name}", disabled=not editable)
        thigh = st.number_input(f"大腿围 (cm) - {name}", value=safe_float(log.get('thigh')), key=f"th_{name}", disabled=not editable)
        calf = st.number_input(f"小腿围 (cm) - {name}", value=safe_float(log.get('calf')), key=f"ca_{name}", disabled=not editable)

        if st.button(f"保存身体数据 ({name})", key=f"btn_s_{name}", disabled=not editable):
            try:
                data = {
                    "user_name": name, "log_date": str(date.today()),
                    "weight": weight, "chest": chest, "arm": arm, "waist": waist,
                    "hip": hip, "thigh": thigh, "calf": calf
                }
                supabase.table("daily_logs").upsert(data, on_conflict="user_name,log_date").execute()
                st.success("数据已同步！")
                st.rerun()
            except Exception as e: st.error(f"失败: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

    # (2) 饮食打卡
    with st.container():
        st.markdown('<div class="mobile-card">', unsafe_allow_html=True)
        st.markdown("### 🍱 饮食打卡")
        consumed = safe_float(log.get('calorie_intake', 0))
        st.metric("今日已摄入", f"{int(consumed)} kcal")
        
        f_img = st.file_uploader(f"上传餐食图片 ({name})", type=['jpg','png'], key=f"img_{name}", disabled=not editable)
        if f_img:
            st.image(f_img, use_container_width=True)
            if st.button(f"🚀 AI 识别热量 ({name})", key=f"ai_{name}", disabled=not editable):
                add_cal = random.randint(350, 650)
                supabase.table("daily_logs").upsert({
                    "user_name": name, "log_date": str(date.today()), "calorie_intake": consumed + add_cal
                }, on_conflict="user_name,log_date").execute()
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # (3) 运动消耗
    with st.container():
        st.markdown('<div class="mobile-card">', unsafe_allow_html=True)
        st.markdown("### 🏃 运动消耗")
        ex_burn = safe_float(log.get('calorie_burn', 0))
        st.metric("今日已消耗", f"{int(ex_burn)} kcal")
        
        ex_dur = st.number_input(f"运动时长 (分钟) - {name}", value=int(safe_float(log.get('ex_duration'))), key=f"dur_{name}", disabled=not editable)
        if st.button(f"⚡ 计算运动消耗 ({name})", key=f"exb_{name}", disabled=not editable):
            burn_val = ex_dur * random.uniform(6.0, 9.0)
            supabase.table("daily_logs").upsert({
                "user_name": name, "log_date": str(date.today()), "calorie_burn": burn_val, "ex_duration": ex_dur
            }, on_conflict="user_name,log_date").execute()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # (4) 趋势查看
    with st.container():
        st.markdown('<div class="mobile-card">', unsafe_allow_html=True)
        st.markdown("### 📈 趋势分析")
        metric_opt = st.selectbox(f"选择指标 ({name})", ["weight", "waist", "thigh", "arm", "hip"], key=f"opt_{name}")
        if st.button(f"生成趋势图 ({name})", key=f"tr_{name}"):
            hist = supabase.table("daily_logs").select("*").eq("user_name", name).order("log_date").execute()
            df = pd.DataFrame(hist.data)
            if not df.empty:
                df['log_date'] = pd.to_datetime(df['log_date'])
                st.line_chart(df.set_index('log_date')[metric_opt])
        st.markdown('</div>', unsafe_allow_html=True)

    # (5) 健康心得
    with st.container():
        st.markdown('<div class="mobile-card">', unsafe_allow_html=True)
        st.markdown("### 💭 健康心得")
        note_val = st.text_area(f"今日感想 ({name})", value=str(log.get('note', '')), key=f"nt_{name}", disabled=not editable)
        if st.button(f"发布心得 ({name})", key=f"btn_n_{name}", disabled=not editable):
            supabase.table("daily_logs").upsert({
                "user_name": name, "log_date": str(date.today()), "note": note_val
            }, on_conflict="user_name,log_date").execute()
            st.success("心得已同步！")
        st.markdown('</div>', unsafe_allow_html=True)

# --- 7. 页面渲染 (纵向堆叠) ---
# 先显示自己的，再显示对方的
render_user_section(my_name, editable=True)
st.markdown("---")
render_user_section(other_name, editable=False)

# 侧边栏
with st.sidebar:
    st.image(icon_path, width=100) if os.path.exists(icon_path) else None
    if st.button("退出登录 / 切换身份"):
        st.session_state.clear()
        st.rerun()
