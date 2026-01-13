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
# 🎨 界面样式 (原始风格)
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

if "lang_choice" not in st.session_state: st.session_state.lang_choice = "中文"
c_l, lc1, lc2, lc3 = st.columns([2, 1, 1, 1])
with lc1: 
    if st.button("🇹🇭 ไทย", use_container_width=True): st.session_state.lang_choice = "ภาษาไทย"; st.rerun()
with lc2: 
    if st.button("🇨🇳 中文", use_container_width=True): st.session_state.lang_choice = "中文"; st.rerun()
with lc3: 
    if st.button("🇺🇸 EN", use_container_width=True): st.session_state.lang_choice = "English"; st.rerun()
T = LANG[st.session_state.lang_choice]

# ------------------------------------------------------------
# 🤖 Auto-Scraper (修复逻辑：只抓有数据的日期)
# ------------------------------------------------------------
SOURCE_URL = "https://news.sanook.com/lotto/"
DATA_FILE = "historical_data.csv"

def get_thai_month_map():
    return {
        "มกราคม": "01", "กุมภาพันธ์": "02", "มีนาคม": "03", "เมษายน": "04",
        "พฤษภาคม": "05", "มิถุนายน": "06", "กรกฎาคม": "07", "สิงหาคม": "08",
        "กันยายน": "09", "ตุลาคม": "10", "พฤศจิกายน": "11", "ธันวาคม": "12"
    }

def scrape_and_append(current_df):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(SOURCE_URL, headers=headers, timeout=10)
        if response.status_code != 200: return

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 1. 找到所有可能的“彩票区块”
        # Sanook 将每一期彩票放在 class="lotto-check__item" 或类似的结构里
        # 我们遍历页面上所有包含“รางวัลที่ 1” (一等奖) 的区块
        
        # 查找所有一等奖的容器 (div)
        prize_blocks = soup.find_all("div", class_=lambda x: x and "number--1st" in x)
        
        if not prize_blocks: return

        month_map = get_thai_month_map()
        
        for p1_div in prize_blocks:
            # 对于每一个找到的号码块，往上找它的父容器，直到找到包含日期的标题
            # 或者简单点：在这个块附近找日期
            
            # 获取一等奖号码
            prize_1 = p1_div.get_text().strip()
            if not prize_1 or not prize_1.isdigit(): continue # 如果是空的或者是占位符，跳过

            # 尝试找对应的末两位
            # 在同一个父级容器里找
            parent = p1_div.find_parent("div", class_="lotto-check__content") or p1_div.find_parent("article") or soup
            p2d_div = parent.find("div", class_=lambda x: x and "number--last2" in x)
            if not p2d_div: continue
            prize_2d = p2d_div.get_text().strip()

            # 尝试找对应的日期
            # 通常在父容器的 h3 或 time 标签里
            # 获取父容器内的所有文本
            block_text = parent.get_text()
            
            # 解析日期
            found_month = None
            found_month_num = None
            for m_th, m_num in month_map.items():
                if m_th in block_text:
                    found_month = m_th
                    found_month_num = m_num
                    break
            
            if not found_month: continue
            
            # 正则提取日期
            day_match = re.search(r'(\d{1,2})\s*' + found_month, block_text)
            year_match = re.search(r'(25\d{2})', block_text)
            
            if not day_match: continue
            
            day = f"{int(day_match.group(1)):02d}"
            
            if year_match:
                th_year = int(year_match.group(1))
                year = str(th_year - 543)
            else:
                year = str(datetime.datetime.now().year)

            date_str = f"{found_month_num}/{day}/{year}"
            
            # 找到了一组完整的数据 (日期 + 1等奖 + 2位)
            # 检查是否已存在
            if date_str not in current_df['date'].values:
                # 写入 CSV
                new_row = {
                    "date": date_str,
                    "prize_1st": prize_1,
                    "prize_2digits": prize_2d,
                    "prize_pre_3digit": "[]",
                    "prize_sub_3digits": "[]"
                }
                df_new = pd.DataFrame([new_row])
                df_new.to_csv(DATA_FILE, mode='a', header=False, index=False)
                st.toast(f"Updated: {date_str}", icon="✅")
                time.sleep(1)
                st.rerun()
                return # 更新一次即可
            else:
                # 如果这个日期已经有了，且是页面上最新的（第一个），那说明不需要更新
                # 继续检查下一个 block 吗？通常不需要，因为我们只要最新的
                # 但为了保险，只在第一个匹配项退出
                return

    except Exception as e:
        print(f"Scrape Error: {e}")

def update_dataset_if_needed():
    if not os.path.exists(DATA_FILE): return

    try:
        df = pd.read_csv(DATA_FILE)
        
        # 简单的触发逻辑：如果数据行数少，或者想每次都检查，直接运行
        # 为了不影响性能，我们只在“看似需要更新”时运行
        # 但既然之前判定总出错，我们这里做一个简单的 CD (Cool Down)
        # 或者：每次加载页面都静默检查一次（不转圈圈，后台跑）
        scrape_and_append(df)
            
    except Exception as e:
        pass

# Run Auto-Update Check
update_dataset_if_needed()

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
@st.cache_data(ttl=300)  # Cache for 5 minutes, then refresh
def load_data():
    if not os.path.exists(DATA_FILE): return pd.DataFrame()
    df = pd.read_csv(DATA_FILE)
    df = df.drop_duplicates(subset=['date'], keep='last')
    
    def parse_dt(d):
        try: return pd.to_datetime(d, format="%m/%d/%Y")
        except: 
            try: return pd.to_datetime(d, format="%Y-%m-%d")
            except: return pd.NaT
    df['date_obj'] = df['date'].apply(parse_dt)
    
    # 过滤未来的错误数据 (Dirty Data Fix)
    today = datetime.datetime.now()
    # 允许未来 5 天的误差，防止时区问题，但超过5天肯定错
    df = df[df['date_obj'] <= (today + datetime.timedelta(days=5))]
    
    df = df.sort_values('date_obj', ascending=False).reset_index(drop=True)
    return df

df = load_data()

if df.empty:
    st.error("No Data.")
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
<div class="result-title">1st Prize</div>
<div class="result-number-1st">{latest_1st}</div>
</div>
<div class="sub-prizes-row">
<div class="sub-prize-item"><div class="result-title">3 Prefix</div><div class="sub-number">{prefix_str}</div></div>
<div class="sub-prize-item"><div class="result-title">3 Suffix</div><div class="sub-number">{suffix_str}</div></div>
<div class="sub-prize-item"><div class="result-title">2 Digits</div><div class="sub-number sub-number-2d">{latest_2d}</div></div>
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
    for col in ['prize_pre_3digit', 'prize_sub_3digits']:
        if col in df.columns:
            try:
                items = ast.literal_eval(str(row[col]))
                if isinstance(items, list):
                    for item in items:
                        # Handle both integers and strings, pad to 3 digits
                        item_str = str(item).strip()
                        if item_str.isdigit() and 1 <= len(item_str) <= 3:
                            all_3digits.append(item_str.zfill(3))
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
t_reasons_2 = [f"{counter_2[p]} hits" for p in t_picks_2 if p != "--"]
pop3 = list(counter_3.keys())
w3 = list(counter_3.values())
if not pop3: pop3=['000']; w3=[1]
t_picks_3 = random.choices(pop3, weights=w3, k=3)
t_reasons_3 = [f"{counter_3.get(p,0)} hits" for p in t_picks_3 if p != "--"]
# Ensure 3 picks with padding
while len(t_picks_2) < 3: t_picks_2.append("--"); t_reasons_2.append("")
while len(t_picks_3) < 3: t_picks_3.append("--"); t_reasons_3.append("")
while len(t_reasons_2) < 3: t_reasons_2.append("")
while len(t_reasons_3) < 3: t_reasons_3.append("")

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
# Module 3: Mathematical Truth (数学真相概率表)
# -----------------------------------------------
st.divider()
st.subheader("📊 Mathematical Truth")
st.markdown("*Prize probabilities and expected values based on official lottery structure*")

# Thai Lottery Prize Structure
prize_data = [
    {"Prize": "1st Prize", "Probability": "1/1,000,000", "Payout": "6,000,000 THB", "EV/Ticket": "6.00 THB"},
    {"Prize": "Nearby 1st", "Probability": "2/1,000,000", "Payout": "100,000 THB", "EV/Ticket": "0.20 THB"},
    {"Prize": "2nd Prize", "Probability": "5/1,000,000", "Payout": "200,000 THB", "EV/Ticket": "1.00 THB"},
    {"Prize": "3rd Prize", "Probability": "10/1,000,000", "Payout": "80,000 THB", "EV/Ticket": "0.80 THB"},
    {"Prize": "4th Prize", "Probability": "50/1,000,000", "Payout": "40,000 THB", "EV/Ticket": "2.00 THB"},
    {"Prize": "5th Prize", "Probability": "100/1,000,000", "Payout": "20,000 THB", "EV/Ticket": "2.00 THB"},
    {"Prize": "3-Digit (Front/Back)", "Probability": "4,000/1,000,000", "Payout": "4,000 THB", "EV/Ticket": "16.00 THB"},
    {"Prize": "2-Digit (Last)", "Probability": "10,000/1,000,000", "Payout": "2,000 THB", "EV/Ticket": "20.00 THB"},
]
import pandas as pd
prize_df = pd.DataFrame(prize_data)
st.dataframe(prize_df, use_container_width=True, hide_index=True)

# Summary
total_ev = 6 + 0.2 + 1 + 0.8 + 2 + 2 + 16 + 20  # ~48 THB
ticket_cost = 80
st.markdown(f"""
**Summary:**
- 💰 Ticket Cost: **{ticket_cost} THB**
- 📈 Expected Return per Ticket: **~{total_ev:.0f} THB**
- 📉 Expected Loss per Ticket: **~{ticket_cost - total_ev:.0f} THB** (ROI: {((total_ev/ticket_cost)-1)*100:.1f}%)
""")

# -----------------------------------------------
# Module 4: Historical Backtest (历史模拟回测)
# -----------------------------------------------
st.divider()
st.subheader("⏪ Historical Backtest")
st.markdown("*Simulate playing with historical data*")

backtest_years = st.slider("Backtest Period (Years)", min_value=1, max_value=10, value=3)

if st.button("Run Backtest"):
    # Get data for backtest
    draws_per_year = 24
    total_periods = min(backtest_years * draws_per_year, len(df))
    
    if total_periods < 12:
        st.warning("Not enough historical data for this backtest period.")
    else:
        trend_hits = 0
        random_hits = 0
        cost_per_draw = 240  # 3 tickets @ 80 THB
        
        # Chronological order for rolling backtest
        df_chrono = df.sort_values('date_obj', ascending=True).reset_index(drop=True)
        start_idx = max(0, len(df_chrono) - total_periods)
        
        for i in range(start_idx + 10, len(df_chrono)):  # Need at least 10 prior periods
            target = str(df_chrono.iloc[i]['prize_2digits']).strip().zfill(2)
            
            # Build history up to this point
            history = []
            for j in range(start_idx, i):
                val = str(df_chrono.iloc[j]['prize_2digits']).strip()
                if val and val.lower() != 'nan':
                    history.append(val.zfill(2))
            
            if not history:
                continue
                
            # Trend strategy: weighted random from history
            hist_counter = collections.Counter(history)
            pop = list(hist_counter.keys())
            wgt = list(hist_counter.values())
            trend_picks = random.choices(pop, weights=wgt, k=3) if pop else []
            
            # Random strategy
            random_picks = [f"{random.randint(0,99):02d}" for _ in range(3)]
            
            if target in trend_picks:
                trend_hits += 1
            if target in random_picks:
                random_hits += 1
        
        periods_tested = len(df_chrono) - start_idx - 10
        total_cost = periods_tested * cost_per_draw
        
        bt_col1, bt_col2 = st.columns(2)
        with bt_col1:
            st.metric("🔥 Trend Strategy", f"{trend_hits} wins", f"ROI: {((trend_hits * 2000 - total_cost) / total_cost * 100):.1f}%")
        with bt_col2:
            st.metric("🎲 Random Strategy", f"{random_hits} wins", f"ROI: {((random_hits * 2000 - total_cost) / total_cost * 100):.1f}%")
        
        # Conclusion
        diff = trend_hits - random_hits
        if abs(diff) <= 2:
            st.info("📊 **Conclusion**: Both strategies perform similarly. This confirms the lottery's random nature.")
        elif diff > 0:
            st.success(f"📊 **Conclusion**: Trend strategy slightly ahead (+{diff}), but could be luck.")
        else:
            st.warning(f"📊 **Conclusion**: Random strategy won (+{-diff})! Chasing hot numbers doesn't always work.")

# -----------------------------------------------
# Module 5: Monte Carlo Simulation (蒙特卡洛模拟)
# -----------------------------------------------
st.divider()
st.subheader("🎰 Monte Carlo Simulation")
st.markdown("*Large-scale random sampling simulation*")

mc_years = st.slider("Simulation Period (Years)", min_value=1, max_value=10, value=5, key="mc_years")
mc_tickets = st.slider("Tickets per Draw", min_value=1, max_value=10, value=1, key="mc_tickets")

if st.button("Run Monte Carlo"):
    sims = int(24 * mc_years)  # 24 draws per year
    total_cost = 0
    total_win = 0
    jackpot_hit = False
    wins_breakdown = {"2-digit": 0, "3-digit": 0, "other": 0, "jackpot": 0}
    
    for _ in range(sims):
        for _ in range(mc_tickets):
            total_cost += 80
            
            # 2-digit (1% chance)
            if random.random() < 0.01:
                total_win += 2000
                wins_breakdown["2-digit"] += 1
            
            # 3-digit (0.4% chance)
            if random.random() < 0.004:
                total_win += 4000
                wins_breakdown["3-digit"] += 1
            
            # Jackpot (1/1,000,000)
            if random.random() < 0.000001:
                total_win += 6000000
                wins_breakdown["jackpot"] += 1
                jackpot_hit = True
            
            # Other prizes (~0.017% combined)
            if random.random() < 0.00017:
                total_win += 30000
                wins_breakdown["other"] += 1
    
    net = total_win - total_cost
    
    mc_col1, mc_col2, mc_col3 = st.columns(3)
    with mc_col1:
        st.metric("Total Cost", f"{total_cost:,} THB")
    with mc_col2:
        st.metric("Total Winnings", f"{total_win:,} THB")
    with mc_col3:
        st.metric("Net Profit", f"{net:,} THB", delta=f"{(net/total_cost*100):.1f}%" if total_cost > 0 else "0%")
    
    st.markdown(f"**Wins**: 2-digit: {wins_breakdown['2-digit']} | 3-digit: {wins_breakdown['3-digit']} | Other: {wins_breakdown['other']} | Jackpot: {wins_breakdown['jackpot']}")
    
    if jackpot_hit:
        st.balloons()
        st.success("🤯 JACKPOT HIT! (This is extremely rare - don't expect this in real life!)")
    elif net > 0:
        st.success("💰 Profit! But remember, this is just simulation luck.")
    else:
        st.error("📉 Loss. Long-term, the house always wins.")

# -----------------------------------------------
# Module 6: Scientific Validation (科学有效性检验)
# -----------------------------------------------
st.divider()
st.subheader("🧪 Scientific Validation")
st.markdown("*Chi-Square test to verify lottery randomness*")

# Chi-Square Test on 2-digit numbers
all_2d_for_chi = [str(row['prize_2digits']).strip().zfill(2) for idx, row in df.iterrows() if str(row['prize_2digits']).strip().lower() != 'nan']
total_draws_chi = len(all_2d_for_chi)

if total_draws_chi > 0:
    expected_freq = total_draws_chi / 100.0
    from collections import Counter as ChiCounter
    chi_counter = ChiCounter(all_2d_for_chi)
    
    chi_square_stat = 0.0
    for i in range(100):
        num_str = f"{i:02d}"
        observed = chi_counter.get(num_str, 0)
        chi_square_stat += ((observed - expected_freq) ** 2) / expected_freq
    
    critical_value = 124.34  # df=99, p=0.05
    
    chi_col1, chi_col2 = st.columns(2)
    with chi_col1:
        st.metric("Sample Size", f"{total_draws_chi} draws")
        st.metric("Chi-Square (χ²)", f"{chi_square_stat:.2f}")
    with chi_col2:
        st.metric("Critical Value (p=0.05)", f"{critical_value}")
        if chi_square_stat < critical_value:
            st.success("✅ Fair: Random distribution (H₀ accepted)")
        else:
            st.warning("⚠️ Bias Detected")
    
    if chi_square_stat < critical_value:
        st.info("📊 **Conclusion**: The lottery is truly random. Historical patterns are just noise.")
    else:
        st.warning("📊 **Conclusion**: Statistical deviation detected. Could be sampling artifact or genuine bias.")

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