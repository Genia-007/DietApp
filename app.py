import streamlit as st
import pandas as pd
import httpx
from datetime import datetime, date, timedelta
import json

# --- 1. 配置与专属图标 ---
# 确保你的照片 6af1af85193fb5400cc2503413532cbe.jpg 就在 DietApp 文件夹下
st.set_page_config(
    layout="wide", 
    page_title="花大爷 & 不差儿 智能基地", 
    page_icon="6af1af85193fb5400cc2503413532cbe.jpg"
)

# 🎨 蒂芙尼蓝风格 CSS
st.markdown("""
    <style>
    .stApp { background-color: #F0F9F9; }
    :root { --tiffany-blue: #0ABAB5; --deep-teal: #088F8A; }
    .main-card { 
        background: white; padding: 25px; border-radius: 35px; 
        border-top: 8px solid var(--tiffany-blue); 
        box-shadow: 0 8px 20px rgba(0,0,0,0.05); margin-bottom: 25px; 
    }
    .header-style { color: var(--deep-teal); font-weight: bold; margin-bottom: 15px; }
    div[data-testid="stMetricValue"] { color: var(--tiffany-blue) !important; font-size: 1.8rem !important; }
    .stButton>button { background-color: var(--tiffany-blue); color: white; border-radius: 20px; width: 100%; border: none; height: 45px;}
    </style>
    """, unsafe_allow_html=True)

# 🔑 钥匙配置
SUPABASE_URL = "https://hjrvdusefkjtmucsreeq.supabase.co"
SUPABASE_KEY = "sb_publishable_yDO1V8a3qYz8YPSzXSHdWA_mhpQG8QF"

# --- 2. 核心功能函数 ---
def call_supabase(method, data=None, query=""):
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
    url = f"{SUPABASE_URL}/rest/v1/diet_records{query}"
    try:
        with httpx.Client() as client:
            if method == "POST": return client.post(url, json=data, headers=headers)
            return client.get(url, headers=headers)
    except: return None

# --- 3. 登录与身份判断 ---
if 'user_role' not in st.session_state:
    with st.form("login"):
        st.markdown("<h2 style='text-align:center; color:#0ABAB5;'>🎨 开启双人打卡基地</h2>", unsafe_allow_html=True)
        role = st.selectbox("👤 选择身份", ["花大爷", "不差儿"])
        c1, c2, c3 = st.columns(3)
        age = c1.number_input("🎂 年龄", value=25)
        height = c2.number_input("📏 身高 (cm)", value=170.0)
        gender = c3.selectbox("🚻 性别", ["男", "女"])
        if st.form_submit_button("🚀 进入基地"):
            st.session_state.user_role = role
            # 计算建议卡路里 (Mifflin-St Jeor 公式)
            s_cal = (10 * 60 + 6.25 * height - 5 * age + (5 if gender=="男" else -161)) * 1.3
            st.session_state.base_info = {"age": age, "height": height, "gender": gender, "s_cal": s_cal}
            st.rerun()
    st.stop()

# --- 4. 顶部数据预加载 ---
all_res = call_supabase("GET", query="?order=created_at.desc")
full_db = pd.DataFrame(all_res.json()) if all_res and all_res.status_code == 200 else pd.DataFrame()

# 计算打卡天数
def get_days(name):
    if full_db.empty: return 0
    u_dates = pd.to_datetime(full_db[full_db['user_name'] == name]['created_at']).dt.date
    return u_dates.nunique()

# 顶部日历与状态
st.markdown("<div class='main-card'>", unsafe_allow_html=True)
ca1, ca2, ca3 = st.columns([1, 2, 1])
with ca1:
    view_date = st.date_input("📅 历史回顾", date.today())
with ca2:
    st.markdown(f"<div style='text-align:center;'><h3 style='color:#0ABAB5;'>{view_date} 战况</h3><p>📍 所在地天气：舒适 22°C | 🦾 累计坚持 {get_days(st.session_state.user_role)} 天</p></div>", unsafe_allow_html=True)
with ca3:
    st.image("6af1af85193fb5400cc2503413532cbe.jpg", width=80)
st.markdown("</div>", unsafe_allow_html=True)

# 筛选当日数据
query_today = f"?created_at=gte.{view_date}T00:00:00&created_at=lt.{view_date + timedelta(days=1)}T00:00:00&order=created_at.desc"
res_today = call_supabase("GET", query=query_today)
day_db = pd.DataFrame(res_today.json()) if res_today and res_today.status_code == 200 else pd.DataFrame()

# --- 5. 渲染镜像对垒区 ---
col_left, col_right = st.columns(2)

def render_side(user_name, column, is_me):
    with column:
        avatar = "👨‍🦳" if user_name == "花大爷" else "👩‍𝓠"
        st.markdown(f"<h2 class='header-style'>{avatar} {user_name}</h2>", unsafe_allow_html=True)
        
        u_data = day_db[day_db['user_name'] == user_name] if not day_db.empty else pd.DataFrame()
        latest = u_data.iloc[0] if not u_data.empty else None

        # 1. 身体指标
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        st.write("📊 **身体指标记录**")
        if st.button(f"查看 {user_name} 历史趋势图", key=f"t_{user_name}"):
            p_db = full_db[full_db['user_name'] == user_name].copy()
            if not p_db.empty:
                p_db['created_at'] = pd.to_datetime(p_db['created_at'])
                st.line_chart(p_db.set_index('created_at')[['weight', 'body_fat']])

        if is_me:
            with st.form(f"form_body_{user_name}"):
                c1, c2 = st.columns(2)
                w = c1.number_input("体重 (kg)", value=float(latest['weight']) if latest is not None else 60.0)
                h = c2.number_input("身高 (cm)", value=float(latest['height']) if latest is not None else 170.0)
                c3, c4 = st.columns(2)
                bmi = w / ((h/100)**2)
                c3.metric("BMI", f"{bmi:.1f}")
                fat = c4.number_input("体脂率 (%)", value=float(latest['body_fat']) if latest is not None else 20.0)
                st.write("围度 (胸/腰/臂/臀/大腿/小腿)")
                d1, d2, d3 = st.columns(3)
                ch = d1.number_input("胸围", value=80.0); wa = d2.number_input("腰围", value=70.0); ar = d3.number_input("臂围", value=25.0)
                hi = d1.number_input("臀围", value=90.0); th = d2.number_input("大腿", value=55.0); ca = d3.number_input("小腿", value=35.0)
                if st.form_submit_button("💾 保存身体指标"):
                    payload = {"user_name":user_name, "weight":w, "height":h, "bmi":bmi, "body_fat":fat, "chest":ch, "waist":wa, "arm":ar, "hip":hi, "thigh":th, "calf":ca, "created_at":datetime.now().isoformat()}
                    call_supabase("POST", payload)
                    st.rerun()
        else:
            # 对方的信息展示
            m1, m2 = st.columns(2)
            m1.metric("体重", f"{latest['weight'] if latest is not None else 0} kg")
            m2.metric("BMI", f"{latest['bmi'] if latest is not None else 0:.1f}")
            st.write(f"胸/腰/臀: {latest['chest'] if latest is not None else 0}/{latest['waist'] if latest is not None else 0}/{latest['hip'] if latest is not None else 0}")
        st.markdown("</div>", unsafe_allow_html=True)

        # 2. 饮食打卡
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        st.write("🥗 **饮食打卡 (AI 分析)**")
        s_cal = st.session_state.base_info['s_cal']
        in_cal = u_data['in_calories'].sum() if not u_data.empty else 0
        st.metric("建议摄入 vs 已摄入", f"{s_cal:.0f} kcal", delta=f"{in_cal} kcal")
        st.caption(f"碳水: {u_data['carbs'].sum() if not u_data.empty else 0}g | 蛋白: {u_data['protein'].sum() if not u_data.empty else 0}g")
        
        if is_me:
            with st.form(f"form_diet_{user_name}"):
                wat = st.number_input("饮水量 (ml)", value=0, step=100)
                st.write("上传照片自动识别热量 (早/午/晚/加餐)")
                f1 = st.file_uploader("📸 餐饮照片", type=['jpg','png'])
                if st.form_submit_button("🚀 发布饮食并分析"):
                    # 模拟 AI 分析结果
                    payload = {"user_name":user_name, "water":wat, "in_calories": 450, "carbs":50, "protein":20, "created_at":datetime.now().isoformat()}
                    call_supabase("POST", payload)
                    st.rerun()
        else:
            st.write(f"今日已饮水: **{u_data['water'].sum() if not u_data.empty else 0} ml**")
            st.write(f"今日已摄入: **{in_cal} kcal**")
        st.markdown("</div>", unsafe_allow_html=True)

        # 3. 健身打卡
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        st.write("🏋️ **健身与总消耗**")
        bmr = 10 * (float(latest['weight']) if latest else 60) + 6.25 * (float(latest['height']) if latest else 170) - 150
        sport_cal = u_data['out_calories'].sum() if not u_data.empty else 0
        st.metric("总消耗 (基代+运动)", f"{bmr + sport_cal:.0f} kcal")
        
        if is_me:
            with st.form(f"form_sport_{user_name}"):
                st.file_uploader("🏋️ 运动照片")
                st_time = st.number_input("运动时长 (min)", value=0)
                st_item = st.text_input("运动项目")
                if st.form_submit_button("💾 同步健身数据"):
                    call_supabase("POST", {"user_name":user_name, "out_calories": st_time * 8, "workout":st_item, "created_at":datetime.now().isoformat()})
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # 4. 健康心得
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        st.write("💡 **健康心得**")
        if is_me:
            with st.form(f"form_note_{user_name}"):
                note = st.text_area("记录文字、图片、表情包...")
                if st.form_submit_button("🚀 发布心得"):
                    call_supabase("POST", {"user_name":user_name, "message_to_partner":note, "created_at":datetime.now().isoformat()})
                    st.rerun()
        else:
            st.info(latest['message_to_partner'] if latest and latest['message_to_partner'] else "对方还没写心得哦")
        st.markdown("</div>", unsafe_allow_html=True)

# 渲染对垒
render_side("不差儿", col_left, is_me=(st.session_state.user_role == "不差儿"))
render_side("花大爷", col_right, is_me=(st.session_state.user_role == "花大爷"))