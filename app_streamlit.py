
import streamlit as st
import pandas as pd
import random
import collections
import os
import datetime

# ------------------------------------------------------------
# 🌍 多语言配置 / Multi-language Config
# ------------------------------------------------------------
LANG = {
    "ภาษาไทย": {
        "title": "🇹🇭 วิเคราะห์หวยไทย (AI)",
        "password_label": "กรุณาใส่รหัสผ่าน (Enter Password):",
        "password_error": "😕 รหัสผ่านผิด",
        "data_loaded": "💾 โหลดข้อมูลแล้ว",
        "data_total_fmt": " (ทั้งหมด {} งวด)",
        "data_latest": "งวดล่าสุด: ",
        "tab_trend": "🔥 เลขเด็ด (ตามสถิติ)",
        "tab_random": "🧪 เลขสุ่ม (คณิตศาสตร์)",
        "trend_desc": "แนะนำเลขที่ออกบ่อยในอดีต (Top Hits)",
        "random_desc": "สุ่มตัวเลขตามหลักความน่าจะเป็น (Pure Random)",
        "rec_label_trend": "เลขแนะนำ",
        "rec_label_radom": "เลขสุ่ม",
        "reason": "ออก {} ครั้ง",
        "reason_rnd": "สุ่มแท้จริง",
        "ev_title": "📊 ความจริงทางคณิตศาสตร์",
        "ev_desc": "ตารางแสดงมูลค่าจริงของสลากฯ เมื่อเทียบกับราคาขาย",
        "ev_col_prize": "รางวัล",
        "ev_col_rule": "กติกา",
        "ev_col_amount": "เงินรางวัล",
        "ev_col_prob": "โอกาส",
        "ev_col_value": "มูลค่าจริง",
        "ev_conclusion": "💡 บทสรุป",
        "ev_conclusion_text": "ราคาขาย 80 บาท แต่มูลค่าทางคณิตศาสตร์เพียง {:.2f} บาท\nทุกใบที่คุณซื้อ คือการขาดทุนทางทฤษฎี {:.2f} บาท",
        # Backtest
        "bt_title": "⏪ ทดสอบย้อนหลัง (Backtest)",
        "bt_years_label": "ย้อนหลังกี่ปี?",
        "bt_btn": "เริ่มทดสอบ",
        "bt_info_range": "ช่วงเวลา: {} ถึง {}",
        "bt_info_count": "จำนวนงวด: {} งวด",
        "bt_info_cost": "ทุน: ซื้อ 3 ชุด/งวด (ชุดละ 80 บาท)",
        "bt_strat_trend": "🔥 กลยุทธ์เลขเด็ด (Trend)",
        "bt_strat_rand": "🧪 กลยุทธ์สุ่ม (Random)",
        "bt_col_hits": "ถูกรางวัล",
        "bt_col_invest": "เงินลงทุน",
        "bt_col_return": "เงินรางวัล",
        "bt_col_net": "กำไร/ขาดทุน",
        "bt_col_roi": "ROI (%)",
        "bt_conclusion": "🧐 บทสรุปการทดสอบ",
        "bt_con_equal": "ทั้งสองกลยุทธ์ให้ผลลัพธ์ใกล้เคียงกัน ยืนยันว่าหวยเป็นเรื่องของดวง",
        "bt_con_trend": "กลยุทธ์เลขเด็ดทำได้ดีกว่าเล็กน้อย (อาจเป็นเพียงความบังเอิญ)",
        "bt_con_rand": "กลยุทธ์สุ่มทำได้ดีกว่า! แสดงว่าการเก็งเลขไม่ได้ผลเสมอไป",
        # Simulation
        "sim_title": "💰 จำลองความน่าจะเป็น (Monte Carlo)",
        "sim_desc": "จำลองการซื้อหวยด้วยความน่าจะเป็นทางคณิตศาสตร์ (รวมรางวัลที่ 1)",
        "sim_btn": "เริ่มจำลอง",
        "sim_result_label": "ผลลัพธ์จำลอง 5 ปี (ซื้อ 1 ใบ/งวด)",
        "sim_comment_loss": "💡 ความเห็น: ขาดทุนตามคาด การพนันมีความเสี่ยง",
        "sim_comment_win": "💡 ความเห็น: โชคดีมาก! (แต่เกิดขึ้นยาก)",
        "footer": "🔒 Private Access Only | 888"
    },
    "中文": {
        "title": "🇹🇭 泰国彩票智能决策",
        "password_label": "请输入访问密码:",
        "password_error": "😕 密码错误",
        "data_loaded": "💾 数据已加载",
        "data_total_fmt": " (共 {} 期)",
        "data_latest": "最新: ",
        "tab_trend": "🔥 趋势策略 (追热)",
        "tab_random": "🧪 随机策略 (防守)",
        "trend_desc": "基于历史出现频率最高的号码推荐",
        "random_desc": "完全数学随机推荐 (承认独立概率)",
        "rec_label_trend": "推荐",
        "rec_label_radom": "随机",
        "reason": "出现 {} 次",
        "reason_rnd": "纯随机",
        "ev_title": "📊 奖金结构与数学真相",
        "ev_desc": "这是彩票的真实价值表。",
        "ev_col_prize": "奖项",
        "ev_col_rule": "规则",
        "ev_col_amount": "奖金",
        "ev_col_prob": "中奖率",
        "ev_col_value": "贡献价值",
        "ev_conclusion": "💡 核心结论",
        "ev_conclusion_text": "一张售价 80 THB 的彩票，数学价值仅 {:.2f} THB。\n每买一张，理论亏损 {:.2f} THB。",
        # Backtest
        "bt_title": "⏪ 历史回测 (Backtest)",
        "bt_years_label": "回测过去多少年数据？",
        "bt_btn": "开始回测",
        "bt_info_range": "回测区间: {} 至 {}",
        "bt_info_count": "回测期数: {} 期",
        "bt_info_cost": "策略设定: 每期购买 3 注 2位数号码 (成本 240 THB)",
        "bt_strat_trend": "🔥 趋势策略 (Trend)",
        "bt_strat_rand": "🧪 随机策略 (Random)",
        "bt_col_hits": "中奖次数",
        "bt_col_invest": "总投入",
        "bt_col_return": "总回报",
        "bt_col_net": "净盈亏",
        "bt_col_roi": "回报率 (ROI)",
        "bt_conclusion": "🧐 回测结论",
        "bt_con_equal": "两种策略表现几乎一致！这再次验证了彩票的随机游走性质。",
        "bt_con_trend": "趋势策略略微领先，但这可能仅仅是运气波动。",
        "bt_con_rand": "随机策略竟然反超了！说明追热号并不总是有效。",
        # Simulation
        "sim_title": "💰 纯概率模拟 (含头奖)",
        "sim_desc": "基于数学期望的 Monte Carlo 模拟，包含从一等奖到小奖的所有概率。",
        "sim_btn": "运行概率模拟",
        "sim_result_label": "模拟结果 (每期买1张，持续5年)",
        "sim_comment_loss": "💡 点评: 长期参与大概率是亏损的，请保持娱乐心态。",
        "sim_comment_win": "💡 点评: 运气不错，小赚一笔！主要是靠运气。",
        "footer": "🔒 私有部署 | 仅限授权访问"
    },
    "English": {
        "title": "🇹🇭 Thai Lottery Insight",
        "password_label": "Enter Password:",
        "password_error": "😕 Incorrect Password",
        "data_loaded": "💾 Data Loaded",
        "data_total_fmt": " (Total {})",
        "data_latest": "Latest: ",
        "tab_trend": "🔥 Trend Pick",
        "tab_random": "🧪 Random Pick",
        "trend_desc": "Based on historical frequency (Hot Numbers)",
        "random_desc": "Pure mathematical random selection",
        "rec_label_trend": "Pick",
        "rec_label_radom": "Rand",
        "reason": "Hit {} times",
        "reason_rnd": "Random",
        "ev_title": "📊 Math & Truth",
        "ev_desc": "The real mathematical value of a lottery ticket.",
        "ev_col_prize": "Prize",
        "ev_col_rule": "Rule",
        "ev_col_amount": "Amount",
        "ev_col_prob": "Prob.",
        "ev_col_value": "Value",
        "ev_conclusion": "💡 Conclusion",
        "ev_conclusion_text": "Ticket Price: 80 THB, Real Value: {:.2f} THB.\nTheoretical loss per ticket: {:.2f} THB.",
        # Backtest
        "bt_title": "⏪ Historical Backtest",
        "bt_years_label": "Years to backtest:",
        "bt_btn": "Start Backtest",
        "bt_info_range": "Range: {} to {}",
        "bt_info_count": "Draws: {}",
        "bt_info_cost": "Strategy: Buy 3 tickets (2-digits) per draw.",
        "bt_strat_trend": "🔥 Trend Strategy",
        "bt_strat_rand": "🧪 Random Strategy",
        "bt_col_hits": "Hits",
        "bt_col_invest": "Invest",
        "bt_col_return": "Return",
        "bt_col_net": "Net",
        "bt_col_roi": "ROI",
        "bt_conclusion": "🧐 Conclusion",
        "bt_con_equal": "Both strategies performed similarly. Random walk confirmed.",
        "bt_con_trend": "Trend strategy performed slightly better (likely luck).",
        "bt_con_rand": "Random strategy outperformed Trend! Hot numbers don't guarantee wins.",
        # Simulation
        "sim_title": "💰 Monte Carlo Simulation",
        "sim_desc": "Pure probability simulation including Jackpot chances.",
        "sim_btn": "Run Simulation",
        "sim_result_label": "Simulation (1 ticket/draw for 5 years)",
        "sim_comment_loss": "💡 Comment: Long term loss is expected.",
        "sim_comment_win": "💡 Comment: Super Lucky! But rare.",
        "footer": "🔒 Private Access Only"
    }
}

# ------------------------------------------------------------
# 页面配置 (Page Config)
# ------------------------------------------------------------
st.set_page_config(page_title="Thai Lottery", page_icon="🎰", layout="centered")

if "lang_choice" not in st.session_state:
    st.session_state["lang_choice"] = "ภาษาไทย"

# Top language selector
c1, c2 = st.columns([3, 1])
with c2:
    options = ["ภาษาไทย", "中文", "English"]
    lang_opt = st.selectbox("Language", options, label_visibility="collapsed")
    st.session_state["lang_choice"] = lang_opt

T = LANG[st.session_state["lang_choice"]]

# ------------------------------------------------------------
# 🔐 安全验证 (Security)
# ------------------------------------------------------------
def check_password():
    def password_entered():
        if st.session_state["password"] == "888":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input(T["password_label"], type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input(T["password_label"], type="password", on_change=password_entered, key="password")
        st.error(T["password_error"])
        return False
    else:
        return True

if not check_password():
    st.stop()

# ------------------------------------------------------------
# 主标题
# ------------------------------------------------------------
st.title(T["title"])

# 读取数据
@st.cache_data
def load_data():
    if not os.path.exists("historical_data.csv"):
        return pd.DataFrame()
    df = pd.read_csv("historical_data.csv")
    def parse_dt(d):
        try: return pd.to_datetime(d, format="%m/%d/%Y")
        except: 
            try: return pd.to_datetime(d, format="%Y-%m-%d")
            except: return pd.NaT
    df['date_obj'] = df['date'].apply(parse_dt)
    df = df.sort_values('date_obj', ascending=False)
    # Ensure proper reset index for iteration later
    df = df.reset_index(drop=True)
    return df

df = load_data()

if df.empty:
    st.error("No Data Found.")
    st.stop()

# 数据加载显示 (本地化)
total_str = T["data_total_fmt"].format(len(df))
st.success(f"{T['data_loaded']}{total_str}")
st.text(f"{T['data_latest']} {df.iloc[0]['date']}")

# 统计频率
all_2digits = []
for idx, row in df.iterrows():
    val = str(row['prize_2digits']).strip()
    if len(val) == 1: val = "0" + val
    if val and val.lower() != 'nan':
        all_2digits.append(val)
counter_2 = collections.Counter(all_2digits)

# -----------------------------------------------
# 1. 选号助手 (Smart Picker)
# -----------------------------------------------
st.divider()
tab1, tab2 = st.tabs([T["tab_trend"], T["tab_random"]])

with tab1:
    st.write(T["trend_desc"])
    cols = st.columns(3)
    population = list(counter_2.keys())
    weights = list(counter_2.values())
    if population:
        trend_picks = random.choices(population, weights=weights, k=3)
        for i, num in enumerate(trend_picks):
            count = counter_2[num]
            cols[i].metric(label=f"{T['rec_label_trend']} {i+1}", value=num, delta=T["reason"].format(count))

with tab2:
    st.write(T["random_desc"])
    cols = st.columns(3)
    rand_picks = [f"{random.randint(0,99):02d}" for _ in range(3)]
    for i, num in enumerate(rand_picks):
        cols[i].metric(label=f"{T['rec_label_radom']} {i+1}", value=num)

# -----------------------------------------------
# 2. 数学表 (Math Table)
# -----------------------------------------------
st.divider()
st.subheader(T["ev_title"])
st.markdown(T["ev_desc"])

if st.session_state["lang_choice"] == "中文":
    p_names = ["一等奖", "二等奖", "三等奖", "四等奖", "五等奖", "邻近奖", "前/后三", "末两位"]
    p_rules = ["6位全中", "6位", "6位", "6位", "6位", "头奖±1", "前3或后3", "末2位"]
elif st.session_state["lang_choice"] == "ภาษาไทย":
    p_names = ["รางวัลที่ 1", "รางวัลที่ 2", "รางวัลที่ 3", "รางวัลที่ 4", "รางวัลที่ 5", "ข้างเคียง", "3 ตัวหน้า/หลัง", "2 ตัวท้าย"]
    p_rules = ["ตรงทุกตัว", "6 หลัก", "6 หลัก", "6 หลัก", "6 หลัก", "ใกล้เคียง", "3 ตัว", "2 ตัว"]
else:
    p_names = ["1st Prize", "2nd Prize", "3rd Prize", "4th Prize", "5th Prize", "Side Prize", "3 Digits", "2 Digits"]
    p_rules = ["All Match", "6 Digits", "6 Digits", "6 Digits", "6 Digits", "+/- 1", "Prefix/Suffix", "Last 2"]

data_ev = {
    T["ev_col_prize"]: p_names,
    T["ev_col_amount"]: [6000000, 200000, 80000, 40000, 20000, 100000, 4000, 2000],
    T["ev_col_prob"]: [1, 5, 10, 50, 100, 2, 4000, 10000], 
    T["ev_col_rule"]: p_rules
}
df_ev = pd.DataFrame(data_ev)
df_ev[T["ev_col_value"]] = df_ev[T["ev_col_amount"]] * (df_ev[T["ev_col_prob"]] / 1000000)
df_ev[T["ev_col_prob"]] = df_ev[T["ev_col_prob"]].apply(lambda x: f"1/{int(1000000/x):,}")

st.dataframe(df_ev[[T["ev_col_prize"], T["ev_col_rule"], T["ev_col_amount"], T["ev_col_prob"], T["ev_col_value"]]], hide_index=True)

total_ev = df_ev[T["ev_col_value"]].sum()
loss = 80 - total_ev
st.info(T["ev_conclusion_text"].format(total_ev, loss))

# -----------------------------------------------
# 3. 详细历史回测 (Detailed Backtest)
# -----------------------------------------------
st.divider()
st.subheader(T["bt_title"])

years_back = st.slider(T["bt_years_label"], 1, 10, 5)

if st.button(T["bt_btn"]):
    with st.spinner("Simulating... / กำลังคำนวณ..."):
        # Prepare data (Oldest to Newest)
        chron_data = df.sort_values('date_obj', ascending=True)
        latest_date = chron_data.iloc[-1]['date_obj']
        start_date = latest_date - pd.DateOffset(years=years_back)
        
        test_set = chron_data[chron_data['date_obj'] >= start_date]
        
        st.write(T["bt_info_range"].format(start_date.strftime('%Y-%m-%d'), latest_date.strftime('%Y-%m-%d')))
        st.write(T["bt_info_count"].format(len(test_set)))
        st.caption(T["bt_info_cost"])
        
        results = {
            "Trend": {"cost": 0, "win": 0, "hits": 0},
            "Random": {"cost": 0, "win": 0, "hits": 0}
        }
        
        # Simulate logic (Same as CLI)
        current_data_pool = chron_data[chron_data['date_obj'] < start_date].copy()
        for idx, row in test_set.iterrows():
            target_val = str(row['prize_2digits']).strip()
            if len(target_val) == 1: target_val = "0" + target_val
            
            # Update history pool (Add previous draw)
            # Actually for rolling, we need data available BEFORE this draw
            # For simplicity, we assume we update pool dynamically
            
            # 1. Calc Trend
            pool_vals = []
            for _, r in current_data_pool.iterrows():
                v = str(r['prize_2digits']).strip()
                if len(v) == 1: v = "0" + v
                if v and v.lower() != 'nan': pool_vals.append(v)
            
            if pool_vals:
                ctr = collections.Counter(pool_vals)
                picks_trend = random.choices(list(ctr.keys()), weights=list(ctr.values()), k=3)
            else:
                picks_trend = [f"{random.randint(0,99):02d}" for _ in range(3)]
            
            picks_rand = [f"{random.randint(0,99):02d}" for _ in range(3)]
            
            # Check Win
            cost_per_draw = 240 # 3 tickets * 80
            results["Trend"]["cost"] += cost_per_draw
            results["Random"]["cost"] += cost_per_draw
            
            if target_val in picks_trend:
                results["Trend"]["win"] += 2000
                results["Trend"]["hits"] += 1
            if target_val in picks_rand:
                results["Random"]["win"] += 2000
                results["Random"]["hits"] += 1
            
            # Add current draw to pool for NEXT round
            current_data_pool = pd.concat([current_data_pool, pd.DataFrame([row])])

        # Show Results Table
        res_data = []
        for strat, name in [("Trend", T["bt_strat_trend"]), ("Random", T["bt_strat_rand"])]:
            r = results[strat]
            net = r["win"] - r["cost"]
            roi = (net / r["cost"]) * 100 if r["cost"] > 0 else 0
            res_data.append({
                "Strategy": name,
                T["bt_col_hits"]: f"{r['hits']} / {len(test_set)}",
                T["bt_col_invest"]: f"{r['cost']:,}",
                T["bt_col_return"]: f"{r['win']:,}",
                T["bt_col_net"]: f"{net:,}",
                T["bt_col_roi"]: f"{roi:.2f}%"
            })
        
        st.table(pd.DataFrame(res_data).set_index("Strategy"))
        
        # Conclusion
        diff = results["Trend"]["hits"] - results["Random"]["hits"]
        st.subheader(T["bt_conclusion"])
        if abs(diff) <= 2:
            st.info(T["bt_con_equal"])
        elif diff > 0:
            st.warning(T["bt_con_trend"])
        else:
            st.error(T["bt_con_rand"])

# -----------------------------------------------
# 4. 纯概率模拟 (Monte Carlo with Jackpot)
# -----------------------------------------------
st.divider()
st.subheader(T["sim_title"])
st.markdown(T["sim_desc"])

if st.button(T["sim_btn"]):
    st.write(T["sim_result_label"])
    
    simulations = 120 # 5 years
    ticket_price = 80
    total_cost = 0
    total_win = 0
    jackpot_hit = False
    
    progress_bar = st.progress(0)
    
    for i in range(simulations):
        total_cost += ticket_price
        # Check prizes independently
        current_win = 0
        # 2 Digits (1/100)
        if random.random() < 0.01: current_win += 2000
        # 3 Digits (4/1000)
        if random.random() < 0.004: current_win += 4000
        # Jackpot (1/1M)
        if random.random() < 0.000001: 
            current_win += 6000000
            jackpot_hit = True
        # Small prizes approx
        if random.random() < 0.00016: current_win += 20000 # Approx avg
            
        total_win += current_win
        progress_bar.progress((i + 1) / simulations)
        
    net_profit = total_win - total_cost
    
    c1, c2, c3 = st.columns(3)
    c1.metric(T["sim_total_cost"], f"{total_cost} THB")
    c2.metric(T["sim_total_return"], f"{total_win} THB")
    c3.metric(T["sim_net"], f"{net_profit} THB", delta=net_profit)
    
    if jackpot_hit:
        st.balloons()
        st.success("🤯 JACKPOT!!! " + T["sim_win_msg"])
    elif net_profit > 0:
        st.success(T["sim_comment_win"])
    else:
        st.warning(T["sim_comment_loss"])

st.markdown("---")
st.caption(T["footer"])
