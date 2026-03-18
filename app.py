import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, date, timedelta
import os
import base64
from PIL import Image

# --- 1. 页面与图标配置 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(current_dir, "app_icon.png")

def get_base64_img(bin_file):
    with open(bin_file, 'rb') as f:
        return base64.b64encode(f.read()).decode()

try:
    if os.path.exists(icon_path):
        img_b = get_base64_img(icon_path)
        st.set_page_config(page_title="花大爷 × 不差儿", page_icon=f"data:image/png;base64,{img_b}", layout="wide")
    else:
        st.set_page_config(page_title="花大爷 × 不差儿", page_icon="🎨", layout="wide")
except:
    st.set_page_config(page_title="花大爷 × 不差儿", layout="wide")

# --- 2. Supabase 连接代码 ---
SUPABASE_URL = "https://hjrvdusefkjtmucsreeq.supabase.co"
SUPABASE_KEY = "sb_publishable_yDO1V8a3qYz8YPSzXSHdWA_mhpQG8QF"

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"数据库连接失败: {e}")
    st.stop()

# --- 3. 核心数据写入函数 (带异常处理) ---

def insert_user(data):
    """插入或更新用户基础资料"""
    try:
        # 使用 upsert 保证重复登录时更新数据而非报错
        res = supabase.table("users").upsert(data, on_conflict="name").execute()
        return res
    except Exception as e:
        st.error(f"保存用户信息失败: {e}")
        return None

def save_daily_log(log_data):
    """插入或更新每日打卡记录"""
    try:
        res = supabase.table("daily_logs").upsert(log_data, on_conflict="user_name,date").execute()
        return res
    except Exception as e:
        st.error(f"保存打卡数据失败: {e}")
        return None

# --- 4. 登录初始化逻辑 ---
if 'user_role' not in st.session_state:
    if os.path.exists(icon_path):
        st.image(Image.open(icon_path), width=100)
    
    with st.form("login_gate"):
        st.subheader("🎨 欢迎回来！请初始化身份")
        role = st.selectbox("👤 你是谁？", ["不差儿", "花大爷"])
        u_age = st.number_input("年龄", 1, 100, 24)
        u_height = st.number_input("身高(cm)", 100, 250, 165)
        u_weight = st.number_input("体重(kg)", 30.0, 200.0, 60.0)
        
        if st.form_submit_button("🚀 进入系统"):
            user_payload = {
                "name": role,
                "age": u_age,
                "height": u_height,
                "weight": u_weight,
                "gender": "女"
            }
            # 调用写入函数
            success = insert_user(user_payload)
            if success:
                st.session_state.user_role = role
                st.rerun()

    st.stop()

# --- 5. 首页对垒展示 ---
role_me = st.session_state.user_role
view_date = st.date_input("📅 选择查看日期", date.today())

st.markdown("---")
col_left, col_right = st.columns(2)

def render_side(name, col, is_me):
    with col:
        st.markdown(f"### {'👩‍𝓠' if name=='不差儿' else '👨‍🦳'} {name}")
        
        # 读取数据异常处理
        try:
            res = supabase.table("daily_logs").select("*").eq("user_name", name).eq("date", str(view_date)).execute()
            day_data = res.data[0] if res.data else {}
        except Exception as e:
            st.error(f"读取 {name} 的数据失败: {e}")
            day_data = {}

        st.metric("今日体重", f"{day_data.get('weight', '--')} kg")
        
        if is_me:
            with st.expander("📝 录入今日数据"):
                nw = st.number_input("体重 (kg)", value=60.0, key=f"in_w_{name}")
                note = st.text_input("想对TA说...", key=f"in_n_{name}")
                if st.button("确认同步", key=f"btn_{name}"):
                    log_payload = {
                        "user_name": name,
                        "date": str(view_date),
                        "weight": nw,
                        "note": note
                    }
                    if save_daily_log(log_payload):
                        st.toast("同步成功！🎉")
                        st.rerun()
        else:
            st.info(f"💬 对方想说: {day_data.get('note', 'TA还没说话呢~')}")

# 渲染左右布局
render_side("不差儿", col_left, is_me=(role_me == "不差儿"))
render_side("花大爷", col_right, is_me=(role_me == "花大爷"))
