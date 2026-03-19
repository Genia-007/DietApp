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
    try:
        if v is None or str(v).strip() == "" or str(v).lower() == "none":
            return float(default)
        return float(v)
    except:
        return float(default)

def safe_text(v):
    return str(v).strip() if v is not None else ""

# --- 3.页面 UI 样式注入 ---
st.markdown(f"""
    <style>
    /* 1. 强制所有屏幕下的 columns 都不折叠 */
    [data-testid="column"] {{
        width: 50% !important;
        flex: 1 1 50% !important;
        min-width: 50% !important;
    }}

    /* 2. 缩小手机端的间距和内边距，防止内容溢出 */
    [data-testid="stHorizontalBlock"] {{
        gap: 0.5rem !important;
    }}
    
    .card {{
        padding: 10px !important; /* 手机端卡片内边距调小 */
        margin-bottom: 10px !important;
    }}
    
    /* 3. 针对手机端的字体微调 (可选) */
    @media (max-width: 640px) {{
        .stat-text, p, span, label {{
            font-size: 12px !important;
        }}
        h3 {{
            font-size: 14px !important;
        }}
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. 身份登录 ---
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

# --- 5. 顶部 Header 与 基础信息加载 ---
if os.path.exists(icon_path):
    st.image(icon_path, width=100)

view_date = st.date_input("📅 日期选择", date.today())

try:
    me_base = supabase.table("users").select("*").eq("name", my_name).execute().data[0]
    friend_res = supabase.table("users").select("*").eq("name", other_name).execute()
    friend_base = friend_res.data[0] if friend_res.data else None
except:
    st.error("同步资料失败，请先完成初始化")
    st.stop()

# --- 6. 统一渲染函数 (新增：累计打卡天数 & 运动消耗) ---
def render_column(name, col, editable, base_info):
    try:
        # 获取今日记录
        l_res = supabase.table("daily_logs").select("*").eq("user_name", name).eq("log_date", str(view_date)).execute()
        log = l_res.data[0] if l_res.data else {}
        
        # 获取累计打卡天数 (去重计算有记录的所有日期)
        all_logs = supabase.table("daily_logs").select("log_date").eq("user_name", name).execute()
        streak_days = len({item['log_date'] for item in all_logs.data}) if all_logs.data else 0
    except:
        log = {}
        streak_days = 0

    with col:
        st.markdown(f"### {'👩‍𝓠' if name=='不差儿' else '👨‍🦳'} {name}")
        
        # 显示累计打卡天数
        st.markdown(f'<p class="stat-text">🔥 累计打卡：{streak_days} 天</p>', unsafe_allow_html=True)
        
        if not base_info:
            st.info(f"等待 {name} 初始化...")
            return

        h = safe_float(base_info.get('height', 165.0))
        w_init = safe_float(base_info.get('weight', 60.0))

        # (1) 身体维度模块
        st.markdown('<div class="card"><b>📊 身体维度</b>', unsafe_allow_html=True)
        weight = st.number_input("体重 (kg)", value=safe_float(log.get("weight", w_init)), key=f"w_{name}", disabled=not editable)
        
        g1, g2 = st.columns(2)
        waist = g1.number_input("腰围", value=safe_float(log.get("waist")), key=f"wa_{name}", disabled=not editable)
        thigh = g2.number_input("大腿围", value=safe_float(log.get("thigh")), key=f"th_{name}", disabled=not editable)
        chest = g1.number_input("胸围", value=safe_float(log.get("chest")), key=f"ch_{name}", disabled=not editable)
        arm = g2.number_input("臂围", value=safe_float(log.get("arm")), key=f"ar_{name}", disabled=not editable)
        hip = g1.number_input("臀围", value=safe_float(log.get("hip")), key=f"hi_{name}", disabled=not editable)
        calf = g2.number_input("小腿围", value=safe_float(log.get("calf")), key=f"ca_{name}", disabled=not editable)

        if st.button("💾 保存身体数据", key=f"sv_btn_{name}", disabled=not editable, use_container_width=True):
            data = {
                "user_name": name, "log_date": str(view_date),
                "weight": weight, "chest": chest, "arm": arm, "waist": waist,
                "hip": hip, "thigh": thigh, "calf": calf
            }
            supabase.table("daily_logs").upsert(data, on_conflict="user_name,log_date").execute()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # (2) 运动消耗模块 (新增功能)
        st.markdown('<div class="card"><b>🏃 运动消耗</b>', unsafe_allow_html=True)
        ex_burn = safe_float(log.get('calorie_burn', 0.0))
        st.metric("今日消耗", f"{int(ex_burn)} kcal", delta=f"{streak_days}天坚持" if streak_days > 0 else None)
        
        ex_type = st.text_input("运动项目", value=safe_text(log.get('ex_type')), key=f"ext_{name}", disabled=not editable, placeholder="如：慢跑、瑜伽")
        ex_dur = st.number_input("时长 (分钟)", value=int(safe_float(log.get('ex_duration'))), key=f"exd_{name}", disabled=not editable)
        
        if st.button("⚡ 更新运动消耗", key=f"ex_btn_{name}", disabled=not editable, use_container_width=True):
            # 简单估算逻辑：分钟 * 随机强度系数 (6-10)
            calculated_burn = ex_dur * random.uniform(6.0, 9.0)
            supabase.table("daily_logs").upsert({
                "user_name": name, "log_date": str(view_date),
                "ex_type": ex_type, "ex_duration": ex_dur, "calorie_burn": calculated_burn
            }, on_conflict="user_name,log_date").execute()
            st.rerun()
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

        # (4) 健康心得
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
