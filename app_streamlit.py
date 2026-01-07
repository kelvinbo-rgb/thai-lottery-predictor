import streamlit as st
import pandas as pd
import random
import collections
import os
import scipy.stats as stats
import datetime
import ast
import requests
from bs4 import BeautifulSoup
import re
import time

# ------------------------------------------------------------
# 🎨 界面样式优化 (CSS)
# ------------------------------------------------------------
st.set_page_config(page_title="Thai Lottery", page_icon="💰", layout="centered")

def clean_html(html_str):
    return "\n".join([line.strip() for line in html_str.split("\n")])

st.markdown(clean_html("""
<style>
.block-container { padding-top: 2rem !important; padding-bottom: 2rem !important; }
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.section-header { font-size: 1.3em; font-weight: 600; margin-bottom: 0; }
.section-sub { font-size: 0.9em; color: #666; margin-top: -5px; margin-bottom: 15px; display: block; }
.custom-metric-card { width: 98%; background-color: #f9f9f9; padding: 10px; border-radius: 8px; border: 1px solid #eee; text-align: left; }
.metric-label { font-size: 0.8em; color: #666; margin-bottom: 2px; }
.metric-value { font-size: 1.8em; font-weight: 700; color: #333; line-height: 1.2; }
.metric-delta { font-size: 0.8em; color: #28a745; font-weight: 500; }
.grid-header { font-size: 1.0em; font-weight: 600; color: #333; }
.grid-sub { font-size: 0.75em; color: #888; font-weight: 400; margin-bottom: 8px; }
.net-profit-box-bt { padding: 5px 0px; }
.net-profit-label-bt { font-size: 0.85em; color: #666; }
.net-profit-value-bt { font-size: 1.2em; font-weight: 700; }
.net-profit-box-mc { padding: 0px 0px; }
.net-profit-label-mc { font-size: 14px; color: rgb(49, 51, 63); margin-bottom: 4px; }
.net-profit-value-mc { font-size: 2rem; font-weight: 600; line-height: 1.2; }
.np-pos { color: #09ab3b; } 
.np-neg { color: #ff2b2b; } 
.sci-box { background-color: #f0f2f6; padding: 15px; border-radius: 5px; border-left: 4px solid #555; font-family: monospace; font-size: 0.9em; margin-bottom: 10px; }
.sci-title { font-weight: bold; font-size: 1.1em; color: #333; margin-bottom: 8px; border-bottom: 1px dashed #999; padding-bottom: 5px;}
.sci-row { display: flex; justify-content: space-between; margin-bottom: 4px; }
.sci-val { font-weight: bold; }
.sci-conclusion-pass { margin-top: 10px; font-weight: bold; color: #09ab3b; }
.sci-conclusion-fail { margin-top: 10px; font-weight: bold; color: #ff2b2b; }
.sci-desc { margin-top: 5px; line-height: 1.4; }
.sci-advice { margin-top: 5px; color: #666; font-style: italic; }
.footer-advice { text-align: center; color: #888; font-size: 1.0em; margin-top: 20px; border-top: 1px solid #eee; padding-top: 10px; }
/* Debug Status Bar */
.status-bar { padding: 8px; margin-bottom: 10px; border-radius: 5px; font-size: 0.85em; text-align: center; }
.status-ok { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
.status-warn { background-color: #fff3cd; color: #856404; border: 1px solid #ffeeba; }
.status-err { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
</style>
"""), unsafe_allow_html=True)

# ------------------------------------------------------------
# 🌍 Config
# ------------------------------------------------------------
LANG = {
    "ภาษาไทย": { "title": "💰 วิเคราะห์หวยไทย (AI)", "data_latest": "งวดประจำวันที่ {}", "auto_update_msg": "กำลังตรวจสอบข้อมูล...", "err_scrape": "ไม่สามารถดึงข้อมูลได้: {}" },
    "中文": { "title": "💰 泰国彩票AI智能策略", "data_latest": "最新开奖日期: {}", "auto_update_msg": "正在同步最新数据...", "err_scrape": "抓取失败: {}" },
    "English": { "title": "💰 Thai Lottery AI Strategy", "data_latest": "Draw Date: {}", "auto_update_msg": "Checking for updates...", "err_scrape": "Scrape failed: {}" }
}

if "lang_choice" not in st.session_state: st.session_state.lang_choice = "ภาษาไทย"
c_l, lc1, lc2, lc3 = st.columns([2, 1, 1, 1])
with lc1: 
    if st.button("🇹🇭 ไทย", use_container_width=True): st.session_state.lang_choice = "ภาษาไทย"; st.rerun()
with lc2: 
    if st.button("🇨🇳 中文", use_container_width=True): st.session_state.lang_choice = "中文"; st.rerun()
with lc3: 
    if st.button("🇺🇸 EN", use_container_width=True): st.session_state.lang_choice = "English"; st.rerun()
T = LANG[st.session_state.lang_choice]

# ------------------------------------------------------------
# 🤖 Auto-Scraper (强制同步版)
# ------------------------------------------------------------
SOURCE_URL = "https://news.sanook.com/lotto/"
DATA_FILE = "historical_data.csv"

def get_thai_month_map():
    return {
        "มกราคม": "01", "กุมภาพันธ์": "02", "มีนาคม": "03", "เมษายน": "04",
        "พฤษภาคม": "05", "มิถุนายน": "06", "กรกฎาคม": "07", "สิงหาคม": "08",
        "กันยายน": "09", "ตุลาคม": "10", "พฤศจิกายน": "11", "ธันวาคม": "12"
    }

def sync_data_with_sanook():
    """
    不管三七二十一，直接去 Sanook 抓最新的显示日期。
    如果和本地不一样，就更新。
    """
    status_placeholder = st.empty() # 用于显示顶部状态
    
    try:
        # 1. 尝试连接
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        try:
            response = requests.get(SOURCE_URL, headers=headers, timeout=5)
        except Exception as e:
            status_placeholder.markdown(f'<div class="status-bar status-err">Network Error: {str(e)}</div>', unsafe_allow_html=True)
            return

        if response.status_code != 200:
            status_placeholder.markdown(f'<div class="status-bar status-err">Sanook Error: {response.status_code}</div>', unsafe_allow_html=True)
            return

        soup = BeautifulSoup(response.content, 'html.parser')

        # 2. 暴力搜索页面上的所有日期
        # 我们寻找 h1 和 h3 里的文本
        candidates = []
        if soup.find("h1"): candidates.append(soup.find("h1").get_text())
        for h3 in soup.find_all("h3", class_="lotto-check__title")[:3]:
            candidates.append(h3.get_text())
            
        month_map = get_thai_month_map()
        best_date = None
        best_prize1 = None
        best_prize2d = None
        
        # 遍历候选文本，寻找有效日期
        for text in candidates:
            # 必须包含月份泰语
            found_month = None
            found_month_num = None
            for m_th, m_num in month_map.items():
                if m_th in text:
                    found_month = m_th
                    found_month_num = m_num
                    break
            
            if not found_month: continue
            
            # 提取日 (1-2位数字)
            day_match = re.search(r'(\d{1,2})\s*' + found_month, text)
            if not day_match: continue
            day = f"{int(day_match.group(1)):02d}"
            
            # 提取年 (25xx)
            year_match = re.search(r'(25\d{2})', text)
            year = str(datetime.datetime.now().year) # Default
            if year_match:
                th_year = int(year_match.group(1))
                year = str(th_year - 543)
            
            # 组装日期
            date_str = f"{found_month_num}/{day}/{year}"
            
            # 找到日期后，尝试找对应的号码
            # 简单的父级查找逻辑
            # 重新定位这个 element 在 soup 里的位置
            # (这里为了简化，如果找到了日期，我们假设它是最新的，直接在全页找 number--1st)
            # 这是一个贪婪策略：Sanook 页面上通常只显示一套详细号码（最新那期）
            
            p1 = soup.find("div", class_=lambda x: x and "number--1st" in x)
            p2d = soup.find("div", class_=lambda x: x and "number--last2" in x)
            
            if p1 and p2d:
                best_date = date_str
                best_prize1 = p1.get_text().strip()
                best_prize2d = p2d.get_text().strip()
                break # 找到了就停止

        if not best_date:
            status_placeholder.markdown(f'<div class="status-bar status-warn">Date Parse Failed (No date found on page)</div>', unsafe_allow_html=True)
            return

        # 3. 读取本地 CSV 进行对比
        if os.path.exists(DATA_FILE):
            df = pd.read_csv(DATA_FILE)
            # 检查这个 best_date 是否已经存在
            # 统一转成 string 对比
            if best_date in df['date'].values:
                # status_placeholder.markdown(f'<div class="status-bar status-ok">Data is up to date: {best_date}</div>', unsafe_allow_html=True)
                return # 已存在，无需更新
        else:
            df = pd.DataFrame(columns=["date", "prize_1st", "prize_2digits", "prize_pre_3digit", "prize_sub_3digits"])

        # 4. 写入新数据
        new_row = {
            "date": best_date,
            "prize_1st": best_prize1,
            "prize_2digits": best_prize2d,
            "prize_pre_3digit": "[]",
            "prize_sub_3digits": "[]"
        }
        
        # 打印调试信息到界面
        status_placeholder.markdown(f'<div class="status-bar status-ok">🎉 Found New Data: {best_date}! Updating...</div>', unsafe_allow_html=True)
        
        df_new = pd.DataFrame([new_row])
        df_new.to_csv(DATA_FILE, mode='a', header=not os.path.exists(DATA_FILE), index=False)
        
        # 强制刷新
        time.sleep(1)
        st.rerun()

    except Exception as e:
        status_placeholder.markdown(f'<div class="status-bar status-err">System Error: {str(e)}</div>', unsafe_allow_html=True)

# 🚀 每次加载页面都执行检查
sync_data_with_sanook()

# ------------------------------------------------------------
# 主界面逻辑 (显示数据)
# ------------------------------------------------------------
st.markdown(clean_html(f"""
<h1 style='text-align: center; color: #E63946; font-size: 1.8em; margin-bottom: 0px;'>
{T['title']}
</h1>
<hr style='margin-top: 5px; margin-bottom: 15px;'>
"""), unsafe_allow_html=True)

# 读取数据
@st.cache_data
def load_data():
    if not os.path.exists(DATA_FILE): return pd.DataFrame()
    df = pd.read_csv(DATA_FILE)
    # 简单的去重，防止重复写入
    df = df.drop_duplicates(subset=['date'], keep='last')
    
    def parse_dt(d):
        try: return pd.to_datetime(d, format="%m/%d/%Y")
        except: 
            try: return pd.to_datetime(d, format="%Y-%m-%d")
            except: return pd.NaT
    df['date_obj'] = df['date'].apply(parse_dt)
    df = df.sort_values('date_obj', ascending=False).reset_index(drop=True)
    return df

df = load_data()

if df.empty:
    st.error("Waiting for data...")
    st.stop()

# 显示最新一期
latest = df.iloc[0]
st.success(f"Loaded {len(df)} records. Latest: {latest['date']}")

# --- Official Style Latest Draw Header ---
# (保留原有的显示逻辑，不做变动)
latest_1st = str(latest['prize_1st']).zfill(6)
latest_2d = str(latest['prize_2digits']).zfill(2)
latest_prefix = []
latest_suffix = []
if 'prize_pre_3digit' in latest:
    raw = str(latest['prize_pre_3digit']).strip()
    if raw.startswith('['): 
        try: latest_prefix = ast.literal_eval(raw)
        except: pass
if 'prize_sub_3digits' in latest:
    raw = str(latest['prize_sub_3digits']).strip()
    if raw.startswith('['): 
        try: latest_suffix = ast.literal_eval(raw)
        except: pass

prefix_str = " ".join([str(x) for x in latest_prefix]) if latest_prefix else "-"
suffix_str = " ".join([str(x) for x in latest_suffix]) if latest_suffix else "-"

st.markdown(clean_html(f"""
<style>
.latest-draw-container {{ background-color: #fff; border: 1px solid #ddd; border-radius: 12px; padding: 15px; text-align: center; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
.latest-date {{ font-size: 1.0em; color: #555; margin-bottom: 15px; font-weight: 500; }}
.prize-1st-box {{ margin-bottom: 20px; }}
.result-number-1st {{ font-size: 2.5em; font-weight: 800; color: #173858; letter-spacing: 3px; }}
.result-title {{ font-size: 0.9em; color: #173858; margin-bottom: 2px; }}
.sub-prizes-row {{ display: flex; justify-content: space-around; flex-wrap: wrap; border-top: 1px solid #eee; padding-top: 15px; }}
.sub-prize-item {{ text-align: center; min-width: 30%; margin-bottom: 10px; }}
.sub-number {{ font-size: 1.4em; font-weight: 700; color: #173858; letter-spacing: 1px; }}
.sub-number-2d {{ font-size: 1.6em; font-weight: 800; color: #173858; }}
</style>
<div class="latest-draw-container">
<div class="latest-date">{T['data_latest'].format(latest['date'])}</div>
<div class="prize-1st-box">
<div class="result-title">รางวัลที่ 1 (1st Prize)</div>
<div class="result-number-1st">{latest_1st}</div>
</div>
<div class="sub-prizes-row">
<div class="sub-prize-item"><div class="result-title">3 ตัวหน้า</div><div class="sub-number">{prefix_str}</div></div>
<div class="sub-prize-item"><div class="result-title">3 ตัวท้าย</div><div class="sub-number">{suffix_str}</div></div>
<div class="sub-prize-item"><div class="result-title">2 ตัวท้าย</div><div class="sub-number sub-number-2d">{latest_2d}</div></div>
</div>
</div>
"""), unsafe_allow_html=True)

# -----------------------------------------------
# 统计 & 策略部分
# -----------------------------------------------
all_2digits = []
all_3digits = []
col_prefix = 'prize_pre_3digit'
col_suffix = 'prize_sub_3digits'

for idx, row in df.iterrows():
    val = str(row['prize_2digits']).strip()
    if len(val) == 1: val = "0" + val
    if val and val.lower() != 'nan': all_2digits.append(val)
    
    # 3D parsing
    for col in [col_prefix, col_suffix]:
        if col in df.columns:
            raw = str(row[col]).strip()
            if raw.startswith('['):
                try:
                    items = ast.literal_eval(raw)
                    if isinstance(items, list):
                        for item in items:
                            if isinstance(item, str) and item.isdigit() and len(item) == 3: all_3digits.append(item)
                except: pass
            elif raw.isdigit() and len(raw) == 3: all_3digits.append(raw)

counter_2 = collections.Counter(all_2digits)
counter_3 = collections.Counter(all_3digits)

# Tab Layout
st.divider()
tab1, tab2, tab3 = st.tabs(["🔥 Trend", "🧪 Random", "📊 Hot"])

def show_picker_grid_card(picks_2, picks_3, reasons_2, reasons_3, desc, mode_label):
    st.markdown(f"<div style='margin-bottom:15px; font-size:0.95em; color:#444;'>{desc}</div>", unsafe_allow_html=True)
    
    left_html = f"""<div style="flex:1; margin-right:5px;"><div class='grid-header'>2 Digits</div>"""
    for i in range(3):
        p = picks_2[i] if i < len(picks_2) else "--"
        r = reasons_2[i] if i < len(reasons_2) else ""
        delta_html = f"<div class='metric-delta'>↑ {r}</div>" if r else ""
        left_html += f"""<div class="custom-metric-card" style="width:100%; margin-bottom:10px;"><div class="metric-label">{mode_label} #{i+1}</div><div class="metric-value">{p}</div>{delta_html}</div>"""
    left_html += "</div>"
    
    right_html = f"""<div style="flex:1; margin-left:5px;"><div class='grid-header'>3 Digits</div>"""
    for i in range(3):
        p = picks_3[i] if i < len(picks_3) else "--"
        r = reasons_3[i] if i < len(reasons_3) else ""
        delta_html = f"<div class='metric-delta'>↑ {r}</div>" if r else ""
        right_html += f"""<div class="custom-metric-card" style="width:100%; margin-bottom:10px;"><div class="metric-label">{mode_label} #{i+1}</div><div class="metric-value">{p}</div>{delta_html}</div>"""
    right_html += "</div>"
    
    st.markdown(f"""<div style="display:flex; flex-direction:row; justify-content:space-between;">{left_html}{right_html}</div>""", unsafe_allow_html=True)

# Trend
pop2 = list(counter_2.keys())
w2 = list(counter_2.values())
t_picks_2 = random.choices(pop2, weights=w2, k=3) if pop2 else ["--"]*3
t_reasons_2 = [f"{counter_2[p]} hits" for p in t_picks_2]
pop3 = list(counter_3.keys())
w3 = list(counter_3.values())
if not pop3: pop3=['000']; w3=[1]
t_picks_3 = random.choices(pop3, weights=w3, k=3)
t_reasons_3 = [f"{counter_3.get(p,0)} hits" for p in t_picks_3]

with tab1: show_picker_grid_card(t_picks_2, t_picks_3, t_reasons_2, t_reasons_3, "Based on historical momentum", "Trend")

# Random
r_picks_2 = [f"{random.randint(0,99):02d}" for _ in range(3)]
r_picks_3 = [f"{random.randint(0,999):03d}" for _ in range(3)]
with tab2: show_picker_grid_card(r_picks_2, r_picks_3, ["Rand"]*3, ["Rand"]*3, "Pure Entropy", "Rand")

# Hot
h_picks_2 = [k for k,v in counter_2.most_common(3)]
h_reasons_2 = [f"{counter_2[k]} hits" for k in h_picks_2]
h_picks_3 = [k for k,v in counter_3.most_common(3)]
h_reasons_3 = [f"{counter_3[k]} hits" for k in h_picks_3]
while len(h_picks_2)<3: h_picks_2.append("--"); h_reasons_2.append("")
while len(h_picks_3)<3: h_picks_3.append("--"); h_reasons_3.append("")
with tab3: show_picker_grid_card(h_picks_2, h_picks_3, h_reasons_2, h_reasons_3, "Most Frequent Numbers", "Hot")

# -----------------------------------------------
# Monte Carlo (Simple)
# -----------------------------------------------
st.divider()
st.subheader("Monte Carlo Simulation")
if st.button("Run Sim (5 Years)"):
    years = 5
    sims = int(24 * years)
    cost = 0; win = 0
    for _ in range(sims):
        cost += 80
        if random.random() < 0.01: win += 2000
    st.metric("Net Profit", f"{win - cost} THB")
    if win > cost: st.success("Profit!")
    else: st.error("Loss")

# -----------------------------------------------
# Footer
# -----------------------------------------------
st.divider()
st.markdown(clean_html(f"""
<div style="text-align: center; margin-top: 20px;">
<h3>☕ Support Creator</h3>
<p style="color: #666;">If you find this useful.</p>
</div>
"""), unsafe_allow_html=True)

dc1, dc2 = st.columns(2)
with dc1: st.image("qr_alipay.jpg", caption="Alipay", use_container_width=True)
with dc2: st.image("qr_promptpay.jpg", caption="PromptPay", use_container_width=True)