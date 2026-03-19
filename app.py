# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, date
import random
import os
from PIL import Image

# --- 1. 页面配置与 App 图标修复 (最高优先级) ---
icon_path = "app_icon.png"
try:
    if os.path.exists(icon_path):
        icon_img = Image.open(icon_path)
        st.set_page_config(
            page_title="花大爷 × 不差儿",
            page_icon=icon_img,
            layout="wide", # 必须宽屏模式以支持自适应
            initial_sidebar_state="collapsed"
        )
    else:
        st.set_page_config(page_title="花大爷 × 不差儿", layout="wide")
except:
    st.set_page_config(page_title="花大爷 × 不差儿", layout="wide")

# --- 2. 数据库配置与工具函数 ---
SUPABASE_URL = "https://hjrvdusefkjtmucsreeq.supabase.co"
SUPABASE_KEY = "sb_publishable_yDO1V8a3qYz8YPSzXSHdWA_mhpQG8QF"
TIFFANY_BLUE = "#0ABAB5"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

def safe_float(v, default=0.0):
    """核心安全机制：禁止直接使用 float()"""
    try:
        if v is None or str(v).strip() == "" or str(v).lower() == "none":
            return float(default)
        return float(v)
    except: return float(default)

# --- 3. 手机端布局适配与 UI 样式 (强制禁止横向滚动) ---
st.markdown(f"""
    <style>
    /* 强制自适应宽度与禁止横向滚动 */
    .main {{
        max-width: 100% !important;
        padding: 10px !important;
    }}
    [data-testid="stAppViewContainer"] {{
        overflow-x: hidden !important;
    }}
    
    /* 锁定深色文字 */
    html, body, .stMarkdown, p, span, label, div, .stMetricValue {{
        color: #1A1A1A !important;
        font-family: -apple-system, system-ui, sans-serif !important;
    }}
    
    .stApp {{ background-color: #F8FCFC; }}
    
    /* 卡片式布局 */
    .card {{
        background-color: white; 
        padding: 15px; 
        border-radius: 15px;
        border-top: 5px solid {TIFFANY_BLUE}; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-bottom: 20px;
    }}
    
    /* 按钮与组件适配 */
    .stButton>button {{
        background-color: {TIFFANY_BLUE}; 
        color: white !important;
        border-radius: 10px; 
        font-weight: bold;
        height: 45px;
    }}
    
    /* 区分左右角色的颜色边框 */
    .buchaer-border {{ border-left: 8px solid #FFB6C1; }} /* 浅粉代表左侧不差儿 */
    .huadaye-border {{ border-left: 8px solid {TIFFANY_BLUE}; }} /* 蒂芙尼蓝代表右侧花大爷 */
    
    h3 {{ color: #088F8A !important; margin-bottom: 10px; text-align: center; }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. 身份登录逻辑 ---
if 'user_role' not in st.session_state:
    if os.path.exists(icon_path):
        st.image(icon_path, width=80)
    st.markdown('<div class="card"><h3>👤 确认身份</h3>', unsafe_allow_html=True)
    role = st.radio("选择我是：", ["不差儿", "花大爷"], horizontal=True)
    if st.button("进入基地", use_container_width=True):
        st.session_state.user_role = role
        st.rerun()
    st.stop()

my_name = st.session_state.user_role
other_name = "花大爷" if my_name == "不差儿" else "不差儿"

# --- 5. 初始化判定 ---
try:
    res_me = supabase.table("users").select("*").eq("name", my_name).execute()
    initialized = True if res_me.data and len(res_me.data) > 0 else False
except:
    st.error("数据库连接异常")
    st.stop()

if not initialized:
    st.markdown(f'<div class="card"><h3>🐣 初始化资料 ({my_name})</h3>', unsafe_allow_html=True)
    with st.form("init_form"):
        u_h = st.number_input("身高 (cm)", value=165, step=1)
        u_w = st.number_input("初始体重 (kg)", value=60.0)
        u_a = st.number_input("年龄", value=24, step=1)
        if st.form_submit_button("🚀 完成初始化", use_container_width=True):
            supabase.table("users").upsert({"name": my_name, "height": int(u_h), "weight": safe_float(u_w), "age": int(u_a)}, on_conflict="name").execute()
            st.rerun()
    st.stop()

# --- 6. 数据拉取 ---
try:
    me_data = supabase.table("users").select("*").eq("name", my_name).execute().data[0]
    friend_res = supabase.table("users").select("*").eq("name", other_name).execute()
    friend_data = friend_res.data[0] if friend_res.data else None
except:
    st.error("同步资料失败")
    st.stop()

# --- 7. 顶栏 ---
st.image(icon_path, width=80) if os.path.exists(icon_path) else None
view_date = st.date_input("📅 选择日期", date.today())

# --- 8. 核心渲染函数 (功能 100% 保留) ---
def render_column(name, container, editable, base_info):
    try:
        l_res = supabase.table("daily_logs").select("*").eq("user_name", name).eq("log_date", str(view_date)).execute()
        log = l_res.data[0] if l_res.data else {}
    except: log = {}

    border_class = "buchaer-border" if name == "不差儿" else "huadaye-border"
    
    with container:
        # (1) 身体维度模块
        st.markdown(f'<div class="card {border_class}"><h3>📊 {name} · 身体指标</h3>', unsafe_allow_html=True)
        h = safe_float(base_info.get('height', 165.0))
        w_init = safe_float(base_info.get('weight', 60.0))
        age = safe_float(base_info.get('age', 24.0))

        weight = st.number_input(f"体重 (kg)", value=safe_float(log.get("weight", w_init)), key=f"w_{name}", disabled=not editable, use_container_width=True)
        
        # 维度输入 - 纵向堆叠适配手机
        chest = st.number_input("胸围 (cm)", value=safe_float(log.get("chest")), key=f"ch_{name}", disabled=not editable, use_container_width=True)
        waist = st.number_input("腰围 (cm)", value=safe_float(log.get("waist")), key=f"wa_{name}", disabled=not editable, use_container_width=True)
        arm = st.number_input("臂围 (cm)", value=safe_float(log.get("arm")), key=f"ar_{name}", disabled=not editable, use_container_width=True)
        hip = st.number_input("臀围 (cm)", value=safe_float(log.get("hip")), key=f"hi_{name}", disabled=not editable, use_container_width=True)
        thigh = st.number_input("大腿围 (cm)", value=safe_float(log.get("thigh")), key=f"th_{name}", disabled=not editable, use_container_width=True)
        calf = st.number_input("小腿围 (cm)", value=safe_float(log.get("calf")), key=f"ca_{name}", disabled=not editable, use_container_width=True)

        if st.button("💾 保存数据", key=f"sv_{name}", disabled=not editable, use_container_width=True):
            try:
                data = {
                    "user_name": name, "log_date": str(view_date),
                    "weight": safe_float(weight), "chest": safe_float(chest), "arm": safe_float(arm),
                    "waist": safe_float(waist), "hip": safe_float(hip), "thigh": safe_float(thigh), "calf": safe_float(calf)
                }
                supabase.table("daily_logs").upsert(data, on_conflict="user_name,log_date").execute()
                st.success("同步成功")
                st.rerun()
            except Exception as e: st.error(f"保存报错: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

        # (2) 趋势分析模块
        st.markdown(f'<div class="card {border_class}"><h3>📈 {name} · 趋势分析</h3>', unsafe_allow_html=True)
        metric_opt = st.selectbox("选择指标", ["weight", "waist", "thigh", "arm", "chest", "hip", "calf"], key=f"opt_{name}")
        if st.button("查看历史趋势 📊", key=f"tr_{name}", use_container_width=True):
            hist = supabase.table("daily_logs").select("*").eq("user_name", name).order("log_date").execute()
            df = pd.DataFrame(hist.data)
            if not df.empty and metric_opt in df.columns:
                df['log_date'] = pd.to_datetime(df['log_date'])
                df = df.set_index('log_date')
                st.line_chart(df[metric_opt], use_container_width=True)
            else: st.warning("暂无数据")
        st.markdown('</div>', unsafe_allow_html=True)

        # (3) 饮食打卡 (AI 分析)
        st.markdown(f'<div class="card {border_class}"><h3>🍱 {name} · 饮食打卡</h3>', unsafe_allow_html=True)
        consumed = safe_float(log.get('calorie_intake', 0.0))
        st.metric("今日已摄入", f"{int(consumed)} kcal")
        f_img = st.file_uploader("📷 上传餐食图片", type=['jpg','png'], key=f"fd_{name}", disabled=not editable)
        if f_img: st.image(f_img, use_container_width=True)
        if st.button("🚀 AI 识别热量", key=f"ai_btn_{name}", disabled=not editable, use_container_width=True):
            add_c = float(random.randint(300, 650)) # 模拟 AI 识别
            supabase.table("daily_logs").upsert({"user_name": name, "log_date": str(view_date), "calorie_intake": consumed + add_c}, on_conflict="user_name,log_date").execute()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # (4) 运动消耗 (AI 计算)
        st.markdown(f'<div class="card {border_class}"><h3>🏋️ {name} · 运动消耗</h3>', unsafe_allow_html=True)
        burn = safe_float(log.get('calorie_burn', 0.0))
        st.metric("今日已消耗", f"{int(burn)} kcal")
        ex_dur = st.number_input("运动时长 (min)", value=int(safe_float(log.get('ex_duration'))), key=f"exd_{name}", disabled=not editable, use_container_width=True)
        if st.button("⚡ 计算消耗", key=f"exb_{name}", disabled=not editable, use_container_width=True):
            # BMR = 10*w + 6.25*h - 5*age - 161 (模拟基础)
            calc_burn = safe_float(ex_dur * random.uniform(6.0, 9.5))
            supabase.table("daily_logs").upsert({
                "user_name": name, "log_date": str(view_date),
                "calorie_burn": calc_burn, "ex_duration": ex_dur
            }, on_conflict="user_name,log_date").execute()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # (5) 健康心得
        st.markdown(f'<div class="card {border_class}"><h3>💭 {name} · 健康心得</h3>', unsafe_allow_html=True)
        note_val = st.text_area("记录今日心情...", value=str(log.get('note', '')), key=f"nt_{name}", disabled=not editable, height=100)
        if st.button("💾 发布心得", key=f"nt_btn_{name}", disabled=not editable, use_container_width=True):
            supabase.table("daily_logs").upsert({"user_name": name, "log_date": str(view_date), "note": str(note_val)}, on_conflict="user_name,log_date").execute()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- 9. 智能布局切换 (手机端上下，桌面端左右) ---
# 注入简单的 JS 来检测屏幕宽度并存入 session_state (若有延迟则默认手机适配)
# 注意：Streamlit 官方没有直接的 is_mobile，采用 columns(2) 的自动折叠特性或分段控制

st.markdown("---")
# 这里的布局在移动端 st.columns(2) 会自动折叠，但为了极致适配我们手动优化：
# 使用 st.columns 在宽屏下并排，在窄屏下自动堆叠是默认行为，但此处为了 100% 成功，我们配合 CSS。

col_left, col_right = st.columns([1, 1])

# 渲染：左侧不差儿，右侧花大爷
render_column("不差儿", col_left, (my_name == "不差儿"), friend_data)
render_column("花大爷", col_right, (my_name == "花大爷"), me_data)

# --- 10. 侧边栏 ---
with st.sidebar:
    st.image(icon_path, width=100) if os.path.exists(icon_path) else None
    if st.button("退出登录 / 切换身份", use_container_width=True):
        st.session_state.clear()
        st.rerun()
