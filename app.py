import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, date
import random
import os
from PIL import Image

# --- [0. 数据库修复 SQL - 请务必在 Supabase SQL Editor 执行] ---
# ALTER TABLE public.daily_logs ADD COLUMN IF NOT EXISTS weight float8 DEFAULT 0;
# ALTER TABLE public.daily_logs ADD COLUMN IF NOT EXISTS chest float8 DEFAULT 0;
# ALTER TABLE public.daily_logs ADD COLUMN IF NOT EXISTS arm float8 DEFAULT 0;
# ALTER TABLE public.daily_logs ADD COLUMN IF NOT EXISTS waist float8 DEFAULT 0;
# ALTER TABLE public.daily_logs ADD COLUMN IF NOT EXISTS hip float8 DEFAULT 0;
# ALTER TABLE public.daily_logs ADD COLUMN IF NOT EXISTS thigh float8 DEFAULT 0;
# ALTER TABLE public.daily_logs ADD COLUMN IF NOT EXISTS calf float8 DEFAULT 0;
# ALTER TABLE public.daily_logs ADD COLUMN IF NOT EXISTS calorie_intake float8 DEFAULT 0;
# ALTER TABLE public.daily_logs ADD COLUMN IF NOT EXISTS calorie_burn float8 DEFAULT 0;
# ALTER TABLE public.daily_logs ADD COLUMN IF NOT EXISTS water float8 DEFAULT 0;
# ALTER TABLE public.daily_logs ADD COLUMN IF NOT EXISTS note text;

# --- 1. 基础配置与图标加载 ---
try:
    icon_img = Image.open("app_icon.png")
    st.set_page_config(
        page_title="花大爷 × 不差儿",
        page_icon=icon_img,
        layout="wide",
        initial_sidebar_state="collapsed"
    )
except Exception:
    st.set_page_config(page_title="花大爷 × 不差儿", layout="wide")

# --- 2. 核心常量与 API 配置 ---
SUPABASE_URL = "https://hjrvdusefkjtmucsreeq.supabase.co"
SUPABASE_KEY = "sb_publishable_yDO1V8a3qYz8YPSzXSHdWA_mhpQG8QF"
TIFFANY_BLUE = "#0ABAB5"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# --- 3. 核心修复：数值安全转换函数 (禁止直接使用 float) ---
def safe_float(v, default=0.0):
    try:
        if v is None or str(v).strip() == "" or str(v).lower() == "none":
            return float(default)
        return float(v)
    except:
        return float(default)

# --- 4. 饮食 AI 分析函数 (稳定返回) ---
def analyze_food(img):
    try:
        # 模拟 AI 分析，确保返回 float 类型
        return {"calories": float(random.randint(300, 800))}
    except:
        return {"calories": 500.0}

# --- 5. UI 样式注入 (深色字体、强制左右并排) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #F0F9F9; color: #1A1A1A; }}
    .stMarkdown, p, span, label, div {{ color: #1A1A1A !important; font-weight: 500; }}
    .card {{
        background-color: white; padding: 20px; border-radius: 15px;
        border-top: 5px solid {TIFFANY_BLUE}; box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }}
    .stButton>button {{
        background-color: {TIFFANY_BLUE}; color: white !important;
        border-radius: 10px; width: 100%; border: none; font-weight: bold;
    }}
    [data-testid="column"] {{ width: 50% !important; flex: 1 1 50% !important; min-width: 50% !important; }}
    h3 {{ color: #088F8A !important; text-align: center; margin-bottom: 15px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 6. 身份验证与初始化逻辑 ---
if 'user_role' not in st.session_state:
    st.image("app_icon.png", width=120) if os.path.exists("app_icon.png") else None
    st.markdown('<div class="card"><h3>👤 请确认身份进入基地</h3>', unsafe_allow_html=True)
    role = st.radio("选择身份", ["不差儿", "花大爷"], horizontal=True)
    if st.button("进入系统", use_container_width=True):
        st.session_state.user_role = role
        st.rerun()
    st.stop()

my_name = st.session_state.user_role
other_name = "花大爷" if my_name == "不差儿" else "不差儿"

# 数据库实时判定初始化状态
try:
    res_me = supabase.table("users").select("*").eq("name", my_name).execute()
    initialized = True if res_me.data and len(res_me.data) > 0 else False
except Exception as e:
    st.error(f"数据库访问受阻: {e}")
    st.stop()

if not initialized:
    st.markdown(f'<div class="card"><h3>🐣 首次进入，请初始化 ({my_name})</h3>', unsafe_allow_html=True)
    with st.form("init_form"):
        u_height = st.number_input("身高 (cm)", value=165, step=1)
        u_weight = st.number_input("初始体重 (kg)", value=60.0)
        u_age = st.number_input("年龄", value=24, step=1)
        if st.form_submit_button("🚀 完成初始化"):
            try:
                supabase.table("users").upsert({
                    "name": my_name, "height": int(u_height), "weight": safe_float(u_weight), "age": int(u_age)
                }, on_conflict="name").execute()
                st.rerun()
            except Exception as e: st.error(f"保存失败: {e}")
    st.stop()

# --- 7. 数据加载 ---
try:
    me_data = supabase.table("users").select("*").eq("name", my_name).execute().data[0]
    friend_res = supabase.table("users").select("*").eq("name", other_name).execute()
    friend_data = friend_res.data[0] if friend_res.data else None
except:
    st.error("数据加载异常")
    st.stop()

# 顶部标题栏
st.image("app_icon.png", width=100) if os.path.exists("app_icon.png") else None
c_h1, c_h2 = st.columns([3, 1])
with c_h1:
    view_date = st.date_input("📅 日期选择", date.today())
    st.write(f"今日日期: {view_date} | 天气: 🌦️ 晴转多云 22°C")
with c_h2:
    try:
        streak_res = supabase.table("daily_logs").select("log_date").eq("user_name", my_name).execute()
        streak = len({item['log_date'] for item in streak_res.data}) if streak_res.data else 1
    except: streak = 1
    st.write(f"打卡天数: 🔥 {streak}天")

# --- 8. 统一渲染函数 (左右界面必须完全一致) ---
def render_column(name, col, editable, base_info):
    try:
        l_res = supabase.table("daily_logs").select("*").eq("user_name", name).eq("log_date", str(view_date)).execute()
        log = l_res.data[0] if l_res.data else {}
    except: log = {}

    with col:
        st.markdown(f"### {'👩‍𝓠' if name=='不差儿' else '👨‍🦳'} {name}")
        if not base_info:
            st.info(f"等待 {name} 初始化...")
            return

        # 获取安全数值
        h = safe_float(base_info.get('height', 165.0))
        w_base = safe_float(base_info.get('weight', 60.0))
        age = safe_float(base_info.get('age', 24.0))

        # (1) 身体维度模块 (强制包含全部指标)
        st.markdown('<div class="card"><b>📊 身体指标与维度</b>', unsafe_allow_html=True)
        st.write(f"📏 身高: **{int(h)}** cm (只读)")
        
        # 强制包含全部 7 个指标
        weight = st.number_input("体重 (kg)", value=safe_float(log.get("weight", w_base)), key=f"w_{name}", disabled=not editable)
        chest = st.number_input("胸围 (cm)", value=safe_float(log.get("chest")), key=f"ch_{name}", disabled=not editable)
        arm = st.number_input("臂围 (cm)", value=safe_float(log.get("arm")), key=f"ar_{name}", disabled=not editable)
        waist = st.number_input("腰围 (cm)", value=safe_float(log.get("waist")), key=f"wa_{name}", disabled=not editable)
        hip = st.number_input("臀围 (cm)", value=safe_float(log.get("hip")), key=f"hi_{name}", disabled=not editable)
        thigh = st.number_input("大腿围 (cm)", value=safe_float(log.get("thigh")), key=f"th_{name}", disabled=not editable)
        calf = st.number_input("小腿围 (cm)", value=safe_float(log.get("calf")), key=f"ca_{name}", disabled=not editable)

        bmi = round(weight / ((h/100)**2), 1) if h > 0 else 0
        st.write(f"⚖️ BMI: **{bmi}**")

        if st.button("💾 保存身体数据", key=f"sv_b_{name}", disabled=not editable, use_container_width=True):
            data = {
                "user_name": name, "log_date": str(view_date),
                "weight": weight, "chest": chest, "arm": arm, "waist": waist,
                "hip": hip, "thigh": thigh, "calf": calf
            }
            try:
                supabase.table("daily_logs").upsert(data, on_conflict="user_name,log_date").execute()
                st.success("数据已同步")
                st.rerun()
            except Exception as e: st.error(f"保存失败: {e}")

        # (2) 趋势功能 (支持多指标切换)
        st.markdown("---")
        metric_option = st.selectbox(
            "选择查看趋势图",
            ["weight", "chest", "arm", "waist", "hip", "thigh", "calf"],
            key=f"opt_{name}"
        )
        if st.button("加载趋势图 📈", key=f"tr_btn_{name}", use_container_width=True):
            try:
                hist = supabase.table("daily_logs").select("*").eq("user_name", name).order("log_date").execute()
                df = pd.DataFrame(hist.data)
                if not df.empty and metric_option in df.columns:
                    df['log_date'] = pd.to_datetime(df['log_date'])
                    df = df.set_index('log_date')
                    df[metric_option] = df[metric_option].apply(safe_float)
                    st.line_chart(df[metric_option])
                else: st.warning("暂无历史数据")
            except: st.error("趋势加载失败")
        st.markdown('</div>', unsafe_allow_html=True)

        # (3) 饮食打卡 (缩略图 + 稳定识别)
        st.markdown('<div class="card"><b>🍱 饮食打卡</b>', unsafe_allow_html=True)
        consumed = safe_float(log.get('calorie_intake'))
        st.metric("今日已摄入", f"{int(consumed)} kcal")
        
        food_img = st.file_uploader("📷 上传餐食图片", type=['jpg','png'], key=f"fd_up_{name}", disabled=not editable, label_visibility="collapsed")
        if food_img: st.image(food_img, width=120)
        
        if st.button("🚀 AI 识别热量", key=f"ai_btn_{name}", disabled=not editable, use_container_width=True):
            if not food_img: st.warning("请先上传图片")
            else:
                res = analyze_food(food_img)
                c_val = safe_float(res["calories"])
                try:
                    supabase.table("daily_logs").upsert({
                        "user_name": name, "log_date": str(view_date), "calorie_intake": consumed + c_val
                    }, on_conflict="user_name,log_date").execute()
                    st.rerun()
                except: st.error("热量记录失败")
        st.markdown('</div>', unsafe_allow_html=True)

        # (4) 健身打卡 (输入时长即计算)
        st.markdown('<div class="card"><b>🏋️ 健身打卡</b>', unsafe_allow_html=True)
        ex_img = st.file_uploader("运动打卡图", type=['jpg','png'], key=f"ex_up_{name}", disabled=not editable, label_visibility="collapsed")
        if ex_img: st.image(ex_img, width=120)
        
        ex_d = st.number_input("运动时长 (分钟)", value=int(safe_float(log.get('ex_duration'))), key=f"exd_{name}", disabled=not editable)
        if ex_d > 0:
            burn_est = round(ex_d * 7.5, 2)
            st.metric("预估消耗", f"{burn_est} kcal")
        
        if st.button("⚡ 同步运动热量", key=f"ex_btn_{name}", disabled=not editable, use_container_width=True):
            burnt_val = safe_float(ex_d * random.uniform(5.0, 10.0))
            try:
                supabase.table("daily_logs").upsert({
                    "user_name": name, "log_date": str(view_date), "calorie_burn": burnt_val, "ex_duration": ex_d
                }, on_conflict="user_name,log_date").execute()
                st.rerun()
            except: st.error("运动保存失败")
        st.write(f"⚡ 累计消耗: **{int(safe_float(log.get('calorie_burn')))}** kcal")
        st.markdown('</div>', unsafe_allow_html=True)

        # (5) 健康心得 (左右完全对齐)
        st.markdown('<div class="card"><b>💭 健康心得</b>', unsafe_allow_html=True)
        curr_note = str(log.get('note', ''))
        note = st.text_area("记录今天的小进步...", value=curr_note, key=f"nt_{name}", disabled=not editable, height=100)
        if st.button("💾 保存心得", key=f"nt_btn_{name}", disabled=not editable, use_container_width=True):
            try:
                supabase.table("daily_logs").upsert({
                    "user_name": name, "log_date": str(view_date), "note": str(note)
                }, on_conflict="user_name,log_date").execute()
                st.success("心得已同步")
            except: st.error("心得保存失败")
        st.markdown('</div>', unsafe_allow_html=True)

# 渲染左右分栏 (强制并排)
col_l, col_r = st.columns(2)
render_column("不差儿", col_l, editable=(my_name == "不差儿"), base_info=friend_data)
render_column("花大爷", col_r, editable=(my_name == "花大爷"), base_info=me_data)

if st.sidebar.button("切换身份 / 登出"):
    st.session_state.clear()
    st.rerun()
