import streamlit as st
import pandas as pd
import random
import collections
import os
import scipy.stats as stats
import datetime
import ast
import requests
import re
import time

import firebase_admin
from firebase_admin import auth, firestore

# --- Integrate Main Backend ---
from lottery_predictor import load_data, save_new_draw, db, COLLECTION_NAME

def check_subscription():
    if st.session_state.get('authenticated'):
        return True

    token = st.query_params.get("token")
    if not token:
        st.error("⚠️ 访问凭证缺失：请确认您已通过用户中心跳转。")
        st.stop()

    try:
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token['uid']
        user_ref = db.collection('subscribers').document(uid)
        doc = user_ref.get()
        
        if doc.exists and doc.to_dict().get('status') == 'active':
            st.session_state['authenticated'] = True
            return True
        else:
            st.error("🔒 您的订阅当前处于非活跃状态。")
            st.stop()
    except Exception:
        st.error("⛔ 认证令牌无效或已过期。")
        st.stop()

# Enforce Auth
check_subscription()

# ------------------------------------------------------------
# 🎨 界面样式
# ------------------------------------------------------------
st.set_page_config(page_title="Thai Lottery AI", page_icon="💰", layout="centered")

def clean_html(html_str):
    return "\n".join([line.strip() for line in html_str.split("\n")])

st.markdown(clean_html("""
<style>
.block-container { padding-top: 2rem !important; padding-bottom: 2rem !important; }
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.section-header { font-size: 1.3em; font-weight: 600; margin-bottom: 0; }
.custom-metric-card { width: 98%; background-color: #f9f9f9; padding: 10px; border-radius: 8px; border: 1px solid #eee; text-align: left; }
.metric-label { font-size: 0.8em; color: #666; margin-bottom: 2px; }
.metric-value { font-size: 1.8em; font-weight: 700; color: #333; line-height: 1.2; }
.metric-delta { font-size: 0.8em; color: #28a745; font-weight: 500; }
.grid-header { font-size: 1.0em; font-weight: 600; color: #333; }
.latest-draw-container { background-color: #fff; border: 1px solid #ddd; border-radius: 12px; padding: 15px; text-align: center; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
.latest-date { font-size: 1.0em; color: #555; margin-bottom: 15px; font-weight: 500; }
.prize-1st-box { margin-bottom: 20px; }
.result-number-1st { font-size: 2.5em; font-weight: 800; color: #173858; letter-spacing: 3px; }
.result-title { font-size: 0.9em; color: #173858; margin-bottom: 2px; }
.sub-prizes-row { display: flex; justify-content: space-around; flex-wrap: wrap; border-top: 1px solid #eee; padding-top: 15px; }
.sub-prize-item { text-align: center; min-width: 30%; margin-bottom: 10px; }
.sub-number { font-size: 1.4em; font-weight: 700; color: #173858; letter-spacing: 1px; }
.sub-number-2d { font-size: 1.6em; font-weight: 800; color: #173858; }
</style>
"""), unsafe_allow_html=True)

# ------------------------------------------------------------
# 🌍 Config (Fixed Dictionary)
# ------------------------------------------------------------
LANG = {
    "ภาษาไทย": {
        "title": "💰 วิเคราะห์หวยไทย (AI)",
        "data_latest": "งวดประจำวันที่ {}",
        "trend_tab": "🔥 แนวโน้ม",
        "random_tab": "🧪 สุ่ม",
        "hot_tab": "📊 ท็อปฮิต",
        "momentum_desc": "อ้างอิงจากสถิติที่ผ่านมา",
        "entropy_desc": "การสุ่มตัวเลขทางคณิตศาสตร์",
        "freq_desc": "ตัวเลขที่ออกบ่อยที่สุด",
        "two_digits": "2 ตัว",
        "three_digits": "3 ตัว",
        "math_truth": "📊 ความจริงเชิงสถิติ",
        "math_desc": "โอกาสถูกรางวัลและมูลค่าทางคณิตศาสตร์",
        "p1": "รางวัลที่ 1", "p3_pre": "3 ตัวหน้า", "p3_sub": "3 ตัวท้าย", "p2d": "เลขท้าย 2 ตัว",
        "summary": "สรุป:", "ticket_cost": "ต้นทุนต่อใบ", "expected_return": "มูลค่าเฉลี่ย", "expected_loss": "ส่วนต่างขาดทุนเฉลี่ย",
        "backtest_title": "⏪ ย้อนรอยประวัติศาสตร์", "backtest_desc": "จำลองการซื้อหวยในอดีต", "run_backtest": "เริ่มจำลอง",
        "monte_carlo": "🎰 จำลองเหตุการณ์ (Monte Carlo)", "total_cost": "ทุนรวม", "total_win": "รางวัลรวม", "net_profit": "กำไร/ขาดทุน",
        "validation_title": "🧪 ทดสอบความเป็นธรรม", "fair_stat": "✅ เป็นศูนย์กลาง", "bias_stat": "⚠️ มีความเอนเอียง",
        "support_creator": "☕ สนับสนุนผู้พัฒนา"
    },
    "中文": {
        "title": "💰 泰国彩票AI智能策略",
        "data_latest": "最新开奖日期: {}",
        "trend_tab": "🔥 趋势",
        "random_tab": "🧪 随机",
        "hot_tab": "📊 热门",
        "momentum_desc": "基于历史动量分析",
        "entropy_desc": "纯数学随机熵",
        "freq_desc": "最频繁出现的数字",
        "two_digits": "2 位数",
        "three_digits": "3 位数",
        "math_truth": "📊 数学真相概率表",
        "math_desc": "官方中奖赔率及数学期望值",
        "p1": "一等奖", "p3_pre": "前3位", "p3_sub": "后3位", "p2d": "末2位",
        "summary": "总结:", "ticket_cost": "彩票成本", "expected_return": "预期回报", "expected_loss": "单张平均亏损",
        "backtest_title": "⏪ 历史模拟回测", "backtest_desc": "模拟历史区间策略效果", "run_backtest": "开始回测",
        "monte_carlo": "🎰 蒙特卡洛模拟", "total_cost": "总投入", "total_win": "总奖金", "net_profit": "净盈亏",
        "validation_title": "🧪 科学有效性检验", "fair_stat": "✅ 分布均匀", "bias_stat": "⚠️ 发现显著偏差",
        "support_creator": "☕ 支持开发者"
    },
    "English": {
        "title": "💰 Thai Lottery AI Strategy",
        "data_latest": "Draw Date: {}",
        "trend_tab": "🔥 Trend",
        "random_tab": "🧪 Random",
        "hot_tab": "📊 Hot",
        "momentum_desc": "Based on historical momentum",
        "entropy_desc": "Pure Entropy (Mathematical)",
        "freq_desc": "Most Frequent Numbers",
        "two_digits": "2 Digits",
        "three_digits": "3 Digits",
        "math_truth": "📊 Mathematical Truth",
        "math_desc": "Official probabilities and expected values",
        "p1": "1st Prize", "p3_pre": "3 Prefix", "p3_sub": "3 Suffix", "p2d": "2 Digits",
        "summary": "Summary:", "ticket_cost": "Ticket Cost", "expected_return": "Expected Return", "expected_loss": "Expected Loss",
        "backtest_title": "⏪ Historical Backtest", "backtest_desc": "Simulate playing with historical data", "run_backtest": "Run Backtest",
        "monte_carlo": "🎰 Monte Carlo Simulation", "total_cost": "Total Cost", "total_win": "Total Winnings", "net_profit": "Net Profit",
        "validation_title": "🧪 Scientific Validation", "fair_stat": "✅ Fair", "bias_stat": "⚠️ Bias Detected",
        "support_creator": "☕ Support Creator"
    }
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

def format_display_date(dt_obj):
    if pd.isna(dt_obj): return "-"
    return dt_obj.strftime("%d %b %Y")

# ------------------------------------------------------------
# 🤖 Data Pipeline (Cloud Native with Auto-Sync)
# ------------------------------------------------------------
@st.cache_data(ttl=600)
def fetch_db_data():
    # 只缓存纯粹的数据库读取，把爬虫动作剥离出去
    return load_data()

def get_ui_data():
    from glo_scraper import GLOScraper
    from lottery_predictor import save_new_draw
    
    raw_data = fetch_db_data()
    df = pd.DataFrame(raw_data) if raw_data else pd.DataFrame()
    
    if df.empty:
        return df
    
    # 强悍的时间解析：自动适应各种奇葩日期格式，防止新数据沉底
    def parse_dt(d):
        try: return pd.to_datetime(d, errors='coerce')
        except: return pd.NaT
        
    df['date_obj'] = df['date'].apply(parse_dt)
    df = df.sort_values('date_obj', ascending=False).reset_index(drop=True)
    
    latest_date = df.iloc[0]['date_obj']
    today = pd.Timestamp.today()
    
    # --- Auto-Sync 逻辑（移出缓存区，确保每次刷新都能真实判定） ---
    if pd.notna(latest_date) and (today.date() - latest_date.date()).days >= 1:
        status_box = st.empty()
        status_box.info("🔄 检测到新数据，正在请求官方接口...")
        
        try:
            scraper = GLOScraper()
            new_draw = scraper.fetch_latest_results()
            
            if new_draw and new_draw.get('prize_1st'):
                # 强制规范化新数据的日期，确保它永远排在最上面
                if '-' not in str(new_draw['date']) or len(str(new_draw['date'])) != 10:
                    new_draw['date'] = today.strftime("%Y-%m-%d")
                    
                save_new_draw(None, new_draw)
                status_box.success(f"✅ 官方数据同步成功！最新一期: {new_draw['date']}")
                time.sleep(1.5)
                st.cache_data.clear() # 炸毁旧数据的缓存
                st.rerun() # 强制刷新网页，呈现最新结果
            else:
                status_box.warning("⚠️ 官方接口暂无最新数据，将继续使用现有数据。")
                time.sleep(2)
                status_box.empty() # 隐藏提示框，不影响用户查看旧数据
        except Exception as e:
            status_box.error(f"❌ 抓取过程出错: {str(e)}")
            time.sleep(3)
            status_box.empty()
            
    return df

df = get_ui_data()

if df.empty:
    st.error("No Data Found in Cloud Database.")
    st.stop()

# ------------------------------------------------------------
# 🎯 Main UI Logic
# ------------------------------------------------------------
st.markdown(clean_html(f"<h1 style='text-align: center; color: #E63946; font-size: 1.8em; margin-bottom: 0px;'>{T['title']}</h1><hr style='margin-top: 5px; margin-bottom: 15px;'>"), unsafe_allow_html=True)

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
<div class="latest-draw-container">
<div class="latest-date">{T['data_latest'].format(format_display_date(latest['date_obj']))}</div>
<div class="prize-1st-box">
<div class="result-title">{T["p1"]}</div>
<div class="result-number-1st">{latest_1st}</div>
</div>
<div class="sub-prizes-row">
<div class="sub-prize-item"><div class="result-title">{T["p3_pre"]}</div><div class="sub-number">{prefix_str}</div></div>
<div class="sub-prize-item"><div class="result-title">{T["p3_sub"]}</div><div class="sub-number">{suffix_str}</div></div>
<div class="sub-prize-item"><div class="result-title">{T["p2d"]}</div><div class="sub-number sub-number-2d">{latest_2d}</div></div>
</div>
<div style="margin-top: 20px; text-align: center; display: flex; justify-content: center; gap: 10px;">
    <a href="https://www.glo.or.th/home-page" target="_blank" style="text-decoration: none;">
        <button style="background-color: #173858; color: white; border: none; padding: 10px 20px; border-radius: 20px; cursor: pointer; font-weight: 600; font-size: 0.9em; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            🏛️ 官方主页
        </button>
    </a>
    {f'''<a href="{latest.get('official_chart_url')}" target="_blank" style="text-decoration: none;">
        <button style="background-color: #E63946; color: white; border: none; padding: 10px 20px; border-radius: 20px; cursor: pointer; font-weight: 600; font-size: 0.9em; box-shadow: 0 4px 6px rgba(230, 57, 70, 0.2);">
            📜 查看基因图谱 (Official Chart)
        </button>
    </a>''' if latest.get('official_chart_url') else ""}
</div>
</div>

"""), unsafe_allow_html=True)

# ------------------------------------------------------------
# 📈 Tabs & Analysis
# ------------------------------------------------------------
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
                        item_str = str(item).strip()
                        if item_str.isdigit() and 1 <= len(item_str) <= 3:
                            all_3digits.append(item_str.zfill(3))
            except: pass

counter_2 = collections.Counter(all_2digits)
counter_3 = collections.Counter(all_3digits)

tab1, tab2, tab3 = st.tabs([T["trend_tab"], T["random_tab"], T["hot_tab"]])

def show_picker_grid_card(picks_2, picks_3, reasons_2, reasons_3, desc, mode_label):
    st.markdown(f"<div style='margin-bottom:15px; font-size:0.95em; color:#444;'>{desc}</div>", unsafe_allow_html=True)
    l_html = f"""<div style="flex:1; margin-right:5px;"><div class='grid-header'>{T["two_digits"]}</div>"""
    for i in range(3):
        p = picks_2[i] if i < len(picks_2) else "--"
        r = reasons_2[i] if i < len(reasons_2) else ""
        l_html += f"""<div class="custom-metric-card" style="width:100%; margin-bottom:10px;"><div class="metric-label">{mode_label} #{i+1}</div><div class="metric-value">{p}</div>{f"<div class='metric-delta'>↑ {r}</div>" if r else ""}</div>"""
    r_html = f"""<div style="flex:1; margin-left:5px;"><div class='grid-header'>{T["three_digits"]}</div>"""
    for i in range(3):
        p = picks_3[i] if i < len(picks_3) else "--"
        r = reasons_3[i] if i < len(reasons_3) else ""
        r_html += f"""<div class="custom-metric-card" style="width:100%; margin-bottom:10px;"><div class="metric-label">{mode_label} #{i+1}</div><div class="metric-value">{p}</div>{f"<div class='metric-delta'>↑ {r}</div>" if r else ""}</div>"""
    st.markdown(f"""<div style="display:flex; flex-direction:row; justify-content:space-between;">{l_html}</div>{r_html}</div>""", unsafe_allow_html=True)

with tab1:
    pop2 = list(counter_2.keys())
    w2 = list(counter_2.values())
    t2 = random.choices(pop2, weights=w2, k=3) if pop2 else ["--"]*3
    pop3 = list(counter_3.keys())
    w3 = list(counter_3.values())
    t3 = random.choices(pop3, weights=w3, k=3) if pop3 else ["--"]*3
    show_picker_grid_card(t2, t3, [f"{counter_2.get(p,0)} hits" for p in t2], [f"{counter_3.get(p,0)} hits" for p in t3], T["momentum_desc"], "Trend")

with tab2:
    show_picker_grid_card([f"{random.randint(0,99):02d}" for _ in range(3)], [f"{random.randint(0,999):03d}" for _ in range(3)], ["Rand"]*3, ["Rand"]*3, T["entropy_desc"], "Rand")

with tab3:
    h2 = [k for k,v in counter_2.most_common(3)]
    h3 = [k for k,v in counter_3.most_common(3)]
    show_picker_grid_card(h2, h3, [f"{counter_2.get(k,0)} hits" for k in h2], [f"{counter_3.get(k,0)} hits" for k in h3], T["freq_desc"], "Hot")

# ------------------------------------------------------------
# 📊 Mathematical Truth & Simulation (Simplified for UX)
# ------------------------------------------------------------
st.divider()
st.subheader(T["math_truth"])
st.markdown(f"*{T['math_desc']}*")
p_data = [
    {"奖项 (Prize)": "1st Prize", "中奖概率 (Probability)": "1/1,000,000", "奖金 (Payout)": "6,000,000 THB"},
    {"奖项 (Prize)": "3-Digit (F/B)", "中奖概率 (Probability)": "4,000/1,000,000", "奖金 (Payout)": "4,000 THB"},
    {"奖项 (Prize)": "2-Digit (Last)", "中奖概率 (Probability)": "10,000/1,000,000", "奖金 (Payout)": "2,000 THB"},
]
st.dataframe(pd.DataFrame(p_data), use_container_width=True, hide_index=True)

# ------------------------------------------------------------
# 🎰 Monte Carlo Simulation (新加入的模拟模块)
# ------------------------------------------------------------
st.divider()
st.subheader(T.get("monte_carlo", "🎰 蒙特卡洛模拟 (Monte Carlo)"))
st.markdown("*假设每期坚持买 1 张，持续 5 年 (120期)，看看完全靠运气的长期回报：*")

# 模拟参数
simulations = 120
ticket_price = 80
total_cost = simulations * ticket_price
total_win = 0
jackpot_hit = False

# 运行数学模拟引擎
for _ in range(simulations):
    if random.random() < (10000 / 1000000): total_win += 2000
    if random.random() < (4000 / 1000000): total_win += 4000
    if random.random() < (1 / 1000000): 
        total_win += 6000000
        jackpot_hit = True
    # 其他小奖综合概率
    other_prob = (5+10+50+100+2) / 1000000
    if random.random() < other_prob: total_win += 30000

net_profit = total_win - total_cost

# 渲染精美的数据卡片
m1, m2, m3 = st.columns(3)
m1.metric("总投入 (Cost)", f"฿{total_cost}")
m2.metric("总奖金 (Win)", f"฿{total_win}")
m3.metric("净盈亏 (Net Profit)", f"฿{net_profit}", delta=net_profit)

# 动态点评
if jackpot_hit:
    st.success("🤯 天呐！模拟中竟然中了一等奖 (600万)！这属于极度罕见的幸存者偏差，请勿当真！")
elif net_profit > 0:
    st.info("💡 运气不错，小赚一笔！但这主要是靠运气而非策略。")
else:
    st.warning("💡 长期看依然是亏损的。大数据证明：请将彩票视为【娱乐消费】而非投资。")

# ------------------------------------------------------------
# ☕ Footer
# ------------------------------------------------------------
st.divider()
st.markdown(f"<div style='text-align: center; margin-top: 20px;'><h3>{T['support_creator']}</h3><p style='color: #666;'>If you find this analysis useful</p></div>", unsafe_allow_html=True)
sc1, sc2 = st.columns(2)
with sc1: st.image("qr_alipay.jpg", caption="Alipay", use_container_width=True)
with sc2: st.image("qr_promptpay.jpg", caption="PromptPay", use_container_width=True)