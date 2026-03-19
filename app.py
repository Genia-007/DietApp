import streamlit as st
import requests
from datetime import date, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# --- 配置 ---
API_URL = "http://localhost:8000"
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# --- 认证 ---
def login():
    st.sidebar.title("登录")
    username = st.sidebar.text_input("用户名")
    password = st.sidebar.text_input("密码", type="password")
    if st.sidebar.button("登录"):
        response = requests.post(f"{API_URL}/token", data={"username": username, "password": password})
        if response.status_code == 200:
            token = response.json()["access_token"]
            st.session_state.token = token
            st.session_state.username = username
            st.sidebar.success("登录成功！")
        else:
            st.sidebar.error("登录失败，请检查用户名和密码")

def logout():
    if 'token' in st.session_state:
        del st.session_state.token
        del st.session_state.username
        st.rerun()

# --- API 调用 ---
def get_logs(user_id, start_date, end_date):
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    response = requests.get(f"{API_URL}/logs/{user_id}?start_date={start_date}&end_date={end_date}", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("获取数据失败")
        return []

def create_log(user_id, log_data):
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    response = requests.post(f"{API_URL}/logs", json=log_data, headers=headers)
    if response.status_code == 202:
        st.success("数据已提交")
    else:
        st.error("提交失败")

# --- AI 分析 ---
def analyze_with_ai(data):
    if not DEEPSEEK_API_KEY:
        st.warning("未配置 DeepSeek API 密钥")
        return "请设置 DEEPSEEK_API_KEY 环境变量"
    
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {DEEPSEEK_API_KEY}"}
    payload = {
        "model": "deepseek-v3.5",
        "messages": [
            {"role": "system", "content": "你是一位专业的健身教练。你需要根据用户的健康数据，提供个性化的减肥建议和鼓励。"},
            {"role": "user", "content": f"分析以下健康数据并提供建议：{data}"}
        ],
        "temperature": 0.7
    }
    try:
        response = requests.post("https://api.deepseek.com/chat", json=payload, headers=headers)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        st.error(f"AI 分析失败: {e}")
        return "AI 分析失败，请手动输入"

# --- 主界面 ---
def main():
    st.set_page_config(page_title="双人健康追踪", layout="wide")
    st.title("💪 夫妻健康追踪应用")

    if 'token' not in st.session_state:
        login()
        st.stop()

    user1_id = st.session_state.username
    user2_id = "meimei"  # 假设固定为伴侣

    # 布局
    col1, col2 = st.columns(2)
    with col1:
        st.subheader(f"{user1_id} 的数据")
        user1_data = get_logs(user1_id, date.today() - timedelta(days=30), date.today())
        user1_df = pd.DataFrame(user1_data)
        if not user1_df.empty:
            st.line_chart(user1_df.set_index('log_date')['weight'])
        else:
            st.info("暂无数据")

    with col2:
        st.subheader(f"{user2_id} 的数据")
        user2_data = get_logs(user2_id, date.today() - timedelta(days=30), date.today())
        user2_df = pd.DataFrame(user2_data)
        if not user2_df.empty:
            st.line_chart(user2_df.set_index('log_date')['weight'])
        else:
            st.info("暂无数据")

    # 数据输入
    st.header("📊 记录今日数据")
    col1, col2 = st.columns(2)
    with col1:
        weight = st.number_input(f"{user1_id} 体重 (kg)", min_value=30.0, max_value=300.0, step=0.1)
        body_fat = st.number_input(f"{user1_id} 体脂率 (%)", min_value=0.0, max_value=100.0, step=0.1)
        chest = st.number_input(f"{user1_id} 胸围 (cm)", min_value=0.0, max_value=200.0, step=0.1)
        waist = st.number_input(f"{user1_id} 腰围 (cm)", min_value=0.0, max_value=200.0, step=0.1)
        hip = st.number_input(f"{user1_id} 臀围 (cm)", min_value=0.0, max_value=200.0, step=0.1)
        thigh = st.number_input(f"{user1_id} 大腿围 (cm)", min_value=0.0, max_value=100.0, step=0.1)
        calf = st.number_input(f"{user1_id} 小腿围 (cm)", min_value=0.0, max_value=100.0, step=0.1)
        arm = st.number_input(f"{user1_id} 手臂围 (cm)", min_value=0.0, max_value=100.0, step=0.1)
        notes = st.text_area(f"{user1_id} 备注")

    with col2:
        weight2 = st.number_input(f"{user2_id} 体重 (kg)", min_value=30.0, max_value=300.0, step=0.1)
        body_fat2 = st.number_input(f"{user2_id} 体脂率 (%)", min_value=0.0, max_value=100.0, step=0.1)
        chest2 = st.number_input(f"{user2_id} 胸围 (cm)", min_value=0.0, max_value=200.0, step=0.1)
        waist2 = st.number_input(f"{user2_id} 腰围 (cm)", min_value=0.0, max_value=200.0, step=0.1)
        hip2 = st.number_input(f"{user2_id} 臀围 (cm)", min_value=0.0, max_value=200.0, step=0.1)
        thigh2 = st.number_input(f"{user2_id} 大腿围 (cm)", min_value=0.0, max_value=100.0, step=0.1)
        calf2 = st.number_input(f"{user2_id} 小腿围 (cm)", min_value=0.0, max_value=100.0, step=0.1)
        arm2 = st.number_input(f"{user2_id} 手臂围 (cm)", min_value=0.0, max_value=100.0, step=0.1)
        notes2 = st.text_area(f"{user2_id} 备注")

    if st.button("保存数据"):
        log1 = {
            "user_id": user1_id,
            "log_date": date.today().isoformat(),
            "weight": weight,
            "body_fat_rate": body_fat,
            "chest": chest,
            "waist": waist,
            "hip": hip,
            "thigh": thigh,
            "calf": calf,
            "arm": arm,
            "notes": notes
        }
        log2 = {
            "user_id": user2_id,
            "log_date": date.today().isoformat(),
            "weight": weight2,
            "body_fat_rate": body_fat2,
            "chest": chest2,
            "waist": waist2,
            "hip": hip2,
            "thigh": thigh2,
            "calf": calf2,
            "arm": arm2,
            "notes": notes2
        }
        create_log(user1_id, log1)
        create_log(user2_id, log2)
        st.rerun()

    # AI 分析
    st.header("🤖 AI 健身教练")
    if st.button("分析今日数据"):
        data_to_analyze = f"{user1_id}: {weight}kg, {body_fat}%, {chest}cm, {waist}cm, {hip}cm, {thigh}cm, {calf}cm, {arm}cm. {notes}. " \
                          f"{user2_id}: {weight2}kg, {body_fat2}%, {chest2}cm, {waist2}cm, {hip2}cm, {thigh2}cm, {calf2}cm, {arm2}cm. {notes2}."
        with st.spinner("正在分析..."):
            analysis = analyze_with_ai(data_to_analyze)
        st.write(analysis)

    if st.button("登出"):
        logout()

if __name__ == "__main__":
    main()
