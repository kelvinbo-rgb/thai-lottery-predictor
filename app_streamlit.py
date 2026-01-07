import streamlit as st
import pandas as pd
import random
import collections
import os
import datetime
import ast
import requests
from bs4 import BeautifulSoup
import re
import time

# ------------------------------------------------------------
# 🎨 界面样式优化 (CSS)
# ------------------------------------------------------------
st.set_page_config(page_title="Thai Lottery AI", page_icon="💰", layout="centered")

def clean_html(html_str):
    return "\n".join([line.strip() for line in html_str.split("\n")])

st.markdown(clean_html("""
<style>
.block-container { padding-top: 2rem !important; padding-bottom: 2rem !important; }
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.custom-metric-card { width: 98%; background-color: #f9f9f9; padding: 10px; border-radius: 8px; border: 1px solid #eee; text-align: left; }
.metric-label { font-size: 0.8em; color: #666; margin-bottom: 2px; }
.metric-value { font-size: 1.8em; font-weight: 700; color: #333; line-height: 1.2; }
.metric-delta { font-size: 0.8em; color: #28a745; font-weight: 500; }
.grid-header { font-size: 1.0em; font-weight: 600; color: #333; }
.status-bar { padding: 8px; margin-bottom: 10px; border-radius: 5px; font-size: 0.85em; text-align: center; }
.status-ok { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
.status-warn { background-color: #fff3cd; color: #856404; border: 1px solid #ffeeba; }
.status-err { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
</style>
"""), unsafe_allow_html=True)

# ------------------------------------------------------------
# 🌍 Config (默认中文)
# ------------------------------------------------------------
LANG = {
    "ภาษาไทย": { "title": "💰 วิเคราะห์หวยไทย (AI)", "data_latest": "งวดประจำวันที่ {}", "loading": "กำลังโหลด..." },
    "中文": { "title": "💰 泰国彩票AI智能策略", "data_latest": "最新开奖日期: {}", "loading": "正在同步数据..." },
    "English": { "title": "💰 Thai Lottery AI Strategy", "data_latest": "Draw Date: {}", "loading": "Loading..." }
}

if "lang_choice" not in st.session_state: st.session_state.lang_choice = "中文" # Default to Chinese
c_l, lc1, lc2, lc3 = st.columns([2, 1, 1, 1])
with lc1: 
    if st.button("🇹🇭 ไทย", use_container_width=True): st.session_state.lang_choice = "ภาษาไทย"; st.rerun()
with lc2: 
    if st.button("🇨🇳 中文", use_container_width=True): st.session_state.lang_choice = "中文"; st.rerun()
with lc3: 
    if st.button("🇺🇸 EN", use_container_width=True): st.session_state.lang_choice = "English"; st.rerun()
T = LANG[st.session_state.lang_choice]

# ------------------------------------------------------------
# 🤖 Auto-Scraper (暴力搜索版)
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
    status_placeholder = st.empty()
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(SOURCE_URL, headers=headers, timeout=10)
        response.encoding = 'utf-8' # 强制编码
        
        if response.status_code != 200:
            status_placeholder.markdown(f'<div class="status-bar status-err">Network Error: {response.status_code}</div>', unsafe_allow_html=True)
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        full_text = soup.get_text() # 获取所有纯文本，忽略HTML标签结构

        # 1. 暴力正则匹配日期
        # 格式：数字(1-2位) + 空格 + 泰语月份 + 空格 + 25xx(年份)
        month_names = "|".join(get_thai_month_map().keys())
        # Regex: Look for pattern like "16 มกราคม 2569"
        pattern = re.compile(r'(\d{1,2})\s+(' + month_names + r')\s+(25\d{2})')
        
        matches = pattern.findall(full_text)
        
        if not matches:
            # 备用正则：可能空格被压缩了
            pattern_tight = re.compile(r'(\d{1,2})\s*(' + month_names + r')\s*(25\d{2})')
            matches = pattern_tight.findall(full_text)

        if not matches:
            status_placeholder.markdown(f'<div class="status-bar status-warn">Date Parse Failed (No date pattern found in text)</div>', unsafe_allow_html=True)
            return

        # 我们取第一个匹配到的日期（通常是页面最显眼的位置，即最新日期）
        day_raw, month_raw, year_raw = matches[0]
        
        # 转换格式
        month_map = get_thai_month_map()
        mm = month_map.get(month_raw, "01")
        dd = f"{int(day_raw):02d}"
        yyyy = str(int(year_raw) - 543) # 泰历转公历
        
        best_date = f"{mm}/{dd}/{yyyy}" # Format: MM/DD/YYYY

        # 2. 检查本地 CSV，如果已存在则跳过
        if os.path.exists(DATA_FILE):
            df = pd.read_csv(DATA_FILE)
            if best_date in df['date'].values:
                # 数据已是最新，安静退出
                return 
        else:
            df = pd.DataFrame(columns=["date", "prize_1st", "prize_2digits"])

        # 3. 抓取号码 (使用最稳定的 Class)
        # 无论日期在哪里，最新的奖号通常在特定的 CSS class 里
        p1 = soup.find("div", class_=lambda x: x and "number--1st" in x)
        p2d = soup.find("div", class_=lambda x: x and "number--last2" in x)
        
        if not p1 or not p2d:
            status_placeholder.markdown(f'<div class="status-bar status-warn">Found Date {best_date} but no numbers found. Structure changed?</div>', unsafe_allow_html=True)
            return
            
        prize_1 = p1.get_text().strip()
        prize_2d = p2d.get_text().strip()

        # 4. 写入数据
        new_row = {
            "date": best_date,
            "prize_1st": prize_1,
            "prize_2digits": prize_2d,
            "prize_pre_3digit": "[]",
            "prize_sub_3digits": "[]"
        }
        
        status_placeholder.markdown(f'<div class="status-bar status-ok">✅ Updating: {best_date} | 1st: {prize_1} | 2d: {prize_2d}</div>', unsafe_allow_html=True)
        
        df_new = pd.DataFrame([new_row])
        df_new.to_csv(DATA_FILE, mode='a', header=not os.path.exists(DATA_FILE), index=False)
        
        time.sleep(1.5)
        st.rerun()

    except Exception as e:
        status_placeholder.markdown(f'<div class="status-bar status-err">System Error: {str(e)}</div>', unsafe_allow_html=True)

# 🚀 Run Scraper
sync_data_with_sanook()

# ------------------------------------------------------------
# 主界面逻辑
# ------------------------------------------------------------
st.markdown(clean_html(f"""
<h1 style='text-align: center; color: #E63946; font-size: 1.8em; margin-bottom: 0px;'>
{T['title']}
</h1>
<hr style='margin-top: 5px; margin-bottom: 15px;'>
"""), unsafe_allow_html=True)

@st.cache_data
def load_data():
    if not os.path.exists(DATA_FILE): return pd.DataFrame()
    df = pd.read_csv(DATA_FILE)
    
    # 清洗：删除重复
    df = df.drop_duplicates(subset=['date'], keep='last')
    
    def parse_dt(d):
        try: return pd.to_datetime(d, format="%m/%d/%Y")
        except: 
            try: return pd.to_datetime(d, format="%Y-%m-%d")
            except: return pd.NaT
    df['date_obj'] = df['date'].apply(parse_dt)
    
    # 清洗：删除未来的诡异日期（比如误判为 3000年的）
    # 但保留2026年的数据
    today_limit = datetime.datetime.now() + datetime.timedelta(days=60)
    df = df[df['date_obj'] < today_limit]
    
    df = df.sort_values('date_obj', ascending=False).reset_index(drop=True)
    return df

df = load_data()

if df.empty:
    st.warning("No data found locally. Waiting for scrape...")
    st.stop()

# 显示最新一期
latest = df.iloc[0]
latest_1st = str(latest['prize_1st']).zfill(6)
latest_2d = str(latest['prize_2digits']).zfill(2)

# Sub prizes parsing
latest_prefix = []
latest_suffix = []
if 'prize_pre_3digit' in latest:
    try: latest_prefix = ast.literal_eval(str(latest['prize_pre_3digit']))
    except: pass
if 'prize_sub_3digits' in latest:
    try: latest_suffix = ast.literal_eval(str(latest['prize_sub_3digits']))
    except: pass
    
prefix_str = " ".join([str(x) for x in latest_prefix]) if isinstance(latest_prefix, list) and latest_prefix else "-"
suffix_str = " ".join([str(x) for x in latest_suffix]) if isinstance(latest_suffix, list) and latest_suffix else "-"

st.markdown(clean_html(f"""
<style>
.latest-draw-container {{ background-color: #fff; border: 1px solid #ddd; border-radius: 12px; padding: 15px; text-align: center; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
.latest-date {{ font-size: 1.0em; color: #555; margin-bottom: 15px; font-weight: 500; }}
.result-number-1st {{ font-size: 2.5em; font-weight: 800; color: #173858; letter-spacing: 3px; }}
.sub-number-2d {{ font-size: 1.6em; font-weight: 800; color: #173858; }}
</style>
<div class="latest-draw-container">
<div class="latest-date">{T['data_latest'].format(latest['date'])}</div>
<div style="margin-bottom:20px;">
    <div style="font-size:0.9em;color:#173858;">{T['title'].split(' ')[0]} 1st Prize</div>
    <div class="result-number-1st">{latest_1st}</div>
</div>
<div style="display:flex; justify-content:space-around; border-top:1px solid #eee; padding-top:10px;">
    <div><div style="font-size:0.8em;">3 Prefix</div><div style="font-weight:700;color:#555;">{prefix_str}</div></div>
    <div><div style="font-size:0.8em;">3 Suffix</div><div style="font-weight:700;color:#555;">{suffix_str}</div></div>
    <div><div style="font-size:0.8em;">2 Digits</div><div class="sub-number-2d">{latest_2d}</div></div>
</div>
</div>
"""), unsafe_allow_html=True)

# -----------------------------------------------
# 统计 & 策略部分
# -----------------------------------------------
all_2digits = []
all_3digits = []

for idx, row in df.iterrows():
    val = str(row['prize_2digits']).strip()
    if len(val) == 1: val = "0" + val
    if val and val.lower() != 'nan': all_2digits.append(val)
    # 3D parsing (simplified)
    for col in ['prize_pre_3digit', 'prize_sub_3digits']:
        if col in df.columns:
            try:
                items = ast.literal_eval(str(row[col]))
                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, str) and item.isdigit() and len(item) == 3: all_3digits.append(item)
            except: pass

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
# Footer
# -----------------------------------------------
st.divider()
st.markdown(clean_html(f"""
<div style="text-align: center; margin-top: 20px;">
<h3>☕ Support Creator</h3>
</div>
"""), unsafe_allow_html=True)

dc1, dc2 = st.columns(2)
with dc1: st.image("qr_alipay.jpg", caption="Alipay", use_container_width=True)
with dc2: st.image("qr_promptpay.jpg", caption="PromptPay", use_container_width=True)