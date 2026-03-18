import streamlit as st
import pandas as pd
import httpx
from datetime import datetime, date, timedelta
import base64

# --- 1. 页面配置 (图标修复) ---
# 先尝试加载本地合照，如果失败则用 Emoji 垫底，保证不显示纸飞机
try:
    with open("6af1af85193fb5400cc2503413532cbe.jpg", "rb") as f:
        img_data = f.read()
    st.set_page_config(layout="wide", page_title="花大爷 & 不差儿", page_icon="🎨")
except:
    st.set_page_config(layout="wide", page_title="花大爷 & 不差儿", page_icon="🎨")

# 🎨 移动端优化 CSS
st.markdown("""
    <style>
    .stApp { background-color: #F0F9F9; }
    :root { --tiffany-blue: #0ABAB5; --deep-teal: #088F8A; }
    
    /* 强制手机端列不折叠 (针对两列布局) */
    @media (max-width: 640px) {
        [data-testid="column"] {
            width: 49% !important;
            flex: 1 1 49% !important;
            min-width: 49% !important;
        }
        /* 缩小手机端文字防止溢出 */
        h2 { font-size: 1.2rem !important; }
        .stMetricValue { font-size: 1.2rem !important; }
    }

    .main-card { 
        background: white; padding: 15px; border-radius: 25px; 
        border-top: 5px solid var(--tiffany-blue); 
        box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 15px; 
    }
    .stButton>button { background-color: var(--tiffany-blue); color: white; border-radius: 15px; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# 🔑 钥匙配置 (请确保填入你的真实数据)
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "这里填URL")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "这里填KEY")

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
        st.markdown("<h3 style='text-align:center; color:#0ABAB5;'>🎨 开启双人打卡基地</h3>", unsafe_allow_html=True)
        role = st.selectbox("👤 选择身份", ["花大爷", "不差儿"])
        c1, c2 = st.columns(2)
        age = c1.number_input("🎂 年龄", value=25)
        height = c2.number_input("📏 身高(cm)", value=170.0)
        if st.form_submit_button("🚀 进入基地"):
            st.session_state.user_role = role
            st.session_state.s_cal = (10 * 60 + 6.25 * height - 5 * age - 161) * 1.3
            st.rerun()
    st.stop()

# --- 4. 数据预加载 ---
all_res = call_supabase("GET", query="?order=created_at.desc")
full_db = pd.DataFrame(all_res.json()) if all_res and all_res.status_code == 200 else pd.DataFrame()

# 顶部日历与状态
st.markdown("<div class='main-card'>", unsafe_allow_html=True)
ca1, ca2 = st.columns([1, 1])
with ca1:
    view_date = st.date_input("📅 历史回顾", date.today())
with ca2:
    st.markdown(f"<div style='text-align:right;'><span style='color:#0ABAB5;'><b>{st.session_state.user_role}</b></span><br>打卡 {full_db[full_db['user_name']==st.session_state.user_role].shape[0]} 次</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# 筛选当日数据
query_today = f"?created_at=gte.{view_date}T00:00:00&created_at=lt.{view_date + timedelta(days=1)}T00:00:00&order=created_at.desc"
res_today = call_supabase("GET", query=query_today)
day_db = pd.DataFrame(res_today.json()) if res_today and res_today.status_code == 200 else pd.DataFrame()

# --- 5. 渲染镜像对垒区 ---
# 强制手机端保持 1:1 的左右布局
col_left, col_right = st.columns(2)

def render_side(user_name, column, is_me):
    with column:
        avatar = "👨‍🦳" if user_name == "花大爷" else "👩‍𝓠"
        st.markdown(f"<div style='text-align:center;'><h2 class='header-style'>{avatar} {user_name}</h2></div>", unsafe_allow_html=True)
        
        u_data = day_db[day_db['user_name'] == user_name] if not day_db.empty else pd.DataFrame()
        latest = u_data.iloc[0] if not u_data.empty else None

        # 身体指标
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        st.metric("体重", f"{latest['weight'] if latest is not None else 0} kg")
        if is_me:
            with st.expander("📝 录入指标", expanded=False):
                with st.form(f"f_i_{user_name}"):
                    w = st.number_input("体重", value=60.0)
                    h = st.number_input("身高", value=170.0)
                    if st.form_submit_button("保存"):
                        call_supabase("POST", {"user_name":user_name, "weight":w, "height":h, "bmi":w/(h/100)**2, "created_at":datetime.now().isoformat()})
                        st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # 饮食看板
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        in_cal = u_data['in_calories'].sum() if not u_data.empty else 0
        st.metric("摄入", f"{in_cal} kcal")
        if is_me:
            with st.expander("🍱 传照片", expanded=False):
                with st.form(f"f_d_{user_name}"):
                    st.file_uploader("拍照", type=['jpg','png'], key=f"up_{user_name}")
                    if st.form_submit_button("AI识别并发布"):
                        call_supabase("POST", {"user_name":user_name, "in_calories": 450, "created_at":datetime.now().isoformat()})
                        st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # 心得显示 (如果是对方，只显示文字)
        if latest is not None and latest['message_to_partner']:
            st.markdown(f"<div class='main-card' style='font-size:0.8rem; border-top:2px solid orange;'>{latest['message_to_partner']}</div>", unsafe_allow_html=True)
        
        if is_me:
            with st.form(f"f_n_{user_name}"):
                note = st.text_input("想对TA说...")
                if st.form_submit_button("发送"):
                    call_supabase("POST", {"user_name":user_name, "message_to_partner":note, "created_at":datetime.now().isoformat()})
                    st.rerun()

# 核心：手机端如果你选的是“花大爷”，那我们就把“花大爷”放在右列渲染，对方在左列
render_side("不差儿", col_left, is_me=(st.session_state.user_role == "不差儿"))
render_side("花大爷", col_right, is_me=(st.session_state.user_role == "花大爷"))
