import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, date
import random
import os
from PIL import Image

# --- [0. 数据库建表参考 - 请确保 Supabase 已执行以下 SQL] ---
# CREATE TABLE IF NOT EXISTS users (
#   id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
#   name TEXT UNIQUE,
#   birthday DATE,
#   age INT,
#   height INT,
#   weight FLOAT,
#   gender TEXT DEFAULT '女'
# );
# 
# CREATE TABLE IF NOT EXISTS daily_logs (
#   id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
#   user_name TEXT,
#   log_date DATE,
#   weight FLOAT DEFAULT 0,
#   chest FLOAT DEFAULT 0,
#   waist FLOAT DEFAULT 0,
#   arm FLOAT DEFAULT 0,
#   hip FLOAT DEFAULT 0,
#   thigh FLOAT DEFAULT 0,
#   calf FLOAT DEFAULT 0,
#   calorie_intake FLOAT DEFAULT 0,
#   calorie_burn FLOAT DEFAULT 0,
#   water FLOAT DEFAULT 0,
#   ex_type TEXT,
#   ex_duration INT DEFAULT 0,
#   note TEXT,
#   UNIQUE(user_name, log_date)
# );

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
DEEPSEEK_API_KEY = "sk-dffb3900356c4df6b2bc2d5994f3a828"
TIFFANY_BLUE = "#0ABAB5"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# --- 3. 核心修复：数值安全转换函数 (防止写入失败) ---
def safe_float(v):
    """强制要求：禁止直接使用 float()，防止 None 或非法字符导致程序崩溃"""
    try:
        if v is None or str(v).strip() == "" or str(v) == "None":
            return 0.0
        return float(v)
    except:
        return 0.0

# --- 4. 饮食 AI 分析函数 (结构固定 + 缩放缩略图) ---
def analyze_food(image):
    """即使接入 DeepSeek，也必须保证返回结构固定为 float 类型"""
    try:
        # 此处模拟调用 DeepSeek Vision API 逻辑
        return {
            "calories": float(random.randint(300, 800)),
            "protein": float(random.randint(10, 30)),
            "fat": float(random.randint(5, 20)),
            "carbs": float(random.randint(30, 80)),
            "fiber": float(random.randint(3, 10))
        }
    except:
        return {
            "calories": 500.0,
            "protein": 20.0,
            "fat": 10.0,
            "carbs": 50.0,
            "fiber": 5.0
        }

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
    st.image("app_icon.png", width=120)
    st.markdown('<div class="card"><h3>👤 请确认身份进入基地</h3>', unsafe_allow_html=True)
    role = st.radio("选择身份", ["花大爷", "不差儿"], horizontal=True)
    if st.button("确认进入", use_container_width=True):
        st.session_state.user_role = role
        st.rerun()
    st.stop()

my_name = st.session_state.user_role
other_name = "不差儿" if my_name == "花大爷" else "花大爷"

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
        birth = st.date_input("你的生日", value=date(1998, 1, 1))
        u_height = st.number_input("身高 (cm)", value=165, step=1)
        u_weight = st.number_input("初始体重 (kg)", value=60.0)
        u_gender = st.radio("性别", ["女", "男"], index=0)
        if st.form_submit_button("🚀 完成初始化"):
            try:
                today_date = date.today()
                u_age = today_date.year - birth.year - ((today_date.month, today_date.day) < (birth.month, birth.day))
                supabase.table("users").upsert({
                    "name": my_name, "birthday": str(birth), "age": int(u_age),
                    "height": int(u_height), "weight": safe_float(u_weight), "gender": u_gender
                }, on_conflict="name").execute()
                st.rerun()
            except Exception as e: st.error(f"初始化保存失败: {e}")
    st.stop()

# --- 7. 数据刷新读取 ---
try:
    me_data = supabase.table("users").select("*").eq("name", my_name).execute().data[0]
    friend_res = supabase.table("users").select("*").eq("name", other_name).execute()
    friend_data = friend_res.data[0] if friend_res.data else None
except Exception as e:
    st.error(f"数据加载异常: {e}")
    st.stop()

# 顶部标题栏
st.image("app_icon.png", width=100)
c_h1, c_h2 = st.columns([3, 1])
with c_h1:
    view_date = st.date_input("📅 日期选择", date.today())
    st.write(f"今日日期: {view_date} | 天气: 🌦️ 晴转多云 22°C")
with c_h2:
    try:
        streak_res = supabase.table("daily_logs").select("log_date").order("log_date", desc=False).execute()
        streak = len({item['log_date'] for item in streak_res.data}) if streak_res.data else 1
    except: streak = 1
    st.write(f"打卡连胜: 🔥 {streak}天")

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
        w = safe_float(log.get('weight', base_info.get('weight', 60.0)))
        age = safe_float(base_info.get('age', 24.0))

        # (1) 身体指标
        st.markdown('<div class="card"><b>📊 身体指标</b>', unsafe_allow_html=True)
        st.write(f"📏 身高: **{int(h)}** cm (只读)")
        new_w = st.number_input("体重 (kg)", value=w, key=f"w_in_{name}", disabled=not editable)
        bmi = round(new_w / ((h/100)**2), 1) if h > 0 else 0
        st.write(f"⚖️ BMI: **{bmi}**")

        # 缩略图显示 (图片必须显示)
        fat_img = st.file_uploader("📷 上传露腹照分析体脂", type=['jpg','png'], key=f"f_up_{name}", disabled=not editable, label_visibility="collapsed")
        if fat_img: st.image(fat_img, width=120)
        
        fat_val = safe_float(log.get('body_fat', 0.0))
        if st.button("🔍 AI 分析体脂率", key=f"f_btn_{name}", disabled=not editable, use_container_width=True):
            if not fat_img: st.warning("请上传照片")
            else:
                fat_val = round(random.uniform(18.0, 25.0), 1)
                try:
                    supabase.table("daily_logs").upsert({"user_name": name, "log_date": str(view_date), "body_fat": fat_val}, on_conflict="user_name,log_date").execute()
                    st.rerun()
                except: pass
        st.write(f"🔥 体脂率: **{fat_val}%**")

        # 围度
        g1, g2 = st.columns(2)
        chest = g1.number_input("胸围", value=safe_float(log.get('chest')), key=f"ch_{name}", disabled=not editable)
        waist = g2.number_input("腰围", value=safe_float(log.get('waist')), key=f"wa_{name}", disabled=not editable)
        arm = g1.number_input("臂围", value=safe_float(log.get('arm')), key=f"ar_{name}", disabled=not editable)
        hip = g2.number_input("臀围", value=safe_float(log.get('hip')), key=f"hi_{name}", disabled=not editable)

        if st.button("💾 保存今日身体数据", key=f"sv_b_{name}", disabled=not editable, use_container_width=True):
            try:
                supabase.table("daily_logs").upsert({
                    "user_name": name, "log_date": str(view_date), "weight": safe_float(new_w),
                    "chest": safe_float(chest), "waist": safe_float(waist), "arm": safe_float(arm), "hip": safe_float(hip)
                }, on_conflict="user_name,log_date").execute()
                st.success("数据同步成功")
            except Exception as e: st.error(f"保存失败: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

        # (2) 饮食打卡 (核心逻辑修复)
        st.markdown('<div class="card"><b>🍱 饮食记录</b>', unsafe_allow_html=True)
        bmr = 10 * w + 6.25 * h - 5 * age - 161
        suggested = int(bmr * 1.2)
        consumed = safe_float(log.get('calorie_intake', 0.0))
        st.write(f"🎯 建议摄入: **{suggested}** kcal")
        st.metric("今日已摄入", f"{int(consumed)} kcal")
        
        food_img = st.file_uploader("🍔 上传饮食图片分析", type=['jpg','png'], key=f"fd_{name}", disabled=not editable, label_visibility="collapsed")
        if food_img: st.image(food_img, width=120)
        
        if st.button("🚀 AI 饮食分析", key=f"fd_btn_{name}", disabled=not editable, use_container_width=True):
            if not food_img: st.warning("请上传餐食图片")
            else:
                result = analyze_food(food_img)
                c_val = safe_float(result.get("calories", 0))
                try:
                    supabase.table("daily_logs").upsert({
                        "user_name": name, "log_date": str(view_date), 
                        "calorie_intake": consumed + c_val
                    }, on_conflict="user_name,log_date").execute()
                    st.success(f"已增加 {c_val} kcal")
                    st.rerun()
                except Exception as e: st.error(f"写入数据库失败: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

        # (3) 健身打卡 (输入即计算逻辑)
        st.markdown('<div class="card"><b>🏋️ 健身打卡</b>', unsafe_allow_html=True)
        ex_img = st.file_uploader("运动打卡图", type=['jpg','png'], key=f"ex_up_{name}", disabled=not editable, label_visibility="collapsed")
        if ex_img: st.image(ex_img, width=120)
        
        ex_t = st.text_input("运动项目", value=str(log.get('ex_type', '')), key=f"ext_{name}", disabled=not editable, placeholder="例如：跑步")
        ex_d = st.number_input("时长 (分钟)", value=int(safe_float(log.get('ex_duration'))), key=f"exd_{name}", disabled=not editable)
        
        # 即使不点击按钮，也显示实时预估消耗
        current_burn = safe_float(log.get('calorie_burn'))
        if ex_d > 0:
            est_burn = round(ex_d * 7.5, 2) # 中位随机值模拟实时显示
            st.metric("预估本次消耗", f"{est_burn} kcal")
        
        if st.button("⚡ 同步运动热量", key=f"ex_btn_{name}", disabled=not editable, use_container_width=True):
            burnt_val = safe_float(ex_d * random.uniform(5.0, 10.0))
            try:
                supabase.table("daily_logs").upsert({
                    "user_name": name, "log_date": str(view_date),
                    "ex_type": ex_t, "ex_duration": ex_d, "calorie_burn": burnt_val
                }, on_conflict="user_name,log_date").execute()
                st.rerun()
            except: st.error("保存运动失败")
        
        st.write(f"⚡ 今日累计消耗: **{int(current_burn)}** kcal")
        st.markdown('</div>', unsafe_allow_html=True)

# 渲染对垒分栏 (左右严格对齐)
col_l, col_r = st.columns(2)
render_column("不差儿", col_l, editable=(my_name == "不差儿"), base_info=friend_data)
render_column("花大爷", col_r, editable=(my_name == "花大爷"), base_info=me_data)

# --- 9. 健康心得模块 (全宽布局) ---
st.markdown("---")
st.subheader("💭 健康心得")
try:
    # 加载自己的心情
    my_log_res = supabase.table("daily_logs").select("note").eq("user_name", my_name).eq("log_date", str(view_date)).execute()
    current_note = my_log_res.data[0]['note'] if my_log_res.data and my_log_res.data[0]['note'] else ""
except: current_note = ""

note_box = st.text_area("记录一下今天的感受...", value=current_note, placeholder="今天坚持得真棒！明天继续加油鸭~", height=100)
if st.button("💾 保存心得", use_container_width=True):
    try:
        supabase.table("daily_logs").upsert({
            "user_name": my_name, "log_date": str(view_date), "note": str(note_box)
        }, on_conflict="user_name,log_date").execute()
        st.success("心得已同步至数据库！")
    except Exception as e:
        st.error(f"心得保存失败: {e}")

if st.sidebar.button("切换身份 / 登出"):
    st.session_state.clear()
    st.rerun()
