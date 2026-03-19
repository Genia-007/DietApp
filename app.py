import streamlit as st
from supabase import create_client, Client

# --- 1. 强制配置 ---
st.set_page_config(page_title="花大爷 × 不差儿", layout="wide")

# --- 2. 这里的 URL 和 KEY 请确保填入你之前给我的那串 service_role ---
# 注意：直接写死字符串，不走 st.secrets
URL = "https://hjrvdusefkjtmucsreeq.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhqcnZkdXNlZmtqdG11Y3NyZWVxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3Mzg0MzM2MiwiZXhwIjoyMDg5NDE5MzYyfQ.n7TPfrBJYeo9ZKIIEoOEPIRscmR2joGqHwqNw5-Yqsk"

supabase: Client = create_client(URL, KEY)

# --- 3. 强制并排 CSS (修复你说的手机显示问题) ---
st.markdown("""
    <style>
    /* 核心：强制手机端列宽为 50% */
    [data-testid="column"] {
        width: 50% !important;
        flex: 1 1 50% !important;
        min-width: 50% !important;
    }
    .stMetric { background: white; padding: 10px; border-radius: 10px; border-top: 3px solid #0ABAB5; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. 登录逻辑 ---
if 'user_role' not in st.session_state:
    with st.form("login"):
        st.subheader("🎨 开启双人基地")
        role = st.selectbox("👤 你是谁？", ["不差儿", "花大爷"])
        if st.form_submit_button("🚀 进入系统"):
            try:
                # 哪怕数据库报错，我们也强行进入，不让用户卡住
                supabase.table("users").upsert({"name": role, "gender": "女"}).execute()
            except:
                st.warning("数据库连接有点小脾气，但咱们先进入再说！")
            
            st.session_state.user_role = role
            st.rerun()
    st.stop()

# --- 5. 双列并排界面 ---
st.success(f"🎊 欢迎进入基地：{st.session_state.user_role}")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 👩‍𝓠 不差儿")
    st.metric("今日体重", "60.0 kg")
    st.info("留言内容会显示在这里")

with col2:
    st.markdown("### 👨‍🦳 花大爷")
    st.metric("今日体重", "75.0 kg")
    st.info("留言内容会显示在这里")

if st.button("退出登录"):
    del st.session_state.user_role
    st.rerun()
