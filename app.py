import streamlit as st
import pandas as pd
import httpx
from datetime import datetime, date, timedelta
import base64

# --- 1. 图标强制嵌入 (使用合照图片) ---
def get_base64_img(file_path):
    try:
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except: return None

img_base64 = get_base64_img("6af1af85193fb5400cc2503413532cbe.jpg")
if img_base64:
    st.set_page_config(layout="wide", page_title="花大爷 & 不差儿", page_icon=f"data:image/jpeg;base64,{img_base64}")
else:
    st.set_page_config(layout="wide", page_title="花大爷 & 不差儿", page_icon="🎨")

# --- 2. 手机端强制并排与样式优化 ---
st.markdown("""
    <style>
    .stApp { background-color: #F0F9F9; }
    :root { --tiffany-blue: #0ABAB5; }
    
    /* 强制手机端列不折叠 */
    [data-testid="column"] {
        width: 50% !important;
        flex: 1 1 50% !important;
        min-width: 50% !important;
    }
    
    @media (max-width: 640px) {
        .main-card { padding: 10px !important; border-radius: 15px !important; margin-bottom: 8px !important; }
        h2 { font-size: 1rem !important; }
        .stMetricValue { font-size: 1.1rem !important; }
        label { font-size: 0.8rem !important; }
    }

    .main-card { 
        background: white; padding: 20px; border-radius: 25px; 
        border-top: 5px solid var(--tiffany-blue); 
        box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 15px; 
    }
    .stButton>button { background-color: var(--tiffany-blue); color: white; border-radius: 12px; width: 100%; border: none; }
    </style>
    """, unsafe_allow_html=True)

# 🔑 钥匙配置
SUPABASE_URL = "https://hjrvdusefkjtmucsreeq.supabase.co"
SUPABASE_KEY = "sb_publishable_yDO1V8a3qYz8YPSzXSHdWA_mhpQG8QF"

# --- 3. 登录逻辑 (按要求设置默认值) ---
if 'user_role' not in st.session_state:
    with st.form("login"):
        st.markdown("<h3 style='text-align:center; color:#0ABAB5;'>🎨 开启双人打卡基地</h3>", unsafe_allow_html=True)
        role = st.selectbox("👤 选择身份", ["不差儿", "花大爷"])
        c1, c2, c3 = st.columns(3)
        # 年龄默认24，身高整数显示
        age = c1.number_input("🎂 年龄", value=24, step=1)
        height = c2.number_input("📏 身高 (厘米)", value=165, step=1)
        gender = c3.selectbox("🚻 性别", ["女", "男"], index=0) # 默认女
        
        if st.form_submit_button("🚀 进入基地"):
            st.session_state.user_role = role
            st.session_state.user_params = {"age": age, "height": height, "gender": gender}
            st.rerun()
    st.stop()

# --- 4. 数据读取 ---
def call_db(method, data=None, query=""):
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
    url = f"{SUPABASE_URL}/rest/v1/diet_records{query}"
    try:
        with httpx.Client() as client:
            if method == "POST": return client.post(url, json=data, headers=headers)
            return client.get(url, headers=headers)
    except: return None

all_res = call_db("GET", "?order=created_at.desc")
full_db = pd.DataFrame(all_res.json()) if all_res and all_res.status_code == 200 else pd.DataFrame()

# 顶部状态
st.markdown(f"<div class='main-card' style='text-align:center;'>📅 {date.today()} | 🦾 已打卡 {full_db[full_db['user_name']==st.session_state.user_role].shape[0] if not full_db.empty else 0} 天</div>", unsafe_allow_html=True)

# --- 5. 左右对垒渲染 ---
col_left, col_right = st.columns(2)

def render_side(name, col, is_me):
    with col:
        st.markdown(f"<div style='text-align:center;'><h2>{'👩‍𝓠' if name=='不差儿' else '👨‍🦳'} {name}</h2></div>", unsafe_allow_html=True)
        
        u_data = full_db[full_db['user_name'] == name] if not full_db.empty and 'user_name' in full_db.columns else pd.DataFrame()
        latest = u_data.iloc[0] if not u_data.empty else None

        # 身体指标卡片 (身高体重设为整数)
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        st.write("📊 **身体指标**")
        m1, m2 = st.columns(2)
        m1.metric("体重", f"{int(latest['weight']) if latest is not None else '--'}kg")
        m2.metric("身高", f"{int(latest['height']) if latest is not None else '--'}cm")
        
        if is_me:
            with st.expander("📝 录入", expanded=False):
                with st.form(f"form_{name}"):
                    new_w = st.number_input("体重(kg)", value=60, step=1)
                    new_h = st.number_input("身高(cm)", value=st.session_state.user_params['height'], step=1)
                    note = st.text_input("想说的话...")
                    if st.form_submit_button("保存同步"):
                        payload = {
                            "user_name": name, 
                            "weight": new_w, 
                            "height": new_h, 
                            "message_to_partner": note,
                            "created_at": datetime.now().isoformat()
                        }
                        call_db("POST", data=payload)
                        st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
        # 对方的心得展示
        if not is_me and latest is not None and latest['message_to_partner']:
            st.info(f"💬 {latest['message_to_partner']}")

# 强制布局：左不差儿，右花大爷
render_side("不差儿", col_left, is_me=(st.session_state.user_role == "不差儿"))
render_side("花大爷", col_right, is_me=(st.session_state.user_role == "花大爷"))
