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
            layout="centered"  # 强制居中布局，适配移动端宽度
        )
    else:
        st.set_page_config(page_title="花大爷 × 不差儿", layout="centered")
except:
    st.set_page_config(page_title="花大爷 × 不差儿", layout="centered")

# --- 2. 数据库配置与安全转换 ---
SUPABASE_URL = "https://hjrvdusefkjtmucsreeq.supabase.co"
SUPABASE_KEY = "sb_publishable_yDO1V8a3qYz8YPSzXSHdWA_mhpQG8QF"
TIFFANY_BLUE = "#0ABAB5"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

def safe_float(v, default=0.0):
    try:
        if v is None or str(v).strip() == "" or str(v).lower() == "none":
            return float(default)
        return float(v)
    except: return float(default)

# --- 3. 核心 CSS：移动端纵向适配 + 禁用横向滚动 ---
st.markdown(f"""
    <style>
    /* 强制禁用横向滚动条，解决左右滑动问题 */
    html, body, [data-testid="stAppViewContainer"] {{
        overflow-x: hidden !important;
        width: 100vw !important;
        margin: 0 !important;
        padding: 0 !important;
    }}
    
    /* 锁定深色文字 */
    .stMarkdown, p, span, label, div, .stMetricValue {{
        color: #1A1A1A !important;
        font-family: -apple-system, system-ui, sans-serif !important;
    }}

    .stApp {{ background-color: #F0F9F9; }}
    
    /* 移动端卡片样式：纵向堆叠 */
    .card {{
        background-color: white; 
        padding: 15px; 
        border-radius: 12px;
        border-left: 5px solid {TIFFANY_BLUE}; 
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        width: 100% !important;
    }}
    
    /* 按钮宽度自适应 */
    .stButton>button {{
        background-color: {TIFFANY_BLUE}; 
        color: white !important;
        border-radius: 8px; 
        width: 100%; 
        border: none; 
        font-weight: bold;
        height: 45px;
    }}
    
    /* 隐藏多余边距 */
    [data-testid="column"] {{
        width: 100% !important;
        flex: 1 1 100% !important;
    }}
    
    hr {{ margin: 30px 0; border: 0; border-top: 2px dashed {TIFFANY_BLUE}; }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. 身份登录 ---
if 'user_role' not in st.session_state:
    if os.path.exists(icon_path):
        st.image(icon_path, width=100)
    st.markdown('<div class="card"><h3>👤 确认身份进入基地</h3>', unsafe_allow_html=True)
    role = st.radio("你是谁？", ["不差儿", "花大爷"], horizontal=True)
    if st.button("进入系统", use_container_width=True):
        st.session_state.user_role = role
        st.rerun()
    st.stop()

my_name = st.session_state.user_role
other_name = "花大爷" if my_name == "不差儿" else "不差儿"

# --- 5. 顶栏信息与统计 ---
if os.path.exists(icon_path):
    st.image(icon_path, width=80)

view_date = st.date_input("📅 选择查看日期", date.today())

try:
    # 统计打卡天数
    logs_res = supabase.table("daily_logs").select("log_date").eq("user_name", my_name).execute()
    streak = len({item['log_date'] for item in logs_res.data}) if logs_res.data else 1
except: streak = 1

st.markdown(f"### 🔥 累计打卡: {streak} 天")
st.write(f"今日日期: {view_date} | 天气: 🌦️ 晴 22°C")

# --- 6. 统一渲染函数 (改为纵向堆叠布局) ---
def render_user_section(name, editable, base_info):
    try:
        l_res = supabase.table("daily_logs").select("*").eq("user_name", name).eq("log_date", str(view_date)).execute()
        log = l_res.data[0] if l_res.data else {}
    except: log = {}

    # 用户标题
    st.markdown(f"## {'👩‍𝓠' if name=='不差儿' else '👨‍🦳'} {name} 的日报")
    if not base_info:
        st.warning(f"等待 {name} 初始化基础资料...")
        return

    # 获取基础数据
    h = safe_float(base_info.get('height', 165.0))
    w_base = safe_float(base_info.get('weight', 60.0))
    age = safe_float(base_info.get('age', 24.0))

    # (1) 身体指标与维度 (全部纵向排列)
    with st.container():
        st.markdown('<div class="card"><b>📊 身体指标与维度</b>', unsafe_allow_html=True)
        st.write(f"📏 身高: {int(h)} cm")
        
        weight = st.number_input(f"{name}-体重 (kg)", value=safe_float(log.get("weight", w_base)), key=f"w_{name}", disabled=not editable)
        bmi = round(weight / ((h/100)**2), 1) if h > 0 else 0
        st.write(f"⚖️ BMI: {bmi}")

        # 所有维度纵向平铺，适配手机
        chest = st.number_input("胸围 (cm)", value=safe_float(log.get("chest")), key=f"ch_{name}", disabled=not editable)
        arm = st.number_input("臂围 (cm)", value=safe_float(log.get("arm")), key=f"ar_{name}", disabled=not editable)
        waist = st.number_input("腰围 (cm)", value=safe_float(log.get("waist")), key=f"wa_{name}", disabled=not editable)
        hip = st.number_input("臀围 (cm)", value=safe_float(log.get("hip")), key=f"hi_{name}", disabled=not editable)
        thigh = st.number_input("大腿围 (cm)", value=safe_float(log.get("thigh")), key=f"th_{name}", disabled=not editable)
        calf = st.number_input("小腿围 (cm)", value=safe_float(log.get("calf")), key=f"ca_{name}", disabled=not editable)

        if st.button("💾 保存身体数据", key=f"sv_{name}", disabled=not editable, use_container_width=True):
            try:
                data = {
                    "user_name": name, "log_date": str(view_date),
                    "weight": weight, "chest": chest, "arm": arm, "waist": waist,
                    "hip": hip, "thigh": thigh, "calf": calf
                }
                supabase.table("daily_logs").upsert(data, on_conflict="user_name,log_date").execute()
                st.success("数据同步成功！")
                st.rerun()
            except Exception as e: st.error(f"保存失败: {e}")

        # 趋势功能
        metric_opt = st.selectbox("查看趋势项", ["weight", "waist", "thigh", "chest", "arm", "hip", "calf"], key=f"opt_{name}")
        if st.button("生成趋势图 📈", key=f"tr_{name}", use_container_width=True):
            hist = supabase.table("daily_logs").select("*").eq("user_name", name).order("log_date").execute()
            df = pd.DataFrame(hist.data)
            if not df.empty and metric_opt in df.columns:
                df['log_date'] = pd.to_datetime(df['log_date'])
                st.line_chart(df.set_index('log_date')[metric_opt])
        st.markdown('</div>', unsafe_allow_html=True)

    # (2) 饮食打卡 (AI 分析)
    with st.container():
        st.markdown('<div class="card"><b>🍱 饮食打卡 (AI 识别)</b>', unsafe_allow_html=True)
        consumed = safe_float(log.get('calorie_intake'))
        st.metric("今日摄入", f"{int(consumed)} kcal")
        
        food_img = st.file_uploader(f"上传 {name} 的餐食图片", type=['jpg','png'], key=f"fd_{name}", disabled=not editable)
        if food_img:
            st.image(food_img, use_container_width=True) # 适配手机宽度
        
        if st.button("🚀 启动 AI 饮食分析", key=f"ai_{name}", disabled=not editable, use_container_width=True):
            if not food_img: st.warning("请先上传图片")
            else:
                # 模拟 AI 分析逻辑
                add_cal = float(random.randint(300, 700))
                try:
                    supabase.table("daily_logs").upsert({
                        "user_name": name, "log_date": str(view_date), "calorie_intake": consumed + add_cal
                    }, on_conflict="user_name,log_date").execute()
                    st.rerun()
                except: st.error("写入失败")
        st.markdown('</div>', unsafe_allow_html=True)

    # (3) 运动消耗
    with st.container():
        st.markdown('<div class="card"><b>🏋️ 运动消耗计算</b>', unsafe_allow_html=True)
        burn = safe_float(log.get('calorie_burn'))
        st.metric("已消耗热量", f"{int(burn)} kcal")
        
        ex_dur = st.number_input(f"{name}-运动时长 (分钟)", value=int(safe_float(log.get('ex_duration'))), key=f"exd_{name}", disabled=not editable)
        # 计算逻辑：BMR * 1.2 是基准，运动额外加
        bmr = 10 * weight + 6.25 * h - 5 * age - 161
        
        if st.button("⚡ 计算并同步运动消耗", key=f"exb_{name}", disabled=not editable, use_container_width=True):
            burnt_val = ex_dur * random.uniform(6.0, 10.0)
            try:
                supabase.table("daily_logs").upsert({
                    "user_name": name, "log_date": str(view_date), "calorie_burn": burnt_val, "ex_duration": ex_dur
                }, on_conflict="user_name,log_date").execute()
                st.rerun()
            except: st.error("同步失败")
        st.markdown('</div>', unsafe_allow_html=True)

    # (4) 健康心得 (文字版)
    with st.container():
        st.markdown('<div class="card"><b>💭 健康心得</b>', unsafe_allow_html=True)
        note_val = st.text_area("记录今天的心情或小进步...", value=str(log.get('note', '')), key=f"nt_{name}", disabled=not editable, height=100)
        if st.button("💾 发布心得", key=f"nt_btn_{name}", disabled=not editable, use_container_width=True):
            try:
                supabase.table("daily_logs").upsert({
                    "user_name": name, "log_date": str(view_date), "note": str(note_val)
                }, on_conflict="user_name,log_date").execute()
                st.success("心得已同步至数据库！")
            except: st.error("保存失败")
        st.markdown('</div>', unsafe_allow_html=True)

# --- 7. 渲染主流程 ---
try:
    me_data = supabase.table("users").select("*").eq("name", my_name).execute().data[0]
    friend_res = supabase.table("users").select("*").eq("name", other_name).execute()
    friend_data = friend_res.data[0] if friend_res.data else None
except:
    st.info("请先初始化资料...")
    st.stop()

# 手机适配：核心逻辑改为纵向堆叠
# 首先渲染当前用户（可编辑）
render_user_section(my_name, editable=True, base_info=me_data)

# 分隔线
st.markdown("---")

# 然后渲染队友（只读）
render_user_section(other_name, editable=False, base_info=friend_data)

# 侧边栏/底部退出
if st.button("切换账号 / 退出登录", use_container_width=True):
    st.session_state.clear()
    st.rerun()
