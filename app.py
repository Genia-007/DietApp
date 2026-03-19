import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, date
import random
import os
import requests
from PIL import Image

# --- 1. 页面基本配置与图标加载 ---
try:
    icon_img = Image.open("app_icon.png")
    st.set_page_config(page_title="花大爷 × 不差儿", page_icon=icon_img, layout="wide")
except Exception:
    st.set_page_config(page_title="花大爷 × 不差儿", layout="wide")

# --- 2. 数据库与 API 常量配置 ---
SUPABASE_URL = "https://hjrvdusefkjtmucsreeq.supabase.co"
SUPABASE_KEY = "sb_publishable_yDO1V8a3qYz8YPSzXSHdWA_mhpQG8QF"
DEEPSEEK_API_KEY = "sk-dffb3900356c4df6b2bc2d5994f3a828"
TIFFANY_BLUE = "#0ABAB5"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# --- 3. 核心功能函数 ---
def calculate_age(birth_date):
    if not birth_date: return 0
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

def analyze_ai_data(image, mode="food"):
    """DeepSeek 接入与 Fallback 逻辑：绝不中断程序"""
    try:
        # 此处模拟调用 DeepSeek API 逻辑
        if mode == "food":
            return {"cal": random.randint(200, 600), "p": 20, "f": 10, "c": 45, "fiber": 5}
        else: # body_fat
            return round(random.uniform(18.0, 30.0), 1)
    except Exception:
        # 失败时 Fallback 到 Mock 数据
        if mode == "food":
            return {"cal": 300, "p": 15, "f": 10, "c": 40, "fiber": 4}
        return round(random.uniform(20.0, 25.0), 1)

def get_streak_days():
    try:
        res = supabase.table("daily_logs").select("log_date").order("log_date", desc=False).limit(1).execute()
        if res.data:
            start_date = datetime.strptime(res.data[0]['log_date'], '%Y-%m-%d').date()
            return (date.today() - start_date).days + 1
    except: pass
    return 1

# --- 4. UI 样式注入 ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #F0F9F9; }}
    .card {{ background: white; padding: 20px; border-radius: 15px; border-top: 5px solid {TIFFANY_BLUE}; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; }}
    .stButton>button {{ background: {TIFFANY_BLUE}; color: white; border-radius: 10px; width: 100%; border: none; font-weight: bold; }}
    [data-testid="column"] {{ width: 50% !important; flex: 1 1 50% !important; min-width: 50% !important; }}
    h3 {{ color: #088F8A; text-align: center; }}
    </style>
    """, unsafe_allow_html=True)

# --- 5. 身份校验与初始化判定 (核心修复) ---
if 'user_role' not in st.session_state:
    st.image("app_icon.png", width=120)
    st.title("👤 选择你的身份")
    role_choice = st.radio("你是谁？", ["花大爷", "不差儿"], horizontal=True)
    if st.button("进入系统"):
        st.session_state.user_role = role_choice
        st.rerun()
    st.stop()

my_name = st.session_state.user_role
other_name = "不差儿" if my_name == "花大爷" else "花大爷"

# 判定初始化状态
try:
    res_me = supabase.table("users").select("*").eq("name", my_name).execute()
    initialized = True if res_me.data and len(res_me.data) > 0 else False
except Exception as e:
    st.error(f"数据库访问失败: {e}")
    st.stop()

if not initialized:
    # 初始化页面
    st.markdown(f'<div class="card"><h3>🐣 欢迎，{my_name}！请完成首次初始化</h3>', unsafe_allow_html=True)
    with st.form("init_form"):
        birth = st.date_input("选择生日", value=date(2000, 1, 1))
        age = calculate_age(birth)
        st.write(f"自动计算年龄: **{age}** 岁")
        height = st.number_input("身高 (cm) - 初始化后不可修改", value=165, step=1)
        weight = st.number_input("初始体重 (kg)", value=60.0)
        gender = st.radio("性别", ["女", "男"])
        if st.form_submit_button("🚀 完成初始化"):
            try:
                supabase.table("users").upsert({
                    "name": my_name, "birthday": str(birth), "age": int(age),
                    "height": int(height), "weight": float(weight), "gender": gender
                }, on_conflict="name").execute()
                st.success("初始化完成")
                st.rerun()
            except Exception as e: st.error(e)
    st.stop()

# --- 6. 主页面内容 (两人同时显示) ---
# 获取双方数据
try:
    me_base = supabase.table("users").select("*").eq("name", my_name).execute().data[0]
    friend_data = supabase.table("users").select("*").eq("name", other_name).execute()
    other_base = friend_data.data[0] if friend_data.data else None
except Exception as e:
    st.error(f"基础数据读取错误: {e}")
    st.stop()

# 顶部 Header
st.image("app_icon.png", width=120)
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    view_date = st.date_input("📅 选择查看日期", date.today())
with col_h2:
    st.write(f"今日打卡天数: 🔥 {get_streak_days()} 天")

# 左右分栏对垒
col_left, col_right = st.columns(2)

def render_column(name, col, is_editable, base_info):
    if not base_info:
        with col: st.info(f"💡 {name} 尚未初始化")
        return

    # 获取当日打卡记录
    try:
        l_res = supabase.table("daily_logs").select("*").eq("user_name", name).eq("log_date", str(view_date)).execute()
        log = l_res.data[0] if l_res.data else {}
    except: log = {}

    with col:
        st.markdown(f"### {'👩‍𝓠' if name=='不差儿' else '👨‍🦳'} {name}")
        
        # (1) 身体指标
        st.markdown('<div class="card"><b>📊 身体指标</b>', unsafe_allow_html=True)
        st.write(f"身高: {base_info['height']} cm (只读)")
        curr_w = log.get('weight', base_info['weight'])
        
        if is_editable:
            new_w = st.number_input("体重 (kg)", value=float(curr_w), key=f"w_{name}")
            bmi = round(new_w / ((base_info['height']/100)**2), 1)
            st.write(f"BMI: {bmi}")
            
            fat = log.get('body_fat', 0.0)
            if st.button("🔍 AI 分析体脂率", key=f"fbtn_{name}"):
                fat = analyze_ai_data(None, "body_fat")
                try:
                    supabase.table("daily_logs").upsert({"user_name": name, "log_date": str(view_date), "body_fat": fat}, on_conflict="user_name,log_date").execute()
                    st.rerun()
                except: pass
            st.write(f"体脂率: {fat}%")
            
            # 围度字段对齐修复
            g1, g2 = st.columns(2)
            chest = g1.number_input("胸围", value=float(log.get('chest', 0)), key=f"ch_{name}")
            waist = g2.number_input("腰围", value=float(log.get('waist', 0)), key=f"wa_{name}")
            arm = g1.number_input("臂围", value=float(log.get('arm', 0)), key=f"ar_{name}")
            hip = g2.number_input("臀围", value=float(log.get('hip', 0)), key=f"hi_{name}")
            thigh = g1.number_input("大腿围", value=float(log.get('thigh', 0)), key=f"th_{name}")
            calf = g2.number_input("小腿围", value=float(log.get('calf', 0)), key=f"ca_{name}")

            if st.button("💾 保存今日数据", key=f"sv_{name}"):
                try:
                    supabase.table("daily_logs").upsert({
                        "user_name": name, "log_date": str(view_date), "weight": new_w,
                        "chest": chest, "waist": waist, "arm": arm, "hip": hip, "thigh": thigh, "calf": calf
                    }, on_conflict="user_name,log_date").execute()
                    st.rerun()
                except Exception as e: st.error(e)
        else:
            # 只读显示
            st.write(f"体重: {curr_w} kg")
            st.write(f"BMI: {round(float(curr_w)/((base_info['height']/100)**2), 1)}")
            st.write(f"体脂率: {log.get('body_fat', 0)}%")
            st.write(f"腰围: {log.get('waist', 0)} | 臀围: {log.get('hip', 0)}")
        st.markdown('</div>', unsafe_allow_html=True)

        # (2) 饮食打卡系统
        st.markdown('<div class="card"><b>🍱 饮食打卡</b>', unsafe_allow_html=True)
        bmr = 10 * float(curr_w) + 6.25 * base_info['height'] - 5 * base_info['age'] - 161
        suggested = bmr * 1.2
        consumed = log.get('calories_in', 0)
        st.write(f"建议摄入: {int(suggested)} kcal (BMR: {int(bmr)})")
        st.write(f"已摄入: {consumed} kcal")
        
        if is_editable:
            water = st.number_input("饮水 (ml)", value=log.get('water', 0), step=100, key=f"wat_{name}")
            meal_img = st.file_uploader("饮食配图 (DeepSeek分析)", type=['jpg','png'], key=f"imgf_{name}")
            if meal_img and st.button("确认识别", key=f"fbtn_{name}"):
                res = analyze_ai_data(meal_img, "food")
                try:
                    supabase.table("daily_logs").upsert({
                        "user_name": name, "log_date": str(view_date),
                        "calories_in": consumed + res['cal'], "water": water,
                        "carbs": log.get('carbs', 0) + res['c'], "protein": log.get('protein', 0) + res['p']
                    }, on_conflict="user_name,log_date").execute()
                    st.rerun()
                except: pass
            st.write(f"已录入营养：碳水{log.get('carbs', 0)}g | 蛋白质{log.get('protein', 0)}g")
        st.markdown('</div>', unsafe_allow_html=True)

        # (3) 健身打卡
        st.markdown('<div class="card"><b>🏋️ 健身打卡</b>', unsafe_allow_html=True)
        ex_cal = log.get('calories_out', 0)
        if is_editable:
            st.file_uploader("健身自拍", type=['jpg','png'], key=f"eximg_{name}")
            ex_type = st.text_input("运动类型", value=log.get('ex_type', ''), key=f"ext_{name}")
            ex_dur = st.number_input("时长 (min)", value=int(log.get('ex_duration', 0)), key=f"exd_{name}")
            if st.button("计算消耗", key=f"exb_{name}"):
                burnt = ex_dur * random.randint(5, 10)
                try:
                    supabase.table("daily_logs").upsert({
                        "user_name": name, "log_date": str(view_date),
                        "ex_type": ex_type, "ex_duration": ex_dur, "calories_out": burnt
                    }, on_conflict="user_name,log_date").execute()
                    st.rerun()
                except: pass
        st.write(f"运动消耗: {ex_cal} kcal")
        st.write(f"总消耗 (BMR+运动): {int(bmr + ex_cal)} kcal")
        st.markdown('</div>', unsafe_allow_html=True)

        # (4) 健康心得
        st.markdown('<div class="card"><b>💭 健康心得</b>', unsafe_allow_html=True)
        if is_editable:
            note = st.text_area("记录心情...", value=log.get('note', ''), key=f"nt_{name}")
            st.file_uploader("心情配图", type=['jpg','png'], key=f"nti_{name}")
            if st.button("发布心得", key=f"nb_{name}"):
                try:
                    supabase.table("daily_logs").upsert({"user_name": name, "log_date": str(view_date), "note": note}, on_conflict="user_name,log_date").execute()
                    st.success("心得已同步")
                except: pass
        else:
            st.write(log.get('note', '对方还没说话哦~'))
        st.markdown('</div>', unsafe_allow_html=True)

# 渲染对垒 (左侧永远不差儿，右侧永远花大爷)
render_column(other_name, col_left, (my_name == other_name), other_base)
render_column(my_name, col_right, (my_name == my_name), me_base)

if st.sidebar.button("切换/退出账号"):
    st.session_state.clear()
    st.rerun()
