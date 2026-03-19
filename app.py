import streamlit as st
from supabase import create_client, Client

# 1. 基础配置
st.set_page_config(page_title="花大爷 × 不差儿", layout="wide")

# 2. 从 Secrets 读取配置 (确保你的 Secrets 填的是 service_role 那把长钥匙)
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("❌ 钥匙读取失败，请检查 Streamlit 后台 Secrets 设置")
    st.stop()

# 3. 登录逻辑
if 'user_role' not in st.session_state:
    with st.form("login_form"):
        st.subheader("🎨 开启双人打卡基地")
        role = st.selectbox("👤 你是谁？", ["不差儿", "花大爷"])
        age = st.number_input("年龄", 1, 100, 24)
        h = st.number_input("身高(cm)", 100, 250, 163)
        w = st.number_input("初始体重(kg)", 30.0, 200.0, 61.5)
        
        if st.form_submit_button("🚀 进入系统"):
            try:
                # 构造数据
                user_data = {
                    "name": role, 
                    "age": int(age), 
                    "height": int(h), 
                    "weight": float(w), 
                    "gender": "女"
                }
                
                # 核心修复：最稳健的 upsert 写法
                # 因为 name 是主键，Supabase 会自动处理冲突
                supabase.table("users").upsert(user_data).execute()
                
                st.session_state.user_role = role
                st.rerun()
            except Exception as e:
                # 如果还报错，这里会显示具体的数据库反馈
                st.error(f"❌ 数据库写入异常: {e}")
    st.stop()

# 4. 进入系统后的界面
st.balloons() 
st.success(f"🎊 欢迎进入基地，{st.session_state.user_role}！")
st.info("数据已成功同步至 Supabase 数据库。")

if st.button("退出登录"):
    del st.session_state.user_role
    st.rerun()
