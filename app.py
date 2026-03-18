import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, date, timedelta
import plotly.graph_objects as go
import random
from PIL import Image

# --- 1. 页面配置与图标 ---
st.set_page_config(
    page_title="花大爷 × 不差儿",
    page_icon="app_icon.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 🎨 蒂芙尼蓝 UI 注入
st.markdown("""
    <style>
    .stApp { background-color: #F0F9F9; }
    [data-testid="column"] { 
        padding: 10px; 
        border-radius: 20px; 
        background: white;
        margin: 5px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }
    .main-card {
        border-top: 5px solid #0ABAB5;
        padding: 15px;
        border-radius: 15px;
        margin-bottom: 20px;
    }
    h1, h2, h3 { color: #088F8A; }
    .stButton>button {
        background-color: #0ABAB5;
        color: white;
        border-radius: 12px;
        width: 100%;
        border: none;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. Supabase 客户端封装 ---
SUPABASE_URL = "https://hjrvdusefkjtmucsreeq.supabase.co"
SUPABASE_KEY = "sb_publishable_yDO1V8a3qYz8YPSzXSHdWA_mhpQG8QF"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_user_data(name):
    res = supabase.table("users").select("*").eq("name", name).execute()
    return res.data[0] if res.data else None

def get_daily_logs(name, log_date):
    res = supabase.table("daily_logs").select("*").eq("user", name).eq("date", str(log_date)).execute()
    return res.data[0] if res.data else {}

# --- 3. AI 模拟分析函数 ---
def mock_ai_calories(image):
    return random.randint(250, 750) if image else 0

def mock_ai_body_fat(image):
    return round(random.uniform(15.0, 30.0), 1) if image else 0

# --- 4. 核心计算公式 ---
def calculate_metrics(weight, height, age, gender):
    bmi = round(weight / ((height/100)**2), 1)
    # BMR (Mifflin-St Jeor)
    if gender == "女":
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    return bmi, int(bmr)

# --- 5. 登录初始化逻辑 ---
if 'user_role' not in st.session_state:
    st.image("app_icon.png", width=100)
    st.title("🎨 欢迎来到双人打卡基地")
    
    with st.form("init_form"):
        st.subheader("请选择身份并初始化资料")
        role = st.selectbox("身份", ["花大爷", "不差儿"])
        bday = st.date_input("生日", date(2000, 1, 1))
        h = st.number_input("身高 (cm)", 140, 200, 165)
        g = st.selectbox("性别", ["女", "男"], index=0)
        w = st.number_input("当前体重 (kg)", 30.0, 150.0, 55.0)
        
        if st.form_submit_button("进入系统"):
            age = (date.today() - bday).days // 365
            user_data = {
                "name": role, "age": age, "height": h, "gender": g, "weight": w
            }
            supabase.table("users").upsert(user_data, on_conflict="name").execute()
            st.session_state.user_role = role
            st.rerun()
    st.stop()

# --- 6. 首页 UI 渲染 ---
user_role = st.session_state.user_role
partner_role = "不差儿" if user_role == "花大爷" else "花大爷"

# 顶部日历与天气
st.image("app_icon.png", width=60)
t1, t2 = st.columns([2, 1])
with t1:
    view_date = st.date_input("📅 日历回顾", date.today())
with t2:
    st.write(f"🌤️ 杭州: 舒适 22°C")
    st.write(f"🔥 打卡天数: 12 天")

st.write("---")

# 左右布局：左(不差儿-只读) | 右(花大爷-可编辑)
col_left, col_right = st.columns(2)

def render_side(name, is_editable):
    container = st.container()
    with container:
        st.subheader(f"{'👨‍🦳' if name=='花大爷' else '👩‍𝓠'} {name}")
        
        u_info = get_user_data(name)
        log = get_daily_logs(name, view_date)
        
        if not u_info:
            st.warning("暂无基础数据")
            return

        bmi, bmr = calculate_metrics(u_info['weight'], u_info['height'], u_info['age'], u_info['gender'])

        # (1) 身体指标
        with st.expander("📊 身体指标", expanded=True):
            st.write(f"📏 身高: {u_info['height']}cm | 体重: {u_info['weight']}kg")
            st.metric("BMI", bmi)
            fat_val = log.get('body_fat', 0)
            st.write(f"🧬 体脂率: {fat_val if fat_val else '0'} %")
            
            if is_editable:
                img = st.file_uploader("上传图片分析体脂", key=f"fat_{name}", type=['png','jpg'])
                if st.button("AI 模拟分析体脂"):
                    new_fat = mock_ai_body_fat(img)
                    supabase.table("daily_logs").upsert({"user":name, "date":str(view_date), "body_fat":new_fat}, on_conflict="user,date").execute()
                    st.rerun()

            st.write("📐 围度记录 (cm)")
            st.caption(f"胸:{log.get('chest',0)} | 腰:{log.get('waist',0)} | 臀:{log.get('hip',0)}")
            
            if st.button("趋势查询 📈", key=f"trend_{name}"):
                fig = go.Figure(data=go.Scatter(x=[1,2,3,4], y=[60, 59, 58.5, 58], line=dict(color='#0ABAB5')))
                st.plotly_chart(fig, use_container_width=True)

        # (2) 饮食打卡
        with st.expander("🥗 饮食卡路里", expanded=True):
            st.write(f"💡 建议摄入: {bmr} kcal")
            curr_in = log.get('calorie_intake', 0)
            st.metric("已摄入", f"{curr_in} kcal", delta=f"{curr_in - bmr}")
            
            st.write(f"💧 饮水: {log.get('water', 0)} ml")
            
            if is_editable:
                meal_img = st.file_uploader("拍摄餐食 AI 识别", key=f"meal_{name}")
                water_add = st.number_input("加水 (ml)", 0, 1000, 250, step=50)
                if st.button("同步饮食数据"):
                    cal = mock_ai_calories(meal_img)
                    supabase.table("daily_logs").upsert({
                        "user":name, "date":str(view_date), 
                        "calorie_intake": curr_in + cal,
                        "water": log.get('water', 0) + water_add
                    }, on_conflict="user,date").execute()
                    st.rerun()
            
            st.caption("🥑 碳水: 45% | 蛋: 30% | 脂: 25%")

        # (3) 健身打卡
        with st.expander("🏋️ 健身打卡", expanded=True):
            burned = log.get('calorie_burn', 0)
            st.write(f"基础代谢: {bmr} kcal")
            st.write(f"运动消耗: {burned} kcal")
            st.metric("总消耗", f"{bmr + burned} kcal")
            
            if is_me := is_editable:
                st.text_input("运动类型", "慢跑", key=f"ex_type_{name}")
                if st.button("同步运动消耗"):
                    supabase.table("daily_logs").upsert({
                        "user":name, "date":str(view_date), "calorie_burn": 400
                    }, on_conflict="user,date").execute()
                    st.rerun()

        # (4) 健康心得
        with st.expander("💡 健康心得", expanded=True):
            st.write(log.get('note', "今天也要加油哦！✨"))
            if is_editable:
                new_note = st.text_area("写下心得...", key=f"note_input_{name}")
                if st.button("保存心得"):
                    supabase.table("daily_logs").upsert({
                        "user":name, "date":str(view_date), "note": new_note
                    }, on_conflict="user,date").execute()
                    st.rerun()

# 渲染左右两边
with col_left:
    render_side("不差儿", is_editable=False)

with col_right:
    render_side("花大爷", is_editable=True)
