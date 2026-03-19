import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, date
import random
import os
from PIL import Image

# --- 1. 基础配置与图标 ---
try:
    icon_img = Image.open("app_icon.png")
    st.set_page_config(page_title="花大爷 × 不差儿", page_icon=icon_img, layout="wide")
except:
    st.set_page_config(page_title="花大爷 × 不差儿", layout="wide")

# --- 2. 数据库与安全转换 ---
URL = "https://hjrvdusefkjtmucsreeq.supabase.co"
KEY = "sb_publishable_yDO1V8a3qYz8YPSzXSHdWA_mhpQG8QF"
supabase: Client = create_client(URL, KEY)

def safe_float(v):
    try:
        return float(v) if v is not None else 0.0
    except: return 0.0

# --- 3. UI 样式 (强制黑字 + 左右对齐) ---
st.markdown("""
    <style>
    .stApp { background-color: #F0F9F9; color: #1A1A1A; }
    .stMarkdown, p, span, label, div { color: #1A1A1A !important; font-weight: 500; }
    .card {
        background-color: white; padding: 20px; border-radius: 15px;
        border-top: 5px solid #0ABAB5; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .stButton>button { background-color: #0ABAB5; color: white !important; border-radius: 10px; width: 100%; border: none; font-weight: bold; }
    [data-testid="column"] { width: 50% !important; flex: 1 1 50% !important; min-width: 50% !important; }
    h3 { color: #088F8A !important; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. 身份登录 ---
if 'user_role' not in st.session_state:
    st.image("app_icon.png", width=120) if os.path.exists("app_icon.png") else st.write("🎨")
    with st.form("login"):
        role = st.selectbox("选择身份", ["花大爷", "不差儿"])
        if st.form_submit_button("进入系统"):
            st.session_state.user_role = role
            st.rerun()
    st.stop()

my_name = st.session_state.user_role
other_name = "不差儿" if my_name == "花大爷" else "花大爷"

# --- 5. 初始化判定 ---
res_me = supabase.table("users").select("*").eq("name", my_name).execute()
if not res_me.data:
    with st.form("init"):
        st.subheader(f"🐣 {my_name}，请初始化")
        h = st.number_input("身高(cm)", 100, 250, 165)
        w = st.number_input("初始体重(kg)", 30.0, 200.0, 60.0)
        age = st.number_input("年龄", 1, 100, 24)
        if st.form_submit_button("完成初始化"):
            supabase.table("users").upsert({"name": my_name, "height": h, "weight": w, "age": age}).execute()
            st.rerun()
    st.stop()

# --- 6. 主界面渲染 ---
st.image("app_icon.png", width=100) if os.path.exists("app_icon.png") else None
view_date = st.date_input("📅 选择日期", date.today())
col_left, col_right = st.columns(2)

def render_column(name, col, is_editable):
    # 数据拉取
    u_res = supabase.table("users").select("*").eq("name", name).execute()
    u_base = u_res.data[0] if u_res.data else None
    l_res = supabase.table("daily_logs").select("*").eq("user_name", name).eq("log_date", str(view_date)).execute()
    log = l_res.data[0] if l_res.data else {}

    with col:
        st.markdown(f"### {'👩‍𝓠' if name=='不差儿' else '👨‍🦳'} {name}")
        if not u_base:
            st.info(f"等待 {name} 初始化...")
            return

        # (1) 身体指标与趋势
        st.markdown('<div class="card"><b>📊 身体指标</b>', unsafe_allow_html=True)
        h = safe_float(u_base['height'])
        w = safe_float(log.get('weight', u_base['weight']))
        st.write(f"📏 身高: {int(h)} cm")
        st.write(f"⚖️ 体重: {w} kg")
        st.write(f"🧬 BMI: {round(w/((h/100)**2), 1)}")
        st.write(f"🔥 体脂率: {log.get('body_fat', 0)}%")
        
        if is_editable:
            new_w = st.number_input("更新体重", value=w, key=f"nw_{name}")
            if st.button("查看体重趋势 📈", key=f"trend_{name}"):
                st.toast("趋势图生成中... (此处可接入历史数据查询)")
            if st.button("保存今日体重", key=f"sw_{name}"):
                try:
                    supabase.table("daily_logs").upsert({"user_name": name, "log_date": str(view_date), "weight": safe_float(new_w)}, on_conflict="user_name,log_date").execute()
                    st.success("同步成功")
                    st.rerun()
                except Exception as e: st.error(f"写入失败: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

        # (2) 围度记录 (找回大腿/小腿)
        st.markdown('<div class="card"><b>📏 身体围度 (cm)</b>', unsafe_allow_html=True)
        g1, g2 = st.columns(2)
        fields = ["chest", "waist", "arm", "hip", "thigh", "calf"]
        labels = ["胸围", "腰围", "臂围", "臀围", "大腿围", "小腿围"]
        
        vals = {}
        for i, (f, lb) in enumerate(zip(fields, labels)):
            target_col = g1 if i % 2 == 0 else g2
            curr_v = safe_float(log.get(f, 0))
            if is_editable:
                vals[f] = target_col.number_input(lb, value=curr_v, key=f"{f}_{name}")
            else:
                target_col.write(f"{lb}: {curr_v}")

        if is_editable and st.button("保存围度数据", key=f"sv_{name}"):
            try:
                # 强制转为 float 写入，防止 22P02 报错
                save_data = {"user_name": name, "log_date": str(view_date)}
                for f in fields: save_data[f] = safe_float(vals[f])
                supabase.table("daily_logs").upsert(save_data, on_conflict="user_name,log_date").execute()
                st.success("围度已更新")
                st.rerun()
            except Exception as e: st.error(f"保存失败: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

        # (3) 饮食打卡 (修复 AI 写入)
        st.markdown('<div class="card"><b>🍱 饮食打卡</b>', unsafe_allow_html=True)
        c_in = safe_float(log.get('calorie_intake', 0))
        st.write(f"🍎 已摄入: {c_in} kcal")
        if is_editable:
            food_img = st.file_uploader("拍美食", type=['jpg','png'], key=f"fi_{name}")
            if food_img: st.image(food_img, width=120)
            if st.button("🚀 AI 饮食分析", key=f"aib_{name}"):
                add_cal = random.randint(300, 600)
                try:
                    supabase.table("daily_logs").upsert({"user_name": name, "log_date": str(view_date), "calorie_intake": c_in + add_cal}, on_conflict="user_name,log_date").execute()
                    st.rerun()
                except Exception as e: st.error(f"写入失败: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

# 渲染
render_column(other_name, col_left, False)
render_column(my_name, col_right, True)
