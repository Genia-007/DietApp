import streamlit as st
import pandas as pd
import httpx
from datetime import datetime, date, timedelta
import json
import base64

# --- 1. 专属图标与 Favicon 修复 (Base64 技术) ---
# 请确保你的照片文件名与此处完全一致，且在 GitHub 仓库中
try:
    with open("6af1af85193fb5400cc2503413532cbe.jpg", "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    favicon = f"data:image/jpeg;base64,{encoded_string}"
    st.set_page_config(
        layout="wide", 
        page_title="花大爷 & 不差儿 智能基地", 
        page_icon=favicon # 使用 Base64 图标
    )
except:
    st.set_page_config(layout="wide", page_title="花大爷 & 不差儿", page_icon="🎨")

# 🎨 移动端强制 1:1 对垒 CSS
st.markdown("""
    <style>
    .stApp { background-color: #F0F9F9; }
    :root { --tiffany-blue: #0ABAB5; --deep-teal: #088F8A; }
    
    /* 强制手机端列不折叠 (Key Move) */
    @media (max-width: 640px) {
        [data-testid="column"] {
            width: 49% !important;
            flex: 1 1 49% !important;
            min-width: 49% !important;
        }
        /* 缩小手机端 Metric 文字防止溢出 */
        .stMetricValue { font-size: 1.2rem !important; }
        .stMetricDelta { font-size: 0.8rem !important; }
        h2 { font-size: 1.1rem !important; }
    }

    /* 蒂芙尼蓝流线型卡片设计 */
    .main-card { 
        background: white; 
        padding: 15px; 
        border-radius: 25px; 
        border-top: 5px solid var(--tiffany-blue); 
        box-shadow: 0 4px 10px rgba(0,0,0,0.05); 
        margin-bottom: 15px; 
    }
    
    .header-style { color: var(--deep-teal); font-weight: bold; margin-bottom: 10px; }
    div[data-testid="stMetricValue"] { color: var(--tiffany-blue) !important; font-size: 1.6rem !important; }
    
    /* 按钮圆角适配 */
    .stButton>button { 
        background-color: var(--tiffany-blue); 
        color: white; 
        border-radius: 15px; 
        border: none;
    }
    .stButton>button:hover { background-color: var(--deep-teal); }
    </style>
    """, unsafe_allow_html=True)

# 🔑 钥匙配置 (请务必填入你的真实数据)
SUPABASE_URL = "https://hjrvdusefkjtmucsreeq.supabase.co"
SUPABASE_KEY = "sb_publishable_yDO1V8a3qYz8YPSzXSHdWA_mhpQG8QF"

# --- 2. 核心功能函数 ---
def call_supabase(method, data=None, query=""):
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
    url = f"{SUPABASE_URL}/rest/v1/diet_records{query}"
    try:
        with httpx.Client() as client:
            if method == "POST": return client.post(url, json=data, headers=headers)
            # 默认按时间倒序拿数据
            return client.get(f"{url}{query}", headers=headers)
    except: return None

# --- 3. 登录与基础信息录入 (防 KeyReset) ---
if 'user_role' not in st.session_state:
    with st.form("login_form"):
        st.markdown("<h3 style='text-align:center; color:#0ABAB5;'>🎨 开启双人对垒之旅</h3>", unsafe_allow_html=True)
        role = st.selectbox("👤 你是谁？", ["花大爷", "不差儿"])
        c1, c2 = st.columns(2)
        age = c1.number_input("🎂 年龄", value=25)
        height = c2.number_input("📏 身高 (cm)", value=170.0)
        gender = c3 = st.selectbox("🚻 性别", ["男", "女"])
        if st.form_submit_button("🚀 进入基地"):
            st.session_state.user_role = role
            # 计算建议卡路里和基代 (基于 Mifflin-St Jeor 公式)
            s_cal = (10 * 60 + 6.25 * height - 5 * age - 161) * 1.3
            st.session_state.base_info = {"age": age, "height": height, "gender": gender, "s_cal": s_cal}
            st.rerun()
    st.stop() # 未登录则停止执行

# --- 4. 数据预加载与状态栏 (彻底解决 KeyError) ---
all_res = call_supabase("GET", query="?order=created_at.desc")
full_db = pd.DataFrame(all_res.json()) if all_res and all_res.status_code == 200 else pd.DataFrame()

# 计算打卡天数
def get_days(name):
    if full_db.empty: return 0
    # 这里的 user_dates =pd.to_datetime(full_db[full_db['user_name'] == name]['created_at']).dt.date
    # pd.DataFrame(all_res.json()) 需要列名检查
    if 'user_name' not in full_db.columns: return 0
    u_dates = pd.to_datetime(full_db[full_db['user_name'] == name]['created_at']).dt.date
    return u_dates.nunique()

# 顶部日历回顾与状态
st.markdown("<div class='main-card'>", unsafe_allow_html=True)
ca1, ca2, ca3 = st.columns([1, 2, 1])
with ca1:
    view_date = st.date_input("📅 历史回顾", date.today())
with ca2:
    st.markdown(f"""
        <div style='text-align:center;'>
        <h3 style='color:#0ABAB5; margin:0;'>{view_date} 战况</h3>
        <p style='color:grey; font-size:0.8rem;'>📍 当前位置：自动云端同步中 | 🌤️ 天气：舒适 22°C</p>
        </div>
    """, unsafe_allow_html=True)
with ca3:
    st.markdown(f"""
        <div style='text-align:right;'>
        <span style='color:#0ABAB5;'><b>{st.session_state.user_role}</b></span><br>打卡 {get_days(st.session_state.user_role)} 天
        </div>
    """, unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# 筛选日期数据
query_str = f"?created_at=gte.{view_date}T00:00:00&created_at=lt.{view_date + timedelta(days=1)}T00:00:00&order=created_at.desc"
res = call_supabase("GET", query=query_str)
day_db = pd.DataFrame(res.json()) if res and res.status_code == 200 else pd.DataFrame()

# --- 5. 左右镜像对垒区：强制不折叠 ---
col_left, col_right = st.columns(2)

def render_side(user_name, column, is_me):
    with column:
        avatar = "👨‍🦳" if user_name == "花大爷" else "👩‍𝓠"
        st.markdown(f"<div style='text-align:center;'><h2 class='header-style'>{avatar} {user_name} {'(我)' if is_me else ''}</h2></div>", unsafe_allow_html=True)
        
        u_data = day_db[day_db['user_name'] == user_name] if not day_db.empty else pd.DataFrame()
        latest = u_data.iloc[0] if not u_data.empty else None

        # 1. 身体指标记录 (Metric 缩小适配手机)
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        st.write("📊 **身体指标**")
        m1, m2 = st.columns(2)
        m1.metric("体重", f"{latest['weight'] if latest is not None else 0} kg")
        m2.metric("身高", f"{latest['height'] if latest is not None else 170} cm")
        
        # 录入区 (仅限本人且放在 expander 里)
        if is_me:
            with st.expander("📝 今日指标录入", expanded=False):
                with st.form(f"f_i_{user_name}"):
                    w = st.number_input("体重 (kg)", value=60.0, step=0.1)
                    h = st.number_input("身高 (cm)", value=170.0)
                    if st.form_submit_button("💾 保存数据"):
                        call_supabase("POST", {"user_name":user_name, "weight":w, "height":h, "bmi":w/(h/100)**2, "created_at":datetime.now().isoformat()})
                        st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # 2. 饮食卡路里 (已叠加)
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        in_cal = u_data['in_calories'].sum() if not u_data.empty else 0
        water = u_data['water'].sum() if not u_data.empty else 0
        s_cal = st.session_state.base_info['s_cal']
        
        c1, c2 = st.columns(2)
        c1.metric("建议摄入", f"{s_cal:.0f} kcal")
        c2.metric("已摄入", f"{in_cal} kcal", delta=f"{in_cal-s_cal:.0f}")
        
        # 录入区
        if is_me:
            with st.expander("🍱 传照片算热量", expanded=False):
                with st.form(f"f_d_{user_name}"):
                    wat_in = st.number_input("饮水 (ml)", value=0, step=100)
                    st.file_uploader("📸 餐点图片", type=['jpg','png'], key=f"d_up_{user_name}")
                    if st.form_submit_button("🚀 AI识别并同步"):
                        # 模拟 AI 分析结果
                        call_supabase("POST", {"user_name":user_name, "water":wat_in, "in_calories": 450, "created_at":datetime.now().isoformat()})
                        st.balloons()
                        st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # 3. 健身与消耗
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        # 基代 BMR
        bmr = s_cal # Mifflin-St Jeor 基础
        sport_cal = u_data['out_calories'].sum() if not u_data.empty else 0
        st.write(f"基础代谢: **{bmr:.0f} kcal**")
        st.write(f"今日运动: **{sport_cal} kcal**")
        st.write(f"🔥 总消耗: **{bmr + sport_cal:.0f} kcal**")
        st.markdown("</div>", unsafe_allow_html=True)

        # 4. 健康心得 (独立模块)
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        note_val = latest['message_to_partner'] if latest is not None else ""
        if note_val: st.info(note_val)
        
        if is_me:
            with st.form(f"f_n_{user_name}"):
                note = st.text_input("给TA留言...", placeholder="表情包/文字")
                if st.form_submit_button("发布"):
                    call_supabase("POST", {"user_name":user_name, "message_to_partner":note, "created_at":datetime.now().isoformat()})
                    st.toast("心得已同步！")
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# 执行渲染：不差儿在左，花大爷在右
render_side("不差儿", col_left, is_me=(st.session_state.user_role == "不差儿"))
render_side("花大爷", col_right, is_me=(st.session_state.user_role == "花大爷"))
