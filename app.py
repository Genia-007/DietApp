import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, date
import random
import os
from PIL import Image

# --- 1. 页面配置与图标 ---
try:
    icon_img = Image.open("app_icon.png")
    st.set_page_config(page_title="花大爷 × 不差儿", page_icon=icon_img, layout="wide")
except:
    st.set_page_config(page_title="花大爷 × 不差儿", layout="wide")

# --- 2. 数据库配置 ---
SUPABASE_URL = "https://hjrvdusefkjtmucsreeq.supabase.co"
SUPABASE_KEY = "sb_publishable_yDO1V8a3qYz8YPSzXSHdWA_mhpQG8QF"
TIFFANY_BLUE = "#0ABAB5"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# --- 3. 核心工具函数 ---
def calculate_age(birth_date):
    if not birth_date: return 0
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

def get_streak_days():
    """从最早的一笔打卡记录开始计算天数"""
    try:
        res = supabase.table("daily_logs").select("log_date").order("log_date", desc=False).limit(1).execute()
        if res.data:
            start_date = datetime.strptime(res.data[0]['log_date'], '%Y-%m-%d').date()
            return (date.today() - start_date).days + 1
    except: pass
    return 1

# CSS 注入 (蒂芙尼蓝)
st.markdown(f"""
    <style>
    .stApp {{ background-color: #F0F9F9; }}
    .card {{ background: white; padding: 20px; border-radius: 15px; border-top: 5px solid {TIFFANY_BLUE}; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; }}
    .stButton>button {{ background: {TIFFANY_BLUE}; color: white; border-radius: 10px; width: 100%; border: none; font-weight: bold; }}
    [data-testid="column"] {{ width: 50% !important; flex: 1 1 50% !important; min-width: 50% !important; }}
    h3 {{ color: #088F8A; text-align: center; }}
    .debug-box {{ background: #eee; padding: 10px; font-size: 0.8rem; border-radius: 5px; margin-bottom: 10px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. 身份选择与数据库校验 (核心修复逻辑) ---
if 'user_role' not in st.session_state:
    st.image("app_icon.png", width=120)
    st.title("👤 请选择你的身份")
    role = st.radio("你是谁？", ["花大爷", "不差儿"], horizontal=True)
    if st.button("确认身份并进入"):
        st.session_state.user_role = role
        st.rerun()
    st.stop()

# 当前用户
my_name = st.session_state.user_role
other_name = "不差儿" if my_name == "花大爷" else "花大爷"

# --- 5. 实时数据库判定：用户是否已初始化 ---
try:
    # 分别查询两个用户
    res_me = supabase.table("users").select("*").eq("name", my_name).execute()
    res_other = supabase.table("users").select("*").eq("name", other_name).execute()
    
    # 调试信息展示
    with st.expander("🔍 数据库调试信息 (排查重复初始化用)"):
        st.write(f"当前身份: {my_name}")
        st.write(f"我的数据返回: ", res_me.data)
        st.write(f"好友数据返回: ", res_other.data)

    # 判定逻辑：以数据库数据为准
    me_exists = True if res_me.data and len(res_me.data) > 0 else False
    other_exists = True if res_other.data and len(res_other.data) > 0 else False

except Exception as e:
    st.error(f"数据库连接异常: {e}")
    st.stop()

# --- 6. 分支逻辑：初始化页面 vs 主页面 ---
if not me_exists:
    # 执行初始化页面
    st.markdown(f'<div class="card"><h3>🐣 欢迎，{my_name}！请完成首次初始化</h3>', unsafe_allow_html=True)
    with st.form("init_form"):
        birth = st.date_input("你的生日", value=date(2000, 1, 1))
        age = calculate_age(birth)
        st.info(f"自动计算年龄: {age} 岁")
        height = st.number_input("身高 (cm)", value=165, step=1)
        weight = st.number_input("初始体重 (kg)", value=60.0)
        gender = st.radio("性别", ["女", "男"])
        
        if st.form_submit_button("🚀 完成初始化并进入"):
            try:
                supabase.table("users").insert({
                    "name": my_name,
                    "birthday": str(birth),
                    "age": int(age),
                    "height": int(height),
                    "weight": float(weight),
                    "gender": gender
                }).execute()
                st.success("🎉 初始化完成！正在进入基地...")
                # 关键：初始化后立即刷新页面，重新走“判定已存在”的逻辑
                st.rerun()
            except Exception as e:
                st.error(f"保存失败: {e}")
    st.stop()

# --- 7. 主页面逻辑 (只有 me_exists 为 True 才会执行到这里) ---
# 顶部信息栏
col_t1, col_t2 = st.columns([3, 1])
with col_t1:
    st.image("app_icon.png", width=100)
    view_date = st.date_input("📅 选择日期", date.today())
with col_t2:
    st.write(f"打卡天数: 🔥 {get_streak_days()}天")

# 左右分栏同时显示 (修复显示Bug)
col_left, col_right = st.columns(2)

def render_column(name, col, is_editable, user_data):
    # 查询打卡数据
    try:
        l_res = supabase.table("daily_logs").select("*").eq("user_name", name).eq("log_date", str(view_date)).execute()
        log = l_res.data[0] if l_res.data else {}
    except: log = {}

    with col:
        st.markdown(f"### {'👨‍🦳' if name=='花大爷' else '👩‍𝓠'} {name}")
        
        if not user_data:
            st.info(f"💡 {name} 尚未初始化")
            return

        # 1. 身体指标卡
        st.markdown('<div class="card"><b>📊 身体指标</b>', unsafe_allow_html=True)
        st.write(f"身高: {user_data.get('height', 0)} cm")
        w = log.get('weight', user_data.get('weight', 0))
        
        if is_editable:
            new_w = st.number_input("今日体重", value=float(w), key=f"nw_{name}")
            # 围度录入
            g1, g2 = st.columns(2)
            waist = g1.number_input("腰围", value=float(log.get('waist',0)), key=f"wa_{name}")
            hip = g2.number_input("臀围", value=float(log.get('hip',0)), key=f"hi_{name}")
            if st.button("💾 同步今日数据", key=f"sv_{name}"):
                try:
                    supabase.table("daily_logs").upsert({
                        "user_name": name, "log_date": str(view_date), 
                        "weight": new_w, "waist": waist, "hip": hip
                    }, on_conflict="user_name,log_date").execute()
                    st.rerun()
                except Exception as e: st.error(e)
        else:
            st.write(f"体重: {w} kg")
            st.write(f"腰围: {log.get('waist', 0)} | 臀围: {log.get('hip', 0)}")
        st.markdown('</div>', unsafe_allow_html=True)

        # 2. 饮食卡 (带 BMR 计算)
        st.markdown('<div class="card"><b>🍱 饮食与卡路里</b>', unsafe_allow_html=True)
        bmr = 10 * float(w) + 6.25 * user_data.get('height', 0) - 5 * user_data.get('age', 0) - 161
        st.write(f"BMR: {int(bmr)} kcal | 建议: {int(bmr*1.2)} kcal")
        st.write(f"已摄入: {log.get('calories_in', 0)} kcal")
        
        if is_editable:
            if st.file_uploader("拍美食", type=['jpg','png'], key=f"f_{name}"):
                if st.button("AI识别(模拟)", key=f"fb_{name}"):
                    cal = random.randint(300, 600)
                    supabase.table("daily_logs").upsert({
                        "user_name": name, "log_date": str(view_date), 
                        "calories_in": log.get('calories_in', 0) + cal
                    }, on_conflict="user_name,log_date").execute()
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# 渲染左右布局
# 注意：左侧永远显示不差儿，右侧永远显示花大爷，或者根据当前用户调整
# 这里设定左侧为好友，右侧为自己，实现对垒感
render_column(other_name, col_left, False, res_other.data[0] if other_exists else None)
render_column(my_name, col_right, True, res_me.data[0] if me_exists else None)

# 侧边栏登出
if st.sidebar.button("登出 (切换账号)"):
    st.session_state.clear()
    st.rerun()
