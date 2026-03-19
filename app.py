import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, date
import random
import os
import requests
from PIL import Image

# --- [0. 数据库修复 SQL 指令 - 请在 Supabase SQL Editor 执行] ---
# CREATE TABLE IF NOT EXISTS users (
#   id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
#   name TEXT UNIQUE,
#   birthday DATE,
#   age INT,
#   height INT,
#   weight FLOAT,
#   gender TEXT DEFAULT '女'
# );
# 
# CREATE TABLE IF NOT EXISTS daily_logs (
#   id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
#   user_name TEXT,
#   log_date DATE,
#   weight FLOAT DEFAULT 0,
#   chest FLOAT DEFAULT 0,
#   waist FLOAT DEFAULT 0,
#   arm FLOAT DEFAULT 0,
#   hip FLOAT DEFAULT 0,
#   thigh FLOAT DEFAULT 0,
#   calf FLOAT DEFAULT 0,
#   calorie_intake FLOAT DEFAULT 0,
#   calorie_burn FLOAT DEFAULT 0,
#   water FLOAT DEFAULT 0,
#   ex_type TEXT,
#   ex_duration INT DEFAULT 0,
#   note TEXT,
#   UNIQUE(user_name, log_date)
# );

# --- 1. 基础配置与图标加载 ---
try:
    icon_img = Image.open("app_icon.png")
    st.set_page_config(page_title="花大爷 × 不差儿", page_icon=icon_img, layout="wide")
except Exception:
    st.set_page_config(page_title="花大爷 × 不差儿", layout="wide")

# --- 2. 核心常量与 API 配置 ---
SUPABASE_URL = "https://hjrvdusefkjtmucsreeq.supabase.co"
SUPABASE_KEY = "sb_publishable_yDO1V8a3qYz8YPSzXSHdWA_mhpQG8QF"
DEEPSEEK_API_KEY = "sk-dffb3900356c4df6b2bc2d5994f3a828"
TIFFANY_BLUE = "#0ABAB5"
TEXT_COLOR = "#1A1A1A"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# --- 3. UI 样式注入 ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #F0F9F9; color: {TEXT_COLOR}; }}
    .stMarkdown, p, span, label, div {{ color: {TEXT_COLOR} !important; font-weight: 500; }}
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

# --- 4. 工具函数 ---
def calculate_age(birth_date):
    if not birth_date: return 0
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

def get_ai_analysis(image, mode="food"):
    try:
        # 实际部署对接 DeepSeek API 逻辑
        if mode == "food":
            return {"cal": random.randint(250, 600), "p": 25, "f": 12, "c": 45}
        return round(random.uniform(18.5, 26.5), 1)
    except Exception:
        if mode == "food": return {"cal": 350, "p": 20, "f": 10, "c": 40}
        return 22.0

def get_streak_days():
    try:
        res = supabase.table("daily_logs").select("log_date").order("log_date", desc=False).execute()
        if res.data:
            dates = {item['log_date'] for item in res.data}
            return len(dates)
    except: pass
    return 1

# --- 5. 身份登录逻辑 ---
if 'user_role' not in st.session_state:
    st.image("app_icon.png", width=120)
    st.markdown('<div class="card"><h3>👤 身份确认</h3>', unsafe_allow_html=True)
    role = st.radio("你是谁？", ["花大爷", "不差儿"], horizontal=True)
    if st.button("进入基地"):
        st.session_state.user_role = role
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

my_name = st.session_state.user_role
other_name = "不差儿" if my_name == "花大爷" else "花大爷"

# --- 6. 初始化判定 (基于数据库) ---
try:
    res_me = supabase.table("users").select("*").eq("name", my_name).execute()
    initialized = True if res_me.data and len(res_me.data) > 0 else False
except Exception as e:
    st.error(f"数据库连接失败: {e}")
    st.stop()

if not initialized:
    st.markdown(f'<div class="card"><h3>🐣 首次进入，请初始化 ({my_name})</h3>', unsafe_allow_html=True)
    with st.form("init_form"):
        birth = st.date_input("选择生日", value=date(2000, 1, 1))
        u_age = calculate_age(birth)
        st.write(f"👶 自动年龄计算: **{u_age}** 岁")
        u_height = st.number_input("身高 (cm)", value=165, step=1)
        u_weight = st.number_input("初始体重 (kg)", value=60.0)
        u_gender = st.radio("性别", ["女", "男"], index=0)
        if st.form_submit_button("🚀 完成初始化"):
            try:
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
    view_date = st.date_input("📅 选择日期", date.today())
    st.write(f"🌦️ 城市天气：晴间多云 22°C (Mock)")
with c_h2:
    st.write(f"打卡天数: 🔥 **{get_streak_days()}** 天")

# --- 8. 核心左右分栏 ---
col_left, col_right = st.columns(2)

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

        # 身体指标
        st.markdown('<div class="card"><b>📊 身体指标</b>', unsafe_allow_html=True)
        h = base_info['height']
        w = log.get('weight', base_info['weight'])
        st.write(f"📏 身高: **{h}** cm")
        
        if is_editable:
            new_w = st.number_input("体重 (kg)", value=float(w), key=f"w_{name}")
            bmi = round(new_w / ((h/100)**2), 1)
            st.write(f"⚖️ BMI: **{bmi}**")
            
            fat_img = st.file_uploader("📷 上传露腹照片分析体脂率", type=['jpg','png'], key=f"fimg_{name}")
            fat = log.get('body_fat', 0.0)
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
            chest = g1.number_input("胸围", value=float(log.get('chest', 0)), key=f"ch_{name}")
            waist = g2.number_input("腰围", value=float(log.get('waist', 0)), key=f"wa_{name}")
            arm = g1.number_input("臂围", value=float(log.get('arm', 0)), key=f"ar_{name}")
            hip = g2.number_input("臀围", value=float(log.get('hip', 0)), key=f"hi_{name}")
            thigh = g1.number_input("大腿", value=float(log.get('thigh', 0)), key=f"th_{name}")
            calf = g2.number_input("小腿", value=float(log.get('calf', 0)), key=f"ca_{name}")

            if st.button("💾 保存身体记录", key=f"sv_{name}"):
                try:
                    supabase.table("daily_logs").upsert({
                        "user_name": name, "log_date": str(view_date), "weight": new_w,
                        "chest": chest, "waist": waist, "arm": arm, "hip": hip, "thigh": thigh, "calf": calf
                    }, on_conflict="user_name,log_date").execute()
                    st.rerun()
                except Exception as e: st.error(f"保存报错: {e}")
        else:
            st.write(f"⚖️ 体重: **{w}** kg")
            st.write(f"⚖️ BMI: **{round(float(w)/((h/100)**2), 1)}**")
            st.write(f"🔥 体脂率: **{log.get('body_fat', 0)}%**")
            st.write(f"围度: 胸{log.get('chest', 0)} / 腰{log.get('waist', 0)} / 臂{log.get('arm', 0)}")
        st.markdown('</div>', unsafe_allow_html=True)

        # 饮食打卡
        st.markdown('<div class="card"><b>🍱 饮食记录</b>', unsafe_allow_html=True)
        bmr = 10 * float(w) + 6.25 * h - 5 * base_info['age'] - 161
        suggested = int(bmr * 1.2)
        consumed = log.get('calorie_intake', 0)
        st.write(f"🎯 建议摄入: **{suggested}** kcal (BMR: {int(bmr)})")
        st.write(f"🍎 已摄入: **{consumed}** kcal")
        
        if is_editable:
            water = st.number_input("💧 饮水 (ml)", value=float(log.get('water', 0)), key=f"wat_{name}")
            m_img = st.file_uploader("🍔 上传饮食图片 (AI 分析)", type=['jpg','png'], key=f"mimg_{name}")
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
        burn = log.get('calorie_burn', 0)
        if is_editable:
            st.file_uploader("运动自拍", type=['jpg','png'], key=f"eximg_{name}")
            ex_t = st.text_input("运动项目", value=log.get('ex_type', ''), key=f"ext_{name}")
            ex_d = st.number_input("时长 (min)", value=int(log.get('ex_duration', 0)), key=f"exd_{name}")
            if st.button("同步运动热量", key=f"exb_{name}"):
                burnt_val = ex_d * random.randint(5, 10)
                try:
                    supabase.table("daily_logs").upsert({
                        "user_name": name, "log_date": str(view_date),
                        "ex_type": ex_t, "ex_duration": ex_d, "calorie_burn": burnt_val
                    }, on_conflict="user_name,log_date").execute()
                    st.rerun()
                except: pass
        st.write(f"⚡ 运动消耗: **{burn}** kcal")
        st.write(f"🌟 今日总消耗 (BMR+运动): **{int(bmr + burn)}** kcal")
        st.markdown('</div>', unsafe_allow_html=True)

        # 健康心得
        st.markdown('<div class="card"><b>💭 健康心得</b>', unsafe_allow_html=True)
        if is_editable:
            note = st.text_area("今天的心情或感悟...", value=log.get('note', ''), key=f"nt_{name}")
            st.file_uploader("心得配图", type=['jpg','png'], key=f"ntimg_{name}")
            if st.button("发布心得", key=f"ntb_{name}"):
                try:
                    supabase.table("daily_logs").upsert({
                        "user_name": name, "log_date": str(view_date), "note": note
                    }, on_conflict="user_name,log_date").execute()
                    st.success("心得已同步")
                except: pass
        else:
            st.write(log.get('note', '对方还没有写心得~'))
        st.markdown('</div>', unsafe_allow_html=True)

# 渲染 (左不差儿，右花大爷)
render_column("不差儿", col_left, (my_name == "不差儿"), other_base)
render_column("花大爷", col_right, (my_name == "花大爷"), me_base)

if st.sidebar.button("登出 / 切换身份"):
    st.session_state.clear()
    st.rerun()
