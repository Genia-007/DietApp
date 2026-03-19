import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, date
import random
import os
from PIL import Image

# --- [0. 数据库修复 SQL - 请务必在 Supabase 执行] ---
# ALTER TABLE public.daily_logs ADD COLUMN IF NOT EXISTS thigh float8 DEFAULT 0;
# ALTER TABLE public.daily_logs ADD COLUMN IF NOT EXISTS calf float8 DEFAULT 0;
# ALTER TABLE public.daily_logs ADD COLUMN IF NOT EXISTS note text;

# --- 1. 基础配置与图标 ---
try:
    icon_img = Image.open("app_icon.png")
    st.set_page_config(page_title="花大爷 × 不差儿", page_icon=icon_img, layout="wide")
except:
    st.set_page_config(page_title="花大爷 × 不差儿", layout="wide")

# --- 2. 数据库配置 ---
SUPABASE_URL = "https://hjrvdusefkjtmucsreeq.supabase.co"
SUPABASE_KEY = "sb_publishable_yDO1V8a3qYz8YPSzXSHdWA_mhpQG8QF"
TIFFANY_BLUE = "#0ABAB5"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# --- 3. 核心修复：数值安全转换函数 ---
def safe_float(v, default=0.0):
    """强制要求：禁止直接使用 float()"""
    try:
        if v is None or str(v).strip() == "" or str(v) == "None":
            return float(default)
        return float(v)
    except:
        return float(default)

# --- 4. 饮食分析 (必须稳定) ---
def analyze_food(img):
    """即使模拟也必须返回固定结构，确保写入不报错"""
    try:
        # 模拟 AI 分析结果
        return {"calories": float(random.randint(300, 800))}
    except:
        return {"calories": 500.0}

# --- 5. UI 样式注入 ---
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
    st.markdown('<div class="card"><h3>👤 请确认身份进入</h3>', unsafe_allow_html=True)
    role = st.radio("你是谁？", ["花大爷", "不差儿"], horizontal=True)
    if st.button("进入基地", use_container_width=True):
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
    st.error(f"数据库连接失败: {e}")
    st.stop()

if not initialized:
    st.markdown(f'<div class="card"><h3>🐣 欢迎，{my_name}！请初始化资料</h3>', unsafe_allow_html=True)
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

# --- 7. 数据刷新读取 ---
try:
    me_data = supabase.table("users").select("*").eq("name", my_name).execute().data[0]
    friend_res = supabase.table("users").select("*").eq("name", other_name).execute()
    friend_data = friend_res.data[0] if friend_res.data else None
except:
    st.error("数据拉取异常")
    st.stop()

# 顶部信息
st.image("app_icon.png", width=100) if os.path.exists("app_icon.png") else None
c_h1, c_h2 = st.columns([3, 1])
with c_h1:
    view_date = st.date_input("📅 选择日期", date.today())
    st.write(f"今日日期: {view_date} | 天气: 🌦️ 晴转多云 22°C")
with c_h2:
    try:
        streak_res = supabase.table("daily_logs").select("log_date").eq("user_name", my_name).execute()
        streak = len({item['log_date'] for item in streak_res.data}) if streak_res.data else 1
    except: streak = 1
    st.write(f"打卡天数: 🔥 {streak}天")

# --- 8. 统一渲染函数 (左右界面必须完全一致) ---
def render_column(name, col, editable, base_info):
    # 每次刷新重新读取数据库
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

        # (1) 身体指标与趋势 (必须新增趋势功能)
        st.markdown('<div class="card"><b>📊 身体指标</b>', unsafe_allow_html=True)
        st.write(f"📏 身高: **{int(h)}** cm")
        new_w = st.number_input("体重 (kg)", value=w, key=f"w_{name}", disabled=not editable)
        bmi = round(new_w / ((h/100)**2), 1) if h > 0 else 0
        st.write(f"⚖️ BMI: **{bmi}**")

        if st.button("查看趋势 📈", key=f"trend_btn_{name}", use_container_width=True):
            try:
                hist = supabase.table("daily_logs").select("*").eq("user_name", name).order("log_date").execute()
                df = pd.DataFrame(hist.data)
                if not df.empty:
                    df['log_date'] = pd.to_datetime(df['log_date'])
                    df = df.set_index('log_date')
                    st.line_chart(df[['weight', 'waist', 'thigh']])
                else: st.warning("暂无历史数据")
            except: st.error("趋势加载失败")

        # 围度 (补全大腿/小腿)
        g1, g2 = st.columns(2)
        waist = g1.number_input("腰围", value=safe_float(log.get('waist')), key=f"wa_{name}", disabled=not editable)
        hip = g2.number_input("臀围", value=safe_float(log.get('hip')), key=f"hi_{name}", disabled=not editable)
        thigh = g1.number_input("大腿围", value=safe_float(log.get('thigh')), key=f"th_{name}", disabled=not editable)
        calf = g2.number_input("小腿围", value=safe_float(log.get('calf')), key=f"ca_{name}", disabled=not editable)

        if st.button("💾 保存身体数据", key=f"sv_b_{name}", disabled=not editable, use_container_width=True):
            data = {
                "user_name": name, "log_date": str(view_date),
                "weight": safe_float(new_w), "waist": safe_float(waist),
                "hip": safe_float(hip), "thigh": safe_float(thigh), "calf": safe_float(calf)
            }
            try:
                # 先查再写逻辑
                existing = supabase.table("daily_logs").select("*").eq("user_name", name).eq("log_date", str(view_date)).execute()
                if existing.data: supabase.table("daily_logs").update(data).eq("user_name", name).eq("log_date", str(view_date)).execute()
                else: supabase.table("daily_logs").insert(data).execute()
                st.rerun()
            except Exception as e: st.error(f"写入失败: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

        # (2) 饮食打卡 (必须稳定且显示图片)
        st.markdown('<div class="card"><b>🍱 饮食打卡</b>', unsafe_allow_html=True)
        consumed = safe_float(log.get('calorie_intake', 0.0))
        st.metric("已摄入", f"{int(consumed)} kcal")
        
        food_img = st.file_uploader("🍔 上传餐食图片", type=['jpg','png'], key=f"fd_{name}", disabled=not editable, label_visibility="collapsed")
        if food_img: st.image(food_img, width=120)
        
        if st.button("🚀 AI 饮食分析", key=f"fd_btn_{name}", disabled=not editable, use_container_width=True):
            if not food_img: st.warning("请上传图片")
            else:
                res = analyze_food(food_img)
                c_val = safe_float(res["calories"])
                try:
                    supabase.table("daily_logs").upsert({
                        "user_name": name, "log_date": str(view_date), "calorie_intake": consumed + c_val
                    }, on_conflict="user_name,log_date").execute()
                    st.rerun()
                except Exception as e: st.error(f"写入失败: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

        # (3) 健身打卡 (必须自动计算消耗)
        st.markdown('<div class="card"><b>🏋️ 健身打卡</b>', unsafe_allow_html=True)
        ex_img = st.file_uploader("运动图", type=['jpg','png'], key=f"ex_{name}", disabled=not editable, label_visibility="collapsed")
        if ex_img: st.image(ex_img, width=120)
        ex_t = st.text_input("运动项目", value=str(log.get('ex_type', '')), key=f"ext_{name}", disabled=not editable, placeholder="例如：跑步")
        ex_d = st.number_input("时长 (分钟)", value=int(safe_float(log.get('ex_duration'))), key=f"exd_{name}", disabled=not editable)
        
        # 自动计算显示
        if ex_d > 0:
            burn_est = round(ex_d * 7.5, 2)
            st.metric("预估本次消耗", f"{burn_est} kcal")
        
        if st.button("⚡ 同步运动热量", key=f"ex_btn_{name}", disabled=not editable, use_container_width=True):
            burnt_val = safe_float(ex_d * random.uniform(5.0, 10.0))
            try:
                supabase.table("daily_logs").upsert({
                    "user_name": name, "log_date": str(view_date),
                    "ex_type": ex_t, "ex_duration": ex_d, "calorie_burn": burnt_val
                }, on_conflict="user_name,log_date").execute()
                st.rerun()
            except: st.error("保存失败")
        st.write(f"⚡ 今日累计消耗: **{int(safe_float(log.get('calorie_burn')))}** kcal")
        st.markdown('</div>', unsafe_allow_html=True)

# 渲染分栏
col_l, col_r = st.columns(2)
render_column("不差儿", col_l, editable=(my_name == "不差儿"), base_info=friend_data)
render_column("花大爷", col_r, editable=(my_name == "花大爷"), base_info=me_data)

# (4) 健康心得 (文字版最底部)
st.markdown('<div class="card"><b>💭 健康心得</b>', unsafe_allow_html=True)
try:
    my_note_res = supabase.table("daily_logs").select("note").eq("user_name", my_name).eq("log_date", str(view_date)).execute()
    current_note = my_note_res.data[0]['note'] if my_note_res.data and my_note_res.data[0]['note'] else ""
except: current_note = ""

note_text = st.text_area("记录今天的心情或进步...", value=current_note, placeholder="今天坚持得真棒！", height=100)
if st.button("💾 保存心得", use_container_width=True):
    try:
        supabase.table("daily_logs").upsert({
            "user_name": my_name, "log_date": str(view_date), "note": str(note_text)
        }, on_conflict="user_name,log_date").execute()
        st.success("心得已同步")
    except Exception as e: st.error(f"保存失败: {e}")
st.markdown('</div>', unsafe_allow_html=True)

if st.sidebar.button("登出 / 切换账号"):
    st.session_state.clear()
    st.rerun()
