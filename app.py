import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, date
import random
import os
from PIL import Image

# --- 1. 页面配置与图标加载 ---
try:
    icon = Image.open("app_icon.png")
    st.set_page_config(
        page_title="花大爷 × 不差儿",
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="collapsed"
    )
except Exception:
    st.set_page_config(page_title="花大爷 × 不差儿", layout="wide")

# --- 2. 样式注入 (蒂芙尼蓝 #0ABAB5) ---
st.markdown("""
    <style>
    .stApp { background-color: #F0F9F9; }
    [data-testid="stMetricValue"] { color: #0ABAB5 !important; }
    .main-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        border-top: 5px solid #0ABAB5;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .stButton>button {
        background-color: #0ABAB5;
        color: white;
        border-radius: 10px;
        width: 100%;
    }
    /* 强制移动端双列不折叠 */
    [data-testid="column"] {
        width: 50% !important;
        flex: 1 1 50% !important;
        min-width: 50% !important;
    }
    h3 { color: #088F8A; font-size: 1.2rem !important; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 模拟 AI 函数 ---
def mock_calorie():
    return random.randint(200, 800)

def mock_body_fat():
    return round(random.uniform(18.0, 30.0), 1)

def calc_age(birthday):
    today = date.today()
    return today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))

def calc_bmr(w, h, age, gender):
    # Mifflin-St Jeor 公式
    if gender == "女":
        return int(10 * w + 6.25 * h - 5 * age - 161)
    return int(10 * w + 6.25 * h - 5 * age + 5)

# --- 4. 数据库初始化 ---
# 建议在 Streamlit Secrets 中配置，此处保留占位
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception:
    st.error("请在 Streamlit Secrets 中配置 SUPABASE_URL 和 SUPABASE_KEY")
    st.stop()

# --- 5. 登录与初始化逻辑 ---
if 'user_role' not in st.session_state:
    col_img, col_form = st.columns([1, 2])
    with col_img:
        if os.path.exists("app_icon.png"):
            st.image("app_icon.png", width=150)
    with col_form:
        st.markdown("### 🎨 开启双人打卡基地")
        with st.form("init_form"):
            role = st.selectbox("👤 你是谁？", ["花大爷", "不差儿"])
            bday = st.date_input("🎂 生日", value=date(2000, 1, 1))
            height = st.number_input("📏 身高 (cm)", 100, 250, 163)
            weight = st.number_input("⚖️ 体重 (kg)", 30.0, 200.0, 61.5)
            gender = st.radio("🚻 性别", ["女", "男"], index=0)
            
            if st.form_submit_button("🚀 进入系统"):
                age = calc_age(bday)
                user_data = {
                    "name": role,
                    "age": age,
                    "height": height,
                    "weight": weight,
                    "gender": gender
                }
                try:
                    supabase.table("users").upsert(user_data, on_conflict="name").execute()
                    st.session_state.user_role = role
                    st.session_state.u_info = user_data
                    st.rerun()
                except Exception as e:
                    st.error(f"保存失败: {e}")
    st.stop()

# --- 6. 首页结构 ---
role_me = st.session_state.user_role
u_info = st.session_state.u_info

# 顶部状态栏
st.markdown(f"**📅 {date.today()}** | 🌦️ 天气：晴转多云 22°C | 🔥 已连续打卡：7天")
if os.path.exists("app_icon.png"):
    st.image("app_icon.png", width=80)

view_date = st.date_input("查看历史记录", date.today())

# 左右布局
col_left, col_right = st.columns(2)

def render_column(name, col, is_me):
    with col:
        st.markdown(f"### {'👨‍🦳' if name=='花大爷' else '👩‍𝓠'} {name}")
        
        # 获取当日数据
        try:
            res = supabase.table("daily_logs").select("*").eq("user_name", name).eq("date", str(view_date)).execute()
            data = res.data[0] if res.data else {}
        except:
            data = {}

        # (1) 身体指标
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.write("**📊 身体指标**")
        c1, c2 = st.columns(2)
        curr_w = data.get("weight", 0)
        curr_h = u_info["height"] if is_me else 165 # 假设对方身高
        bmi = round(curr_w / ((curr_h/100)**2), 1) if curr_w > 0 else 0
        
        c1.metric("体重", f"{curr_w} kg")
        c2.metric("BMI", bmi)
        
        fat = data.get("body_fat", 0)
        st.write(f"体脂率: {fat}%")
        if is_me:
            if st.button("AI 模拟生成体脂", key=f"fat_{name}"):
                fat = mock_body_fat()
                try:
                    supabase.table("daily_logs").upsert({"user_name": name, "date": str(view_date), "body_fat": fat}, on_conflict="user_name,date").execute()
                    st.rerun()
                except: pass
        
        st.write("围度 (cm):")
        w_cols = st.columns(3)
        w_cols[0].caption(f"胸: {data.get('chest', 0)}")
        w_cols[1].caption(f"腰: {data.get('waist', 0)}")
        w_cols[2].caption(f"臂: {data.get('arm', 0)}")
        st.markdown('</div>', unsafe_allow_html=True)

        # (2) 饮食打卡
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.write("**🍱 饮食打卡**")
        bmr = calc_bmr(u_info["weight"], u_info["height"], u_info["age"], u_info["gender"]) if is_me else 1400
        st.write(f"建议摄入: {bmr} kcal")
        st.write(f"已摄入: {data.get('calories_in', 0)} kcal")
        
        if is_me:
            water = st.number_input("饮水量 (ml)", 0, 5000, data.get("water", 0), step=250, key=f"water_{name}")
            meal = st.file_uploader("上传早餐/午餐/晚餐图片", type=["png", "jpg"], key=f"meal_{name}")
            if meal:
                cal = mock_calorie()
                st.info(f"AI 分析本次摄入: {cal} kcal")
                if st.button("确认记录该餐点", key=f"confirm_{name}"):
                    new_cal = data.get('calories_in', 0) + cal
                    try:
                        supabase.table("daily_logs").upsert({"user_name": name, "date": str(view_date), "calories_in": new_cal, "water": water}, on_conflict="user_name,date").execute()
                        st.rerun()
                    except: pass
        st.markdown('</div>', unsafe_allow_html=True)

        # (3) 健身打卡
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.write("**🏋️ 健身打卡**")
        if is_me:
            ex_type = st.text_input("运动类型", data.get("ex_type", ""), key=f"ext_{name}")
            ex_time = st.number_input("时长 (min)", 0, 300, data.get("ex_time", 0), key=f"exm_{name}")
            if st.button("同步健身消耗", key=f"exb_{name}"):
                ex_cal = int(ex_time * 8) # 模拟消耗
                try:
                    supabase.table("daily_logs").upsert({
                        "user_name": name, "date": str(view_date), 
                        "ex_type": ex_type, "ex_time": ex_time, "calories_out": ex_cal
                    }, on_conflict="user_name,date").execute()
                    st.rerun()
                except: pass
        
        st.write(f"消耗: {data.get('calories_out', 0)} kcal")
        st.write(f"总消耗 (BMR+运动): {bmr + data.get('calories_out', 0)} kcal")
        st.markdown('</div>', unsafe_allow_html=True)

        # (4) 健康心得
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.write("**✍️ 健康心得**")
        if is_me:
            note = st.text_area("记录今天的心情...", data.get("note", ""), key=f"note_{name}")
            if st.button("保存笔记", key=f"noteb_{name}"):
                try:
                    supabase.table("daily_logs").upsert({"user_name": name, "date": str(view_date), "note": note}, on_conflict="user_name,date").execute()
                    st.success("笔记已同步")
                except: pass
        else:
            st.info(data.get("note", "对方还没写心得哦~"))
        st.markdown('</div>', unsafe_allow_html=True)

# 渲染左右分栏
render_column("不差儿", col_left, is_me=(role_me == "不差儿"))
render_column("花大爷", col_right, is_me=(role_me == "花大爷"))

if st.button("退出登录"):
    del st.session_state.user_role
    st.rerun()
