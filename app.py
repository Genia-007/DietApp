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
DARK_TEXT = "#1A1A1A"  # 强制深色文字，解决看不清问题
LIGHT_BG = "#FFFFFF"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# --- 3. UI 样式注入 (修复对比度、强制并排、对称布局) ---
st.markdown(f"""
    <style>
    /* 强制深色文字，无视深色模式 */
    html, body, [data-testid="stAppViewContainer"], .stMarkdown, p, span, label, div {{
        color: {DARK_TEXT} !important;
        background-color: #F5F7F7 !important;
    }}
    .stApp {{ background-color: #F5F7F7; }}
    
    /* 左右强制对齐卡片 */
    .card {{
        background-color: {LIGHT_BG};
        padding: 20px;
        border-radius: 15px;
        border-top: 5px solid {TIFFANY_BLUE};
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        color: {DARK_TEXT} !important;
    }}
    
    /* 强制移动端双列不折叠 */
    [data-testid="column"] {{
        width: 50% !important;
        flex: 1 1 50% !important;
        min-width: 50% !important;
        padding: 5px !important;
    }}
    
    .stButton>button {{
        background-color: {TIFFANY_BLUE};
        color: white !important;
        border-radius: 12px;
        width: 100%;
        border: none;
        font-weight: bold;
    }}
    h3 {{ color: #088F8A !important; text-align: center; margin-bottom: 10px; }}
    .stMetric {{ background: white; padding: 10px; border-radius: 10px; border: 1px solid #eee; }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. 核心功能函数 ---
def calculate_age(birth_date):
    if not birth_date: return 0
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

def get_ai_analysis(image, mode="food"):
    """DeepSeek 接入与 Fallback 兜底"""
    try:
        # 此处模拟 API 请求流程，实际部署需对接 DeepSeek 接口
        if mode == "food":
            return {"cal": random.randint(250, 600), "p": 20, "f": 10, "c": 45, "fiber": 5}
        return round(random.uniform(18.0, 28.0), 1)
    except Exception:
        if mode == "food": return {"cal": 350, "p": 15, "f": 10, "c": 40, "fiber": 4}
        return 22.0

# --- 5. 身份登录与初始化逻辑 ---
if 'user_role' not in st.session_state:
    st.image("app_icon.png", width=120) if os.path.exists("app_icon.png") else st.title("🎨")
    st.markdown('<div class="card"><h3>👤 请选择登录身份</h3>', unsafe_allow_html=True)
    role_choice = st.radio("选择我是：", ["花大爷", "不差儿"], horizontal=True)
    if st.button("进入系统"):
        st.session_state.user_role = role_choice
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

my_name = st.session_state.user_role
other_name = "不差儿" if my_name == "花大爷" else "花大爷"

# 数据库判定初始化 (必须基于数据库)
try:
    res_me = supabase.table("users").select("*").eq("name", my_name).execute()
    initialized = True if res_me.data and len(res_me.data) > 0 else False
except Exception as e:
    st.error(f"数据库连接失败: {e}")
    st.stop()

if not initialized:
    st.markdown(f'<div class="card"><h3>🐣 首次进入，请完成初始化 ({my_name})</h3>', unsafe_allow_html=True)
    with st.form("init_form"):
        birth = st.date_input("选择生日", value=date(2000, 1, 1))
        u_age = calculate_age(birth)
        st.write(f"自动计算年龄: **{u_age}** 岁")
        u_height = st.number_input("身高 (cm)", value=165, step=1)
        u_weight = st.number_input("初始体重 (kg)", value=60.0)
        u_gender = st.radio("性别", ["女", "男"], index=0)
        if st.form_submit_button("🚀 完成初始化"):
            try:
                supabase.table("users").upsert({
                    "name": my_name, "birthday": str(birth), "age": int(u_age),
                    "height": int(u_height), "weight": float(u_weight), "gender": u_gender
                }, on_conflict="name").execute()
                st.success("初始化完成！")
                st.rerun()
            except Exception as e: st.error(f"数据库操作失败: {e}")
    st.stop()

# --- 6. 数据同步拉取 ---
try:
    me_base = supabase.table("users").select("*").eq("name", my_name).execute().data[0]
    friend_data = supabase.table("users").select("*").eq("name", other_name).execute()
    other_base = friend_data.data[0] if friend_data.data else None
except Exception as e:
    st.error(e)
    st.stop()

# 顶部导航
st.image("app_icon.png", width=120)
view_date = st.date_input("📅 查看日期", date.today())

# --- 7. 主界面：左右对齐双人分栏 ---
col_left, col_right = st.columns(2)

def render_column(name, col, is_editable, base_info):
    try:
        l_res = supabase.table("daily_logs").select("*").eq("user_name", name).eq("log_date", str(view_date)).execute()
        log = l_res.data[0] if l_res.data else {}
    except: log = {}

    with col:
        st.markdown(f"### {'👩‍𝓠' if name=='不差儿' else '👨‍🦳'} {name}")
        
        if not base_info:
            st.info(f"等待 {name} 初始化资料...")
            return

        # (1) 身体指标：对称设计
        st.markdown('<div class="card"><b>📊 身体指标</b>', unsafe_allow_html=True)
        h = base_info['height']
        w = log.get('weight', base_info['weight'])
        st.write(f"📏 身高: **{h}** cm (只读)")
        
        if is_editable:
            new_w = st.number_input("体重 (kg)", value=float(w), key=f"w_{name}")
            bmi = round(new_w / ((h/100)**2), 1)
            st.write(f"⚖️ BMI: {bmi}")
            
            # 体脂率 AI 逻辑
            fat = log.get('body_fat', 0.0)
            fat_img = st.file_uploader("📷 上传露腹照片分析体脂", type=['jpg','png'], key=f"fi_{name}")
            if st.button("AI 分析体脂率", key=f"fb_{name}"):
                if not fat_img: st.warning("请上传露腹照片！")
                else:
                    fat = get_ai_analysis(fat_img, "fat")
                    try:
                        supabase.table("daily_logs").upsert({"user_name": name, "log_date": str(view_date), "body_fat": fat}, on_conflict="user_name,log_date").execute()
                        st.rerun()
                    except: pass
            st.write(f"🔥 体脂率: **{fat}%**")
            
            # 围度全字段编辑
            g1, g2 = st.columns(2)
            chest = g1.number_input("胸围", value=float(log.get('chest',0)), key=f"ch_{name}")
            waist = g2.number_input("腰围", value=float(log.get('waist',0)), key=f"wa_{name}")
            arm = g1.number_input("臂围", value=float(log.get('arm',0)), key=f"ar_{name}")
            hip = g2.number_input("臀围", value=float(log.get('hip',0)), key=f"hi_{name}")
            thigh = g1.number_input("大腿", value=float(log.get('thigh',0)), key=f"th_{name}")
            calf = g2.number_input("小腿", value=float(log.get('calf',0)), key=f"ca_{name}")

            if st.button("💾 保存身体数据", key=f"sv_{name}"):
                try:
                    supabase.table("daily_logs").upsert({
                        "user_name": name, "log_date": str(view_date), "weight": new_w,
                        "chest": chest, "waist": waist, "arm": arm, "hip": hip, "thigh": thigh, "calf": calf
                    }, on_conflict="user_name,log_date").execute()
                    st.rerun()
                except Exception as e: st.error(e)
        else:
            # 只读对齐显示
            st.write(f"⚖️ 体重: **{w}** kg")
            st.write(f"⚖️ BMI: {round(float(w)/((h/100)**2), 1)}")
            st.write(f"🔥 体脂率: **{log.get('body_fat', 0)}%**")
            st.write(f"胸围: {log.get('chest',0)} | 腰围: {log.get('waist',0)}")
            st.write(f"臂围: {log.get('arm',0)} | 臀围: {log.get('hip',0)}")
            st.write(f"大腿: {log.get('thigh',0)} | 小腿: {log.get('calf',0)}")
        st.markdown('</div>', unsafe_allow_html=True)

        # (2) 饮食打卡
        st.markdown('<div class="card"><b>🍱 饮食打卡</b>', unsafe_allow_html=True)
        # BMR 计算
        bmr = 10 * float(w) + 6.25 * h - 5 * base_info['age'] - 161
        suggested = int(bmr * 1.2)
        consumed = log.get('calories_in', 0)
        st.write(f"🎯 建议摄入: **{suggested}** kcal (BMR: {int(bmr)})")
        st.write(f"已摄入: **{consumed}** kcal")
        
        if is_editable:
            water = st.number_input("饮水 (ml)", value=int(log.get('water', 0)), key=f"wat_{name}")
            m_img = st.file_uploader("饮食图片", type=['jpg','png'], key=f"mi_{name}")
            if m_img and st.button("AI 分析卡路里", key=f"mib_{name}"):
                res = get_ai_analysis(m_img, "food")
                try:
                    supabase.table("daily_logs").upsert({
                        "user_name": name, "log_date": str(view_date), 
                        "calories_in": consumed + res['cal'], "water": water,
                        "protein": log.get('protein',0)+res['p'], "fat": log.get('fat',0)+res['f'],
                        "carbs": log.get('carbs',0)+res['c'], "fiber": log.get('fiber',0)+res['fiber']
                    }, on_conflict="user_name,log_date").execute()
                    st.rerun()
                except: pass
            st.caption(f"营养：碳水{log.get('carbs',0)}g | 蛋{log.get('protein',0)}g | 脂{log.get('fat',0)}g")
        st.markdown('</div>', unsafe_allow_html=True)

        # (3) 健身打卡
        st.markdown('<div class="card"><b>🏋️ 健身打卡</b>', unsafe_allow_html=True)
        ex_cal = log.get('calories_out', 0)
        if is_editable:
            st.file_uploader("运动配图", type=['jpg','png'], key=f"exi_{name}")
            ex_t = st.text_input("运动类型", value=log.get('ex_type', ""), key=f"ext_{name}")
            ex_d = st.number_input("运动时长 (min)", value=int(log.get('ex_duration', 0)), key=f"exd_{name}")
            if st.button("同步运动消耗", key=f"exb_{name}"):
                burn = ex_d * random.randint(5, 10)
                try:
                    supabase.table("daily_logs").upsert({
                        "user_name": name, "log_date": str(view_date), 
                        "ex_type": ex_t, "ex_duration": ex_d, "calories_out": burn
                    }, on_conflict="user_name,log_date").execute()
                    st.rerun()
                except: pass
        st.write(f"运动消耗: **{ex_cal}** kcal")
        st.write(f"今日总消耗: **{int(bmr + ex_cal)}** kcal")
        st.markdown('</div>', unsafe_allow_html=True)

        # (4) 健康心得
        st.markdown('<div class="card"><b>💭 健康心得</b>', unsafe_allow_html=True)
        if is_editable:
            note = st.text_area("记录今日心情...", value=log.get('note', ""), key=f"nt_{name}")
            st.file_uploader("心得配图", type=['jpg','png'], key=f"nti_{name}")
            if st.button("发布心得", key=f"ntb_{name}"):
                try:
                    supabase.table("daily_logs").upsert({
                        "user_name": name, "log_date": str(view_date), "note": note
                    }, on_conflict="user_name,log_date").execute()
                    st.rerun()
                except: pass
        else:
            st.info(log.get('note', '对方还没写心得哦~'))
        st.markdown('</div>', unsafe_allow_html=True)

# 渲染对垒布局 (左侧固定不差儿，右侧固定花大爷)
render_column("不差儿", col_left, (my_name == "不差儿"), other_base)
render_column("花大爷", col_right, (my_name == "花大爷"), me_base)

# 退出功能
if st.sidebar.button("登出 / 切换身份"):
    st.session_state.clear()
    st.rerun()
