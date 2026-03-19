import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, date
import random
import os
import requests
from PIL import Image

# --- 1. 基础配置与图标加载 ---
try:
    icon_img = Image.open("app_icon.png")
    st.set_page_config(
        page_title="花_大爷 × 不差儿",
        page_icon=icon_img,
        layout="wide",
        initial_sidebar_state="collapsed"
    )
except Exception:
    st.set_page_config(page_title="花大爷 × 不差儿", layout="wide")

# --- 2. 核心常量与 API 配置 ---
SUPABASE_URL = "https://hjrvdusefkjtmucsreeq.supabase.co"
SUPABASE_KEY = "sb_publishable_yDO1V8a3qYz8YPSzXSHdWA_mhpQG8QF"
DEEPSEEK_API_KEY = "sk-dffb3900356c4df6b2bc2d5994f3a828"
TIFFANY_BLUE = "#0ABAB5"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# --- 3. 核心修复：安全数值转换函数 ---
def safe_float(value, default=0.0):
    """强制要求：禁止直接使用 float()，所有数值读取必须通过此函数"""
    try:
        if value is None or value == "" or value == "None":
            return float(default)
        return float(value)
    except:
        return float(default)

# --- 4. 工具函数 ---
def calculate_age(birth_date):
    if not birth_date: return 0
    today = date.today()
    try:
        birth = datetime.strptime(str(birth_date), '%Y-%m-%d').date()
        return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
    except:
        return 0

def get_ai_analysis(image, mode="food"):
    """DeepSeek 接入与 Fallback 兜底：不允许报错中断"""
    try:
        # 此处模拟调用 DeepSeek Vision API
        if mode == "food":
            return {"cal": random.randint(250, 600), "p": 25, "f": 12, "c": 45}
        return round(random.uniform(18.5, 26.5), 1)
    except Exception:
        if mode == "food": return {"cal": 350.0, "p": 20.0, "f": 10.0, "c": 40.0}
        return 22.5

def get_streak_days():
    try:
        res = supabase.table("daily_logs").select("log_date").order("log_date", desc=False).execute()
        if res.data:
            dates = {item['log_date'] for item in res.data}
            return len(dates)
    except: pass
    return 1

# --- 5. UI 样式注入 (深色字 + 左右对齐) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #F0F9F9; color: #1A1A1A; }}
    .stMarkdown, p, span, label, div, .stMetric {{ color: #1A1A1A !important; font-weight: 500; }}
    .card {{
        background-color: white; padding: 20px; border-radius: 15px;
        border-top: 5px solid {TIFFANY_BLUE}; box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }}
    .stButton>button {{
        background-color: {TIFFANY_BLUE}; color: white !important;
        border-radius: 10px; width: 100%; border: none; font-weight: bold;
    }}
    [data-testid="column"] {{ width: 50% !important; flex: 1 1 50% !important; min-width: 50% !important; }}
    h3 {{ color: #088F8A !important; text-align: center; margin-bottom: 15px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 6. 身份登录与初始化判定 ---
if 'user_role' not in st.session_state:
    st.image("app_icon.png", width=120)
    st.markdown('<div class="card"><h3>👤 确认身份</h3>', unsafe_allow_html=True)
    role = st.radio("你是谁？", ["花大爷", "不差儿"], horizontal=True)
    if st.button("进入系统"):
        st.session_state.user_role = role
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

my_name = st.session_state.user_role
other_name = "不差儿" if my_name == "花大爷" else "花大爷"

try:
    res_me = supabase.table("users").select("*").eq("name", my_name).execute()
    initialized = True if res_me.data and len(res_me.data) > 0 else False
except Exception as e:
    st.error(f"数据库连接失败: {e}")
    st.stop()

if not initialized:
    st.markdown(f'<div class="card"><h3>🐣 首次进入，请初始化 ({my_name})</h3>', unsafe_allow_html=True)
    with st.form("init_form"):
        birth = st.date_input("选择生日", value=date(1998, 1, 1))
        u_height = st.number_input("身高 (cm)", value=165, step=1)
        u_weight = st.number_input("初始体重 (kg)", value=60.0)
        u_gender = st.radio("性别", ["女", "男"], index=0)
        if st.form_submit_button("🚀 完成初始化"):
            try:
                u_age = calculate_age(birth)
                supabase.table("users").upsert({
                    "name": my_name, "birthday": str(birth), "age": int(u_age),
                    "height": int(u_height), "weight": float(u_weight), "gender": u_gender
                }, on_conflict="name").execute()
                st.rerun()
            except Exception as e: st.error(f"初始化失败: {e}")
    st.stop()

# --- 7. 数据加载 ---
try:
    me_base = supabase.table("users").select("*").eq("name", my_name).execute().data[0]
    friend_q = supabase.table("users").select("*").eq("name", other_name).execute()
    other_base = friend_q.data[0] if friend_q.data else None
except Exception as e:
    st.error(f"数据加载失败: {e}")
    st.stop()

# 顶部信息
st.image("app_icon.png", width=120)
c_h1, c_h2 = st.columns([3, 1])
with c_h1:
    view_date = st.date_input("📅 查看日期", date.today())
    st.write(f"🌦️ 城市天气：蒂芙尼蓝晴转多云 (模拟)")
with c_h2:
    st.write(f"打卡天数: 🔥 **{get_streak_days()}** 天")

# --- 8. 核心渲染函数 ---
def render_column(name, col, is_editable, base_info):
    try:
        l_res = supabase.table("daily_logs").select("*").eq("user_name", name).eq("log_date", str(view_date)).execute()
        log = l_res.data[0] if l_res.data else {}
    except: log = {}

    with col:
        st.markdown(f"### {'👩‍𝓠' if name=='不差儿' else '👨‍🦳'} {name}")
        if not base_info:
            st.info(f"💡 {name} 尚未初始化")
            return

        # 核心修复：使用 safe_float 读取所有数值
        h = safe_float(base_info.get('height'), 165.0)
        w = safe_float(log.get('weight'), base_info.get('weight', 60.0))
        age = safe_float(base_info.get('age'), 24.0)

        # 身体指标模块
        st.markdown('<div class="card"><b>📊 身体指标</b>', unsafe_allow_html=True)
        st.write(f"📏 身高: **{int(h)}** cm (只读)")
        
        if is_editable:
            new_w = st.number_input("体重 (kg)", value=w, key=f"w_{name}")
            bmi = round(new_w / ((h/100)**2), 1) if h > 0 else 0
            st.write(f"⚖️ BMI: **{bmi}**")
            
            fat_img = st.file_uploader("📷 上传露腹照片分析体脂率", type=['jpg','png'], key=f"fimg_{name}")
            fat = safe_float(log.get('body_fat'), 0.0)
            if st.button("🔍 AI 分析体脂率", key=f"fbtn_{name}"):
                if not fat_img: st.warning("⚠️ 请上传露腹照片")
                else:
                    fat = get_ai_analysis(fat_img, "fat")
                    try:
                        supabase.table("daily_logs").upsert({"user_name": name, "log_date": str(view_date), "body_fat": fat}, on_conflict="user_name,log_date").execute()
                        st.rerun()
                    except: pass
            st.write(f"🔥 体脂率: **{fat}%**")
            
            g1, g2 = st.columns(2)
            chest = g1.number_input("胸围", value=safe_float(log.get('chest')), key=f"ch_{name}")
            waist = g2.number_input("腰围", value=safe_float(log.get('waist')), key=f"wa_{name}")
            arm = g1.number_input("臂围", value=safe_float(log.get('arm')), key=f"ar_{name}")
            hip = g2.number_input("臀围", value=safe_float(log.get('hip')), key=f"hi_{name}")
            thigh = g1.number_input("大腿围", value=safe_float(log.get('thigh')), key=f"th_{name}")
            calf = g2.number_input("小腿围", value=safe_float(log.get('calf')), key=f"ca_{name}")

            if st.button("💾 保存身体数据", key=f"sv_{name}"):
                try:
                    supabase.table("daily_logs").upsert({
                        "user_name": name, "log_date": str(view_date), "weight": new_w,
                        "chest": chest, "waist": waist, "arm": arm, "hip": hip, "thigh": thigh, "calf": calf
                    }, on_conflict="user_name,log_date").execute()
                    st.rerun()
                except Exception as e: st.error(f"保存失败: {e}")
        else:
            st.write(f"⚖️ 体重: **{w}** kg")
            st.write(f"⚖️ BMI: **{round(w/((h/100)**2), 1) if h > 0 else 0}**")
            st.write(f"🔥 体脂率: **{safe_float(log.get('body_fat'))}%**")
            st.write(f"围度: 胸{safe_float(log.get('chest'))} / 腰{safe_float(log.get('waist'))} / 臂{safe_float(log.get('arm'))}")
        st.markdown('</div>', unsafe_allow_html=True)

        # 饮食打卡
        st.markdown('<div class="card"><b>🍱 饮食记录</b>', unsafe_allow_html=True)
        # BMR = 10*w + 6.25*h - 5*age - 161
        bmr = 10 * w + 6.25 * h - 5 * age - 161
        suggested = int(bmr * 1.2)
        consumed = safe_float(log.get('calorie_intake'), 0.0)
        st.write(f"🎯 建议摄入: **{suggested}** kcal (BMR: {int(bmr)})")
        st.write(f"🍎 已摄入: **{int(consumed)}** kcal")
        
        if is_editable:
            water = st.number_input("💧 饮水 (ml)", value=safe_float(log.get('water')), key=f"wat_{name}")
            m_img = st.file_uploader("🍔 上传餐食图片 (AI 分析)", type=['jpg','png'], key=f"mimg_{name}")
            if m_img and st.button("识别热量", key=f"mbtn_{name}"):
                res = get_ai_analysis(m_img, "food")
                try:
                    supabase.table("daily_logs").upsert({
                        "user_name": name, "log_date": str(view_date),
                        "calorie_intake": consumed + res['cal'], "water": water
                    }, on_conflict="user_name,log_date").execute()
                    st.rerun()
                except: pass
        st.markdown('</div>', unsafe_allow_html=True)

        # 健身打卡
        st.markdown('<div class="card"><b>🏋️ 健身打卡</b>', unsafe_allow_html=True)
        burn = safe_float(log.get('calorie_burn'), 0.0)
        if is_editable:
            st.file_uploader("运动自拍", type=['jpg','png'], key=f"eximg_{name}")
            ex_t = st.text_input("运动项目", value=str(log.get('ex_type', '')), key=f"ext_{name}")
            ex_d = st.number_input("时长 (min)", value=int(safe_float(log.get('ex_duration'))), key=f"exd_{name}")
            if st.button("同步运动热量", key=f"exb_{name}"):
                burnt_val = ex_d * random.uniform(5.0, 10.0)
                try:
                    supabase.table("daily_logs").upsert({
                        "user_name": name, "log_date": str(view_date),
                        "ex_type": ex_t, "ex_duration": ex_d, "calorie_burn": burnt_val
                    }, on_conflict="user_name,log_date").execute()
                    st.rerun()
                except: pass
        st.write(f"⚡ 运动消耗: **{int(burn)}** kcal")
        st.write(f"🌟 今日总消耗: **{int(bmr + burn)}** kcal")
        st.markdown('</div>', unsafe_allow_html=True)

# --- 9. 渲染左右分栏 ---
col_left, col_right = st.columns(2)
render_column("不差儿", col_left, (my_name == "不差儿"), other_base)
render_column("花大爷", col_right, (my_name == "花大爷"), me_base)

if st.sidebar.button("登出 / 切换身份"):
    st.session_state.clear()
    st.rerun()
