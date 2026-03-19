import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, date, timedelta
import random
import os
import base64
from PIL import Image

# --- 1. 页面配置与合照图标强制加载 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(current_dir, "app_icon.png")

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

try:
    if os.path.exists(icon_path):
        img_b64 = get_base64_of_bin_file(icon_path)
        
        # [修改1] 强行注入 HTML Head，解决添加到主屏幕显示原始 Logo 问题
        st.markdown(f"""
            <head>
                <link rel="apple-touch-icon" href="data:image/png;base64,{img_b64}">
                <link rel="apple-touch-icon-precomposed" href="data:image/png;base64,{img_b64}">
                <meta name="apple-mobile-web-app-capable" content="yes">
                <title>花大爷 × 不差儿</title>
            </head>
            """, unsafe_allow_html=True)

        # 这里保持浏览器标签页的图标
        st.set_page_config(
            page_title="花大爷 × 不差儿",
            page_icon=Image.open(icon_path),
            layout="wide"
        )
    else:
        st.set_page_config(page_title="花大爷 × 不差儿", page_icon="🎨", layout="wide")
except:
    st.set_page_config(page_title="花大爷 × 不差儿", layout="wide")

# --- 2. 蒂芙尼蓝 UI & 移动端强制并排 & 强制黑字 CSS ---
st.markdown("""
    <style>
    /* [修改2] 强制全局文字为黑色，防止深色模式导致字变成白色看不清 */
    html, body, [data-testid="stMarkdownContainer"], .stApp, .stMetric, span, p, h1, h2, h3, label {
        color: #000000 !important;
    }

    .stApp { background-color: #F0F9F9; }
    
    /* [修改3] 核心 CSS：强制手机端列不折叠，保持 50/50 比例 */
    [data-testid="column"] {
        width: 50% !important;
        flex: 1 1 50% !important;
        min-width: 50% !important;
        padding: 5px !important;
    }
    
    /* 卡片式布局，增加文字颜色锁定 */
    .main-card {
        background: white; border-radius: 20px; padding: 15px;
        border-top: 5px solid #0ABAB5;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        margin-bottom: 15px;
        color: #000000 !important; /* 锁定卡片内文字黑色 */
    }
    .stButton>button { background-color: #0ABAB5; color: white; border-radius: 12px; width: 100%; border: none; font-weight: bold; }
    h3 { color: #088F8A; font-size: 1.1rem !important; margin-bottom: 10px !important; }
    .stMetricValue { font-size: 1.2rem !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 初始化 Supabase ---
# 请检查你的 Secrets 中是否已填好 URL 和 KEY
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error(f"Supabase 连接失败: {e}")
    st.stop()

# --- 4. 身份判定逻辑 ---
if 'user_role' not in st.session_state:
    if os.path.exists(icon_path):
        st.image(Image.open(icon_path), width=120)
    with st.form("login"):
        st.markdown("<h3 style='text-align:center;'>🎨 开启双人打卡基地</h3>", unsafe_allow_html=True)
        role = st.selectbox("👤 你是谁？", ["不差儿", "花大爷"])
        age = st.number_input("年龄", 1, 100, 24)
        h = st.number_input("身高(cm)", 100, 250, 163)
        w = st.number_input("初始体重(kg)", 30.0, 200.0, 61.5)
        if st.form_submit_button("🚀 进入系统"):
            # 存入资料
            try:
                supabase.table("users").upsert({
                    "name": role, "age": age, "height": h, "weight": w, "gender": "女"
                }, on_conflict="name").execute()
                st.session_state.user_role = role
                st.rerun()
            except Exception as e:
                st.error(f"保存资料失败: {e}")
    st.stop()

# --- 5. 首页展示内容 ---
my_role = st.session_state.user_role
other_role = "不差儿" if my_role == "花大爷" else "花大爷"
view_date = st.date_input("📅 查看日期", date.today())

# 左右对垒 (强制 CSS 已经应用于 data-testid="column")
col_left, col_right = st.columns(2)

def render_column(name, col, is_editable):
    # 尝试从数据库读取数据
    try:
        user_res = supabase.table("users").select("*").eq("name", name).execute()
        user_base = user_res.data[0] if user_res.data else None
        
        log_res = supabase.table("daily_logs").select("*").eq("user_name", name).eq("log_date", str(view_date)).execute()
        log_data = log_res.data[0] if log_res.data else {}
    except:
        user_base, log_data = None, {}

    with col:
        st.markdown(f"<div style='text-align:center;'><h3>{'👩‍𝓠' if name=='不差儿' else '👨‍🦳'} {name}</h3></div>", unsafe_allow_html=True)
        
        if not user_base:
            st.info(f"等待 {name} 初始化...")
            return

        # 身体指标卡
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        st.metric("今日体重", f"{log_data.get('weight', user_base['weight'])} kg")
        
        # BMI 计算
        curr_w = float(log_data.get('weight', user_base['weight']))
        height_m = user_base['height'] / 100
        bmi = round(curr_w / (height_m * height_m), 1)
        st.metric("BMI", bmi)

        if is_editable:
            with st.expander("📝 录入"):
                nw = st.number_input("当前体重", value=curr_w, key=f"w_{name}")
                if st.button("更新", key=f"b_{name}"):
                    supabase.table("daily_logs").upsert({
                        "user_name": name, "log_date": str(view_date), "weight": nw
                    }, on_conflict="user_name,log_date").execute()
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # 饮食卡
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        st.write(f"🍎 已摄入: {log_data.get('calories_in', 0)} kcal")
        st.markdown("</div>", unsafe_allow_html=True)

# 渲染左右分栏 (强制并排 CSS 生效)
render_column(other_role, col_left, False)
render_column(my_role, col_right, True)

if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()
