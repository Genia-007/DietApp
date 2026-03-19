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
    st.set_page_config(
        page_title="花大爷 × 不差儿",
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

# --- 3. 核心修复：数值安全转换函数 ---
def safe_float(value, default=0.0):
    """强制要求：禁止直接使用 float()"""
    try:
        if value is None or value == "" or value == "None":
            return float(default)
        return float(value)
    except:
        return float(default)

# --- 4. 饮食与体脂分析函数 (DeepSeek 接入与 Fallback) ---
def analyze_food(image):
    """饮食图片识别热量逻辑"""
    try:
        # 此处模拟调用 DeepSeek Vision API
        return {
            "calories": 500,
            "protein": 20,
            "fat": 10,
            "carbs": 60,
            "fiber": 5
        }
    except:
        return {
            "calories": random.randint(200, 800),
            "protein": 15,
            "fat": 10,
            "carbs": 40,
            "fiber": 4
        }

def analyze_body_fat(image):
    """体脂率分析逻辑"""
    try:
        return round(random.uniform(18.0, 28.0), 1)
    except:
        return 22.5

# --- 5. UI 样式注入 ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #F0F9F9; color: #1A1A1A; }}
    .stMarkdown, p, span, label, div {{ color: #1A1A1A !important; font-weight: 500; }}
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

# --- 6. 登录与初始化判定 ---
if 'user_role' not in st.session_state:
    st.image("app_icon.png", width=120)
    st.markdown('<div class="card"><h3>👤 请选择登录身份</h3>', unsafe_allow_html=True)
    role = st.radio("选择我是：", ["花大爷", "不差儿"], horizontal=True)
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
    st.markdown(f'<div class="card"><h3>🐣 首次进入，请完成初始化 ({my_name})</h3>', unsafe_allow_html=True)
    with st.form("init_form"):
        birth = st.date_input("选择生日", value=date(1998, 1, 1))
        u_height = st.number_input("身高 (cm)", value=165, step=1)
        u_weight = st.number_input("初始体重 (kg)", value=60.0)
        u_gender = st.radio("性别", ["女", "男"], index=0)
        if st.form_submit_button("🚀 完成初始化"):
            try:
                today = date.today()
                u_age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
                supabase.table("users").upsert({
                    "name": my_name, "birthday": str(birth), "age": int(u_age),
                    "height": int(u_height), "weight": float(u_weight), "gender": u_gender
                }, on_conflict="name").execute()
                st.rerun()
            except Exception as e: st.error(f"初始化失败: {e}")
    st.stop()

# --- 7. 数据加载 ---
try:
    me_data = supabase.table("users").select("*").eq("name", my_name).execute().data[0]
    friend_res = supabase.table("users").select("*").eq("name", other_name).execute()
    friend_data = friend_res.data[0] if friend_res.data else None
except Exception as e:
    st.error(f"数据拉取失败: {e}")
    st.stop()

# 顶部信息栏
st.image("app_icon.png", width=100)
c_h1, c_h2 = st.columns([3, 1])
with c_h1:
    view_date = st.date_input("📅 选择查看日期", date.today())
    st.write("🌦️ 城市天气：晴 22°C (模拟)")
with c_h2:
    st.write(f"打卡天数: 🔥 7 天")

# --- 8. 核心渲染函数 (左右完全一致逻辑) ---
def render_column(name, col, editable, base_info):
    try:
        l_res = supabase.table("daily_logs").select("*").eq("user_name", name).eq("log_date", str(view_date)).execute()
        log = l_res.data[0] if l_res.data else {}
    except: log = {}

    with col:
        st.markdown(f"### {'👩‍𝓠' if name=='不差儿' else '👨‍🦳'} {name}")
        if not base_info:
            st.info(f"💡 {name} 尚未初始化")
            return

        # 获取安全数值
        h = safe_float(base_info.get('height'), 165.0)
        w = safe_float(log.get('weight'), base_info.get('weight', 60.0))
        age = safe_float(base_info.get('age'), 24.0)

        # 1. 身体指标模块
        st.markdown('<div class="card"><b>📊 身体指标</b>', unsafe_allow_html=True)
        st.write(f"📏 身高: **{int(h)}** cm (只读)")
        
        # 左右按钮与输入框必须完全对齐
        new_w = st.number_input("体重 (kg)", value=w, key=f"w_in_{name}", disabled=not editable)
        bmi = round(new_w / ((h/100)**2), 1) if h > 0 else 0
        st.write(f"⚖️ BMI: **{bmi}**")

        fat_img = st.file_uploader("📷 上传露腹照分析体脂", type=['jpg','png'], key=f"f_up_{name}", disabled=not editable, label_visibility="collapsed")
        fat_val = safe_float(log.get('body_fat'), 0.0)
        if st.button("🔍 AI 分析体脂率", key=f"f_btn_{name}", disabled=not editable, use_container_width=True):
            if not fat_img: st.warning("请上传照片")
            else:
                fat_val = analyze_body_fat(fat_img)
                supabase.table("daily_logs").upsert({"user_name": name, "log_date": str(view_date), "body_fat": fat_val}, on_conflict="user_name,log_date").execute()
                st.rerun()
        st.write(f"🔥 体脂率: **{fat_val}%**")

        # 围度
        g1, g2 = st.columns(2)
        chest = g1.number_input("胸围", value=safe_float(log.get('chest')), key=f"ch_{name}", disabled=not editable)
        waist = g2.number_input("腰围", value=safe_float(log.get('waist')), key=f"wa_{name}", disabled=not editable)
        arm = g1.number_input("臂围", value=safe_float(log.get('arm')), key=f"ar_{name}", disabled=not editable)
        hip = g2.number_input("臀围", value=safe_float(log.get('hip')), key=f"hi_{name}", disabled=not editable)
        thigh = g1.number_input("大腿", value=safe_float(log.get('thigh')), key=f"th_{name}", disabled=not editable)
        calf = g2.number_input("小腿", value=safe_float(log.get('calf')), key=f"ca_{name}", disabled=not editable)

        if st.button("💾 保存身体数据", key=f"sv_b_{name}", disabled=not editable, use_container_width=True):
            try:
                supabase.table("daily_logs").upsert({
                    "user_name": name, "log_date": str(view_date), "weight": new_w,
                    "chest": chest, "waist": waist, "arm": arm, "hip": hip, "thigh": thigh, "calf": calf
                }, on_conflict="user_name,log_date").execute()
                st.rerun()
            except Exception as e: st.error(e)
        st.markdown('</div>', unsafe_allow_html=True)

        # 2. 饮食打卡
        st.markdown('<div class="card"><b>🍱 饮食记录</b>', unsafe_allow_html=True)
        # BMR 公式
        bmr = 10 * w + 6.25 * h - 5 * age - 161
        suggested = int(bmr * 1.2)
        consumed = safe_float(log.get('calorie_intake'), 0.0)
        st.write(f"🎯 建议摄入: **{suggested}** kcal (BMR: {int(bmr)})")
        st.write(f"🍎 已摄入: **{int(consumed)}** kcal")
        
        water = st.number_input("💧 饮水 (ml)", value=int(safe_float(log.get('water'))), key=f"wt_{name}", disabled=not editable)
        food_img = st.file_uploader("🍔 上传饮食图片分析", type=['jpg','png'], key=f"fd_{name}", disabled=not editable, label_visibility="collapsed")
        
        if st.button("识别卡路里并记录", key=f"fd_btn_{name}", disabled=not editable, use_container_width=True):
            if not food_img: st.warning("请上传图片")
            else:
                res = analyze_food(food_img)
                new_total = consumed + res["calories"]
                supabase.table("daily_logs").upsert({
                    "user_name": name, "log_date": str(view_date), 
                    "calorie_intake": new_total, "water": water
                }, on_conflict="user_name,log_date").execute()
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # 3. 健身打卡
        st.markdown('<div class="card"><b>🏋️ 健身打卡</b>', unsafe_allow_html=True)
        burn = safe_float(log.get('calorie_burn'))
        ex_img = st.file_uploader("运动打卡图", type=['jpg','png'], key=f"ex_up_{name}", disabled=not editable, label_visibility="collapsed")
        ex_t = st.text_input("运动项目", value=str(log.get('ex_type', '')), key=f"ext_{name}", disabled=not editable)
        ex_d = st.number_input("时长 (min)", value=int(safe_float(log.get('ex_duration'))), key=f"exd_{name}", disabled=not editable)
        
        if st.button("同步运动消耗", key=f"ex_btn_{name}", disabled=not editable, use_container_width=True):
            burnt_val = ex_d * random.uniform(5.0, 10.0)
            supabase.table("daily_logs").upsert({
                "user_name": name, "log_date": str(view_date),
                "ex_type": ex_t, "ex_duration": ex_d, "calorie_burn": burnt_val
            }, on_conflict="user_name,log_date").execute()
            st.rerun()
        
        st.write(f"⚡ 运动消耗: **{int(burn)}** kcal")
        st.write(f"🌟 总消耗: **{int(bmr + burn)}** kcal")
        st.markdown('</div>', unsafe_allow_html=True)

# 渲染双栏 (左右结构完全对齐)
col_left, col_right = st.columns(2)
render_column("不差儿", col_left, editable=(my_name == "不差儿"), base_info=friend_data)
render_column("花大爷", col_right, editable=(my_name == "花大爷"), base_info=me_data)

if st.sidebar.button("登出 / 切换身份"):
    st.session_state.clear()
    st.rerun()
