
import streamlit as st
import pandas as pd
import random
import collections
import os
import scipy.stats as stats

# ------------------------------------------------------------
# 🌍 多语言配置 / Multi-language Config
# ------------------------------------------------------------
LANG = {
    "ภาษาไทย": {
        "title": "💰 วิเคราะห์หวยไทย (AI)",
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
        "ev_col_amount": "เงิน(บาท)", # Shortened
        "ev_col_prob": "โอกาส",
        "ev_col_value": "มูลค่า",     # Shortened
        "ev_conclusion": "💡 บทสรุป",
        "ev_conclusion_text": "ราคาขาย 80 บาท แต่มูลค่าทางคณิตศาสตร์เพียง {:.2f} บาท\nทุกใบที่คุณซื้อ คือการขาดทุนทางทฤษฎี {:.2f} บาท",
        # Backtest
        "bt_title": "⏪ ทดสอบย้อนหลัง (Backtest)",
        "bt_years_label": "ย้อนหลังกี่ปี?",
        "bt_btn": "เริ่มทดสอบ",
        "bt_header_info": "📋 ข้อมูลการทดสอบ",
        "bt_info_range": "• ช่วงเวลา: {} ถึง {}",
        "bt_info_count": "• จำนวนงวด: {} งวด",
        "bt_info_cfg": "⚙️ การตั้งค่า: ซื้อ 3 ชุด/งวด (เลขท้าย 2 ตัว)",
        "bt_info_cost_desc": "• ต้นทุนต่องวด: 240 บาท \n• รางวัลหากถูก: 2,000 บาท",
        "bt_strat_trend": "🔥 กลยุทธ์เลขเด็ด (Trend)",
        "bt_strat_rand": "🧪 กลยุทธ์สุ่ม (Random)",
        "bt_lbl_hits": "ถูกรางวัล:",
        "bt_lbl_invest": "เงินลงทุน:",
        "bt_lbl_return": "เงินรางวัล:",
        "bt_lbl_net": "กำไร/ขาดทุน:",
        "bt_lbl_roi": "ROI (%):",
        "bt_comparison": "🧐 บทสรุปเปรียบเทียบ:",
        "bt_con_equal": "ผลลัพธ์ใกล้เคียงกัน! ยืนยันว่า 'เลขเด็ด' ไม่มีผลจริง",
        "bt_con_trend": "เลขเด็ดชนะเล็กน้อย (อาจเป็นแค่ดวง)",
        "bt_con_rand": "เลขสุ่มชนะ! การเก็งเลขตามสถิติไม่ได้ช่วยให้ถูกรางวัลมากขึ้น",
        # Simulation
        "sim_title": "🎲 การจำลอง Monte Carlo",
        "sim_desc": "จำลองเหตุการณ์ในอนาคตด้วยความน่าจะเป็นทางคณิตศาสตร์",
        "sim_btn": "เริ่ม Monte Carlo",
        "sim_narration": "📝 สมมติฐาน: คุณซื้อหวยงวดละ 1 ใบ (80 บาท) ต่อเนื่องเป็นเวลา {} ปี...",
        "sim_lbl_cost": "ต้นทุนรวม:",
        "sim_lbl_return": "เงินรางวัลรวม:",
        "sim_lbl_net": "กำไรสุทธิ:",
        "sim_res_loss": "💡 ผลลัพธ์: ขาดทุน (เป็นปกติของการพนัน)",
        "sim_res_win": "💡 ผลลัพธ์: กำไร (คุณโชคดีมาก!)",
        "sim_jackpot": "🤯 แจ็กพอตแตก! (ถูกรางวัลที่ 1)",
        # Validation
        "val_title": "🧪 การทดสอบทางวิทยาศาสตร์ (Chi-Square)",
        "val_desc": "ตรวจสอบว่าการออกรางวัล 'สุ่ม' จริงหรือไม่?",
        "val_res_pass": "✅ ผลลัพธ์: กระจายตัวแบบสุ่ม (Uniform Distribution)",
        "val_exp_pass": "ตัวเลขทางสถิติยืนยันว่าไม่มี 'ล็อคเลข' หรือ 'รูปแบบ' ที่คาดเดาได้",
        "val_res_fail": "❌ ผลลัพธ์: มีความผิดปกติทางสถิติ",
        # Footer
        "final_rec": "💬 คำแนะนำสุดท้าย: หวยคือ 'ความบันเทิง' ไม่ใช่ 'การลงทุน'",
        "footer": "🔒 Private Access Only | 888"
    },
    "中文": {
        "title": "💰 泰国彩票智能决策",
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
        "ev_conclusion_text": "一张售价 80 THB 的彩票，数学价值仅 {:.2f} THB。\n每买一张，理论亏损 {:.2f} THB。",
        # Backtest
        "bt_title": "⏪ 历史回测 (Backtest)",
        "bt_years_label": "回测过去多少年数据？",
        "bt_btn": "开始回测",
        "bt_header_info": "📋 回测详情",
        "bt_info_range": "• 回测区间: {} 至 {}",
        "bt_info_count": "• 回测期数: {} 期",
        "bt_info_cfg": "⚙️ 策略设定: 每期买 3 注 (2位数)",
        "bt_info_cost_desc": "• 单期成本: 240 THB \n• 中奖奖金: 2,000 THB",
        "bt_strat_trend": "🔥 趋势策略 (Trend)",
        "bt_strat_rand": "🧪 随机策略 (Random)",
        "bt_lbl_hits": "中奖次数:",
        "bt_lbl_invest": "总投入:",
        "bt_lbl_return": "总回报:",
        "bt_lbl_net": "净盈亏:",
        "bt_lbl_roi": "回报率 (ROI):",
        "bt_comparison": "🧐 回测结论:",
        "bt_con_equal": "两种策略表现持平！再次验证了彩票的随机游走性质。",
        "bt_con_trend": "趋势策略略微领先 (可能是运气波动)。",
        "bt_con_rand": "随机策略竟然反超了！说明追热号并不总是有效。",
        # Simulation
        "sim_title": "🎲 蒙特卡洛模拟 (Monte Carlo)",
        "sim_desc": "基于数学期望的纯概率模拟 (含头奖)",
        "sim_btn": "运行模拟",
        "sim_narration": "📝 模拟假设: 您坚持买彩票 {} 年，每期仅买 1 张 (80 THB)...",
        "sim_lbl_cost": "总投入:",
        "sim_lbl_return": "总奖金:",
        "sim_lbl_net": "净盈亏:",
        "sim_res_loss": "💡 点评: 长期参与大概率亏损。请保持娱乐心态。",
        "sim_res_win": "💡 点评: 运气不错，小赚一笔！主要是靠运气。",
        "sim_jackpot": "🤯 天呐！中了头奖 (Jackpot)！",
        # Validation
        "val_title": "🧪 科学有效性检验 (Chi-Square)",
        "val_desc": "使用卡方检验 (Chi-Square Test) 验证号码分布是否随机。",
        "val_res_pass": "✅ 结论：分布均匀 (数据是随机的)",
        "val_exp_pass": "P值显示历史数据没有显著偏差。所谓的“热号”只是统计噪音。",
        "val_res_fail": "❌ 结论：发现统计异常",
        # Footer
        "final_rec": "💬 最终建议: 将彩票视为【消费】而非【投资】。",
        "footer": "🔒 私有部署 | 仅限授权访问"
    },
    "English": {
        "title": "💰 Thai Lottery Insight",
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
        "ev_conclusion_text": "Ticket Price: 80 THB, Real Value: {:.2f} THB.\nTheoretical loss per ticket: {:.2f} THB.",
        # Backtest
        "bt_title": "⏪ Historical Backtest",
        "bt_years_label": "Years to backtest:",
        "bt_btn": "Start Backtest",
        "bt_header_info": "📋 Backtest Details",
        "bt_info_range": "• Range: {} to {}",
        "bt_info_count": "• Draws: {}",
        "bt_info_cfg": "⚙️ Strategy: Buy 3 tickets (2-digits) per draw",
        "bt_info_cost_desc": "• Cost/Draw: 240 THB \n• Prize: 2,000 THB",
        "bt_strat_trend": "🔥 Trend Strategy",
        "bt_strat_rand": "🧪 Random Strategy",
        "bt_lbl_hits": "Hits:",
        "bt_lbl_invest": "Invest:",
        "bt_lbl_return": "Return:",
        "bt_lbl_net": "Net:",
        "bt_lbl_roi": "ROI (%):",
        "bt_comparison": "🧐 Conclusion:",
        "bt_con_equal": "Both strategies performed similarly.",
        "bt_con_trend": "Trend strategy performed slightly better (likely luck).",
        "bt_con_rand": "Random strategy outperformed Trend.",
        # Simulation
        "sim_title": "🎲 Monte Carlo Simulation",
        "sim_desc": "Pure probability simulation including Jackpot chances.",
        "sim_btn": "Run Simulation",
        "sim_narration": "📝 Assumption: Buying 1 ticket (80 THB) per draw for {} years...",
        "sim_lbl_cost": "Total Cost:",
        "sim_lbl_return": "Total Return:",
        "sim_lbl_net": "Net Profit:",
        "sim_res_loss": "💡 Comment: Long term loss is expected.",
        "sim_res_win": "💡 Comment: Lucky!",
        "sim_jackpot": "🤯 JACKPOT HIT!",
        # Validation
        "val_title": "🧪 Scientific Validation (Chi-Square)",
        "val_desc": "Testing for randomness using Chi-Square Goodness of Fit.",
        "val_res_pass": "✅ Result: Uniform Distribution",
        "val_exp_pass": "The data is truly random.",
        "val_res_fail": "❌ Result: Deviation detected",
        # Footer
        "final_rec": "💬 Final Advice: Treat lottery as consumption, not investment.",
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
# 展示 (移除 Rule 列以适应手机窄屏)
st.dataframe(
    df_ev[[T["ev_col_prize"], T["ev_col_amount"], T["ev_col_prob"], T["ev_col_value"]]], 
    hide_index=True,
    use_container_width=True
)

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
    with st.spinner("Calculating..."):
        chron_data = df.sort_values('date_obj', ascending=True)
        latest_date = chron_data.iloc[-1]['date_obj']
        start_date = latest_date - pd.DateOffset(years=years_back)
        test_set = chron_data[chron_data['date_obj'] >= start_date]
        
        # --- Context Info (Like CLI) ---
        st.markdown(f"**{T['bt_header_info']}**")
        st.text(T["bt_info_range"].format(start_date.strftime('%Y-%m-%d'), latest_date.strftime('%Y-%m-%d')) + "\n" +
                T["bt_info_count"].format(len(test_set)) + "\n" +
                T["bt_info_cfg"] + "\n" +
                T["bt_info_cost_desc"])
        
        results = {"Trend": {"cost": 0, "win": 0, "hits": 0}, "Random": {"cost": 0, "win": 0, "hits": 0}}
        current_pool = chron_data[chron_data['date_obj'] < start_date].copy()
        
        for idx, row in test_set.iterrows():
            target = str(row['prize_2digits']).strip().zfill(2)
            vals = [str(r['prize_2digits']).strip().zfill(2) for _, r in current_pool.iterrows()]
            vals = [v for v in vals if v.lower() != 'nan']
            
            if vals:
                c = collections.Counter(vals)
                picks_t = random.choices(list(c.keys()), weights=list(c.values()), k=3)
            else:
                picks_t = [f"{random.randint(0,99):02d}" for _ in range(3)]
                
            picks_r = [f"{random.randint(0,99):02d}" for _ in range(3)]
            
            results["Trend"]["cost"] += 240
            results["Random"]["cost"] += 240
            if target in picks_t: 
                results["Trend"]["win"] += 2000
                results["Trend"]["hits"] += 1
            if target in picks_r: 
                results["Random"]["win"] += 2000
                results["Random"]["hits"] += 1
            
            current_pool = pd.concat([current_pool, pd.DataFrame([row])])
            
        # --- Results Display (Detailed) ---
        
        # Helper to display strategy stats
        def show_stats(name, res):
            net = res["win"] - res["cost"]
            roi = (net / res["cost"]) * 100 if res["cost"] > 0 else 0
            
            st.markdown(f"##### {name}")
            # Use columns for layout
            c1, c2 = st.columns(2)
            c1.write(f"- {T['bt_lbl_hits']} **{res['hits']} / {len(test_set)}**")
            c1.write(f"- {T['bt_lbl_invest']} {res['cost']:,}")
            c2.write(f"- {T['bt_lbl_return']} {res['win']:,}")
            c2.metric(T["bt_lbl_net"], f"{net:,} THB", delta=net) # Metric for visual impact
            st.write(f"- {T['bt_lbl_roi']} **{roi:.2f}%**")
            st.divider()

        show_stats(T["bt_strat_trend"], results["Trend"])
        show_stats(T["bt_strat_rand"], results["Random"])
        
        # Conclusion
        st.markdown(f"**{T['bt_comparison']}**")
        diff = results["Trend"]["hits"] - results["Random"]["hits"]
        if abs(diff) <= 1: st.info(T["bt_con_equal"])
        elif diff > 1: st.warning(T["bt_con_trend"])
        else: st.error(T["bt_con_rand"])

# -----------------------------------------------
# 4. Monte Carlo Simulation
# -----------------------------------------------
st.divider()
st.subheader(T["sim_title"])
st.markdown(T["sim_desc"])

if st.button(T["sim_btn"]):
    years_mc = 5 # Fixed as per prompt or user previous behavior prefer 5
    st.markdown(T["sim_narration"].format(years_mc))
    
    simulations = 120 * (years_mc/5) * 5 # Approx 120 draws for 5 years
    simulations = int(simulations)
    
    ticket_price = 80
    total_cost = 0
    total_win = 0
    jackpot_hit = False
    
    progress_bar = st.progress(0)
    
    for i in range(simulations):
        total_cost += ticket_price
        current_win = 0
        if random.random() < 0.01: current_win += 2000
        if random.random() < 0.004: current_win += 4000
        if random.random() < 0.000001: 
            current_win += 6000000
            jackpot_hit = True
        if random.random() < 0.00016: current_win += 20000
        total_win += current_win
        progress_bar.progress((i + 1) / simulations)
        
    net_profit = total_win - total_cost
    
    c1, c2, c3 = st.columns(3)
    c1.metric(T["sim_lbl_cost"], f"{total_cost}")
    c2.metric(T["sim_lbl_return"], f"{total_win}")
    c3.metric(T["sim_lbl_net"], f"{net_profit}", delta=net_profit)
    
    if jackpot_hit:
        st.balloons()
        st.success(T["sim_jackpot"])
    elif net_profit > 0:
        st.success(T["sim_res_win"])
    else:
        st.warning(T["sim_res_loss"])

# -----------------------------------------------
# 5. Scientific Validation (Chi-Square) - Moved Here
# -----------------------------------------------
st.divider()
st.subheader(T["val_title"])
st.markdown(T["val_desc"])

# Perform Calc
observed_counts = collections.Counter(all_2digits)
# Fill missing
for i in range(100):
    k = f"{i:02d}"
    if k not in observed_counts: observed_counts[k] = 0

obs = [observed_counts[f"{i:02d}"] for i in range(100)]
exp = [len(df)/100] * 100
chi2, p_value = stats.chisquare(obs, f_exp=exp)

c1, c2 = st.columns(2)
c1.metric("Chi-Square", f"{chi2:.2f}")
c2.metric("P-Value", f"{p_value:.4f}")

if p_value > 0.05:
    st.success(T["val_res_pass"])
    st.caption(T["val_exp_pass"])
else:
    st.error(T["val_res_fail"])

# -----------------------------------------------
# Footer
# -----------------------------------------------
st.divider()
st.subheader(T["final_rec"])
st.caption(T["footer"])
