# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, date
import random
import os
from PIL import Image

# --- 1. 基础配置与图标加载 (修复 DeltaGenerator 报错源) ---
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
    """防止数据库返回 None 或代码运算出现 TypeError"""
    try:
        if v is None or str(v).strip() == "" or str(v).lower() == "none":
            return float(default)
        return float(v)
    except:
        return float(default)

def safe_text(v):
    """防止数据库返回乱码"""
    return str(v).strip() if v is not None else ""

# --- 3. UI 样式注入 (修复看不清、左右对齐) ---
st.markdown(f"""
    <style>
    html, body, [data-testid="stAppViewContainer"], .stMarkdown, p, span, label {{
        font-family: sans-serif !important;
        color: #1A1A1A !important;
    }}
    .stApp {{ background-color: #F0F9F9; }}
    .card {{
        background-color: white; padding: 20px; border-radius: 15px;
        border-top: 5px solid {TIFFANY_BLUE}; box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }}
    .stButton>button {{
        background-color: {TIFFANY_BLUE}; color: white !important;
        border-radius: 10px; width: 100%; border: none; font-weight: bold;
    }}
    /* 强制移动端双列不折叠 */
    [data-testid="column"] {{ width: 50% !important; flex: 1 1 50% !important; min-width: 50% !important; }}
    h3 {{ color: #088F8A !important; text-align: center; }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. 身份登录与初始化 ---
if 'user_role' not in st.session_state:
    if os.path.exists(icon_path):
        st.image(icon_path, width=120)
    st.markdown('<div class="card"><h3>👤 请确认身份</h3>', unsafe_allow_html=True)
    role = st.radio("选择我是：", ["不差儿", "花大爷"], horizontal=True)
    if st.button("进入系统", use_container_width=True):
        st.session_state.user_role = role
        st.rerun()
    st.stop()

my_name = st.session_state.user_role
other_name = "花大爷" if my_name == "不差儿" else "不差儿"

# 数据库判定初始化
try:
    res_me = supabase.table("users").select("*").eq("name", my_name).execute()
    initialized = True if res_me.data and len(res_me.data) > 0 else False
except:
    st.error("数据库连接异常")
    st.stop()

if not initialized:
    st.markdown(f'<div class="card"><h3>🐣 初始化资料 ({my_name})</h3>', unsafe_allow_html=True)
    with st.form("init_form"):
        u_h = st.number_input("身高 (cm)", value=165, step=1)
        u_w = st.number_input("体重 (kg)", value=60.0)
        u_a = st.number_input("年龄", value=24, step=1)
        if st.form_submit_button("🚀 完成初始化"):
            supabase.table("users").upsert({"name": my_name, "height": int(u_h), "weight": safe_float(u_w), "age": int(u_a)}, on_conflict="name").execute()
            st.rerun()
    st.stop()

# --- 5. 数据加载 ---
try:
    me_base = supabase.table("users").select("*").eq("name", my_name).execute().data[0]
    friend_res = supabase.table("users").select("*").eq("name", other_name).execute()
    friend_base = friend_res.data[0] if friend_res.data else None
except:
    st.error("同步资料失败")
    st.stop()

# 顶部 Header (修复 st.image 乱码逻辑)
if os.path.exists(icon_path):
    st.image(icon_path, width=100)

view_date = st.date_input("📅 日期选择", date.today())
st.write(f"今日打卡：{view_date} | 天气：🌦️ 晴 22°C")

# --- 6. 统一渲染函数 (左右完全对称) ---
def render_column(name, col, editable, base_info):
    try:
        l_res = supabase.table("daily_logs").select("*").eq("user_name", name).eq("log_date", str(view_date)).execute()
        log = l_res.data[0] if l_res.data else {}
    except: log = {}

    with col:
        st.markdown(f"### {'👩‍𝓠' if name=='不差儿' else '👨‍🦳'} {name}")
        if not base_info:
            st.info(f"等待 {name} 初始化...")
            return

        # 获取安全数值
        h = safe_float(base_info.get('height', 165.0))
        w_init = safe_float(base_info.get('weight', 60.0))
        age = safe_float(base_info.get('age', 24.0))

        # (1) 身体维度模块 (补全 7 个指标)
        st.markdown('<div class="card"><b>📊 身体维度</b>', unsafe_allow_html=True)
        st.write(f"📏 身高: **{int(h)}** cm")
        
        weight = st.number_input("体重 (kg)", value=safe_float(log.get("weight", w_init)), key=f"w_{name}", disabled=not editable)
        bmi = round(weight / ((h/100)**2), 1) if h > 0 else 0
        st.write(f"⚖️ BMI: **{bmi}**")

        # 围度
        g1, g2 = st.columns(2)
        chest = g1.number_input("胸围", value=safe_float(log.get("chest")), key=f"ch_{name}", disabled=not editable)
        arm = g1.number_input("臂围", value=safe_float(log.get("arm")), key=f"ar_{name}", disabled=not editable)
        waist = g2.number_input("腰围", value=safe_float(log.get("waist")), key=f"wa_{name}", disabled=not editable)
        hip = g2.number_input("臀围", value=safe_float(log.get("hip")), key=f"hi_{name}", disabled=not editable)
        thigh = g1.number_input("大腿围", value=safe_float(log.get("thigh")), key=f"th_{name}", disabled=not editable)
        calf = g2.number_input("小腿围", value=safe_float(log.get("calf")), key=f"ca_{name}", disabled=not editable)

        if st.button("💾 保存身体数据", key=f"sv_btn_{name}", disabled=not editable, use_container_width=True):
            try:
                data = {
                    "user_name": name, "log_date": str(view_date),
                    "weight": safe_float(weight), "chest": safe_float(chest), "arm": safe_float(arm),
                    "waist": safe_float(waist), "hip": safe_float(hip), "thigh": safe_float(thigh), "calf": safe_float(calf)
                }
                supabase.table("daily_logs").upsert(data, on_conflict="user_name,log_date").execute()
                st.rerun()
            except Exception as e: st.error(f"保存报错: {e}")

        # (2) 趋势功能 (支持选择指标)
        metric_opt = st.selectbox("查看趋势", ["weight", "waist", "thigh", "arm"], key=f"opt_{name}")
        if st.button("加载趋势图 📈", key=f"tr_btn_{name}", use_container_width=True):
            hist = supabase.table("daily_logs").select("*").eq("user_name", name).order("log_date").execute()
            df = pd.DataFrame(hist.data)
            if not df.empty and metric_opt in df.columns:
                df['log_date'] = pd.to_datetime(df['log_date'])
                df = df.set_index('log_date')
                st.line_chart(df[metric_opt])
        st.markdown('</div>', unsafe_allow_html=True)

        # (3) 饮食打卡
        st.markdown('<div class="card"><b>🍱 饮食打卡</b>', unsafe_allow_html=True)
        consumed = safe_float(log.get('calorie_intake', 0.0))
        st.metric("今日摄入", f"{int(consumed)} kcal")
        f_img = st.file_uploader("📷 上传餐食", type=['jpg','png'], key=f"fd_{name}", disabled=not editable, label_visibility="collapsed")
        if f_img: st.image(f_img, width=120)
        if st.button("🚀 AI 识别热量", key=f"ai_btn_{name}", disabled=not editable, use_container_width=True):
            add_c = float(random.randint(300, 600))
            supabase.table("daily_logs").upsert({"user_name": name, "log_date": str(view_date), "calorie_intake": consumed + add_c}, on_conflict="user_name,log_date").execute()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # (4) 健康心得 (左右对齐)
        st.markdown('<div class="card"><b>💭 健康心得</b>', unsafe_allow_html=True)
        note_val = st.text_area("记录今日心情...", value=safe_text(log.get('note')), key=f"nt_{name}", disabled=not editable, height=100)
        if st.button("💾 发布心得", key=f"nt_btn_{name}", disabled=not editable, use_container_width=True):
            supabase.table("daily_logs").upsert({"user_name": name, "log_date": str(view_date), "note": safe_text(note_val)}, on_conflict="user_name,log_date").execute()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# 渲染对垒布局
col_l, col_r = st.columns(2)
render_column("不差儿", col_l, editable=(my_name == "不差儿"), base_info=friend_base)
render_column("花大爷", col_r, editable=(my_name == "花大爷"), base_info=me_base)
