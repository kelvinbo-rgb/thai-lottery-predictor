
import streamlit as st
import pandas as pd
import random
import collections
import os

# ------------------------------------------------------------
# 🌍 多语言配置 / Multi-language Config
# ------------------------------------------------------------
LANG = {
    "中文": {
        "title": "🇹🇭 泰国彩票智能决策",
        "password_label": "请输入访问密码:",
        "password_error": "😕 密码错误",
        "data_loaded": "💾 数据已加载",
        "data_latest": "最新: ",
        "tab_trend": "🔥 趋势策略 (追热)",
        "tab_random": "🧪 随机策略 (防守)",
        "trend_desc": "基于历史热度加权推荐 (假设热号持续)",
        "random_desc": "完全数学随机推荐 (承认独立概率)",
        "rec_label_trend": "推荐",
        "rec_label_radom": "随机",
        "reason": "历史出现 {} 次",
        "reason_rnd": "纯随机生成",
        "ev_title": "📊 奖金结构与数学真相",
        "ev_desc": "这是彩票的真实价值表。揭示了为什么长期“买多亏多”。",
        "ev_col_prize": "奖项",
        "ev_col_rule": "规则",
        "ev_col_amount": "奖金",
        "ev_col_prob": "中奖率",
        "ev_col_value": "贡献价值",
        "ev_conclusion": "💡 核心结论",
        "ev_conclusion_text": "一张售价 80 THB 的彩票，数学价值仅 {:.2f} THB。\n每买一张，理论亏损 {:.2f} THB。",
        "sim_title": "💰 历史回测模拟",
        "sim_years_label": "回测过去多少年数据？",
        "sim_btn": "开始模拟",
        "sim_strategy_desc": "ℹ️ 模拟策略：假设每期随机购买 1 张 (80 THB)，只统计末两位和前后三奖项。",
        "sim_total_cost": "总投入",
        "sim_total_return": "总回报",
        "sim_net": "净盈亏",
        "sim_loss_msg": "📉 结论：长期参与是负和游戏。",
        "sim_win_msg": "🎉 运气爆表！但请记得这是极小概率事件。",
        "footer": "🔒 私有部署 | 仅限授权访问"
    },
    "English": {
        "title": "🇹🇭 Thai Lottery Insight",
        "password_label": "Enter Password:",
        "password_error": "😕 Incorrect Password",
        "data_loaded": "💾 Data Loaded",
        "data_latest": "Latest: ",
        "tab_trend": "🔥 Trend Strategy",
        "tab_random": "🧪 Random Strategy",
        "trend_desc": "Weighted recommendation based on history.",
        "random_desc": "Pure mathematical random selection.",
        "rec_label_trend": "Pick",
        "rec_label_radom": "Rand",
        "reason": "Hit {} times",
        "reason_rnd": "Pure Random",
        "ev_title": "📊 Math & Truth",
        "ev_desc": "The real mathematical value of a lottery ticket.",
        "ev_col_prize": "Prize",
        "ev_col_rule": "Rule",
        "ev_col_amount": "Amount",
        "ev_col_prob": "Prob.",
        "ev_col_value": "Value",
        "ev_conclusion": "💡 Conclusion",
        "ev_conclusion_text": "Ticket Price: 80 THB, Real Value: {:.2f} THB.\nTheoretical loss per ticket: {:.2f} THB.",
        "sim_title": "💰 Backtest Simulation",
        "sim_years_label": "Years to backtest:",
        "sim_btn": "Run Simulation",
        "sim_strategy_desc": "ℹ️ Strategy: Buy 1 ticket (80 THB) randomly per draw.",
        "sim_total_cost": "Total Cost",
        "sim_total_return": "Total Return",
        "sim_net": "Net Profit",
        "sim_loss_msg": "📉 Long-term participation is a negative-sum game.",
        "sim_win_msg": "🎉 Lucky! But this is rare.",
        "footer": "🔒 Private Access Only"
    },
    "ภาษาไทย": {
        "title": "🇹🇭 วิเคราะห์หวยไทย",
        "password_label": "กรุณาใส่รหัสผ่าน:",
        "password_error": "😕 รหัสผ่านผิด",
        "data_loaded": "💾 โหลดข้อมูลแล้ว",
        "data_latest": "ล่าสุด: ",
        "tab_trend": "🔥 เลขเด็ด (ตามสถิติ)",
        "tab_random": "🧪 เลขสุ่ม (คณิตศาสตร์)",
        "trend_desc": "แนะนำตามความถี่ในอดีต",
        "random_desc": "สุ่มตามหลักคณิตศาสตร์อย่างแท้จริง",
        "rec_label_trend": "แนะนำ",
        "rec_label_radom": "สุ่ม",
        "reason": "ออกแล้ว {} ครั้ง",
        "reason_rnd": "สุ่มแท้จริง",
        "ev_title": "📊 ความจริงทางคณิตศาสตร์",
        "ev_desc": "มูลค่าที่แท้จริงของสลากกินแบ่งรัฐบาล",
        "ev_col_prize": "รางวัล",
        "ev_col_rule": "กติกา",
        "ev_col_amount": "เงินรางวัล",
        "ev_col_prob": "โอกาส",
        "ev_col_value": "มูลค่าจริง",
        "ev_conclusion": "💡 สรุป",
        "ev_conclusion_text": "ราคา 80 บาท มูลค่าจริงเพียง {:.2f} บาท\nขาดทุนทางทฤษฎีใบละ {:.2f} บาท",
        "sim_title": "💰 จำลองผลย้อนหลัง",
        "sim_years_label": "ย้อนหลังกี่ปี?",
        "sim_btn": "เริ่มจำลอง",
        "sim_strategy_desc": "ℹ️ กลยุทธ์: ซื้อสุ่มงวดละ 1 ใบ (80 บาท)",
        "sim_total_cost": "ต้นทุนรวม",
        "sim_total_return": "ได้รับรางวัล",
        "sim_net": "กำไร/ขาดทุน",
        "sim_loss_msg": "📉 ในระยะยาว คุณมีโอกาสขาดทุนสูง",
        "sim_win_msg": "🎉 โชคดีมาก! แต่นี่เป็นโอกาสน้อย",
        "footer": "🔒 สำหรับผู้ได้รับอนุญาตเท่านั้น"
    }
}

# ------------------------------------------------------------
# 页面配置
# ------------------------------------------------------------
st.set_page_config(page_title="Thai Lottery", page_icon="🎰", layout="centered")

# 语言选择 (放在 Sidebar 或顶部)
# 默认中文
if "lang_choice" not in st.session_state:
    st.session_state["lang_choice"] = "中文"

# Top language selector
c1, c2 = st.columns([3, 1])
with c2:
    lang_opt = st.selectbox("Language / ภาษา", ["中文", "English", "ภาษาไทย"], label_visibility="collapsed")
    st.session_state["lang_choice"] = lang_opt

T = LANG[st.session_state["lang_choice"]]

# ------------------------------------------------------------
# 🔐 安全验证
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
    return df

df = load_data()

if df.empty:
    st.error("No Data Found.")
    st.stop()

# 数据加载显示 (分两行优化手机体验)
st.success(f"{T['data_loaded']} (Total {len(df)})")
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
# 1. 选号助手
# -----------------------------------------------
st.divider()
tab1, tab2 = st.tabs([T["tab_trend"], T["tab_random"]])

with tab1:
    st.write(T["trend_desc"])
    cols = st.columns(3)
    # 模拟加权选择
    population = list(counter_2.keys())
    weights = list(counter_2.values())
    if population:
        trend_picks = random.choices(population, weights=weights, k=3)
        for i, num in enumerate(trend_picks):
            # 获取该号码的历史出现次数
            count = counter_2[num]
            cols[i].metric(label=f"{T['rec_label_trend']} {i+1}", value=num, delta=T["reason"].format(count))
            cols[i].caption(f"Valid: {T['reason'].format(count)}") # fallback if metric delta confusing

with tab2:
    st.write(T["random_desc"])
    cols = st.columns(3)
    rand_picks = [f"{random.randint(0,99):02d}" for _ in range(3)]
    for i, num in enumerate(rand_picks):
        cols[i].metric(label=f"{T['rec_label_radom']} {i+1}", value=num)

# -----------------------------------------------
# 2. 数学表
# -----------------------------------------------
st.divider()
st.subheader(T["ev_title"])
st.markdown(T["ev_desc"])

# 构建多语言数据表
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
    T["ev_col_prob"]: [1, 5, 10, 50, 100, 2, 4000, 10000], # per million
    T["ev_col_rule"]: p_rules
}
df_ev = pd.DataFrame(data_ev)

# 计算
df_ev[T["ev_col_value"]] = df_ev[T["ev_col_amount"]] * (df_ev[T["ev_col_prob"]] / 1000000)
# 格式化概率显示 1/N
df_ev[T["ev_col_prob"]] = df_ev[T["ev_col_prob"]].apply(lambda x: f"1/{int(1000000/x):,}")

# 展示
st.dataframe(df_ev[[T["ev_col_prize"], T["ev_col_rule"], T["ev_col_amount"], T["ev_col_prob"], T["ev_col_value"]]], hide_index=True)

total_ev = df_ev[T["ev_col_value"]].sum()
loss = 80 - total_ev
st.info(T["ev_conclusion_text"].format(total_ev, loss))

# -----------------------------------------------
# 3. 回测模拟
# -----------------------------------------------
st.divider()
st.subheader(T["sim_title"])
st.caption(T["sim_strategy_desc"])

years_sim = st.slider(T["sim_years_label"], 1, 10, 5)

if st.button(T["sim_btn"]):
    weeks = years_sim * 24 
    cost = weeks * 80 
    
    # Simple Sim
    wins = 0
    # Simulate: 1 ticket per draw, check 2digit (1%) and 3digit (0.4%)
    for _ in range(weeks):
        r = random.random()
        if r < 0.01: wins += 2000
        elif r < 0.014: wins += 4000
    
    net = wins - cost
    
    c1, c2, c3 = st.columns(3)
    c1.metric(T["sim_total_cost"], f"{cost}")
    c2.metric(T["sim_total_return"], f"{wins}")
    c3.metric(T["sim_net"], f"{net}", delta=net)
    
    if net < 0:
        st.warning(T["sim_loss_msg"])
    else:
        st.balloons()
        st.success(T["sim_win_msg"])

st.markdown("---")
st.caption(T["footer"])
