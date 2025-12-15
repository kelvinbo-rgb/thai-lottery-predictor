
import streamlit as st
import pandas as pd
import random
import datetime
import collections
import os
import requests
from bs4 import BeautifulSoup

# 配置页面
st.set_page_config(page_title="Thai Lottery", page_icon="🎰", layout="centered")

# ------------------------------------------------------------
# 🔐 安全验证 (Security)
# ------------------------------------------------------------
def check_password():
    """Returns `True` if the user had the correct password."""
    
    def password_entered():
        if st.session_state["password"] == "888":
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "请输入访问密码 (Enter Password):", type="password", on_change=password_entered, key="password"
        )
        return False
        
    elif not st.session_state["password_correct"]:
        # Password incorrect, show input + error.
        st.text_input(
            "请输入访问密码 (Enter Password):", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 密码错误 / Password incorrect")
        return False
        
    else:
        # Password correct.
        return True

if not check_password():
    st.stop()  # Do not run further if password incorrect

# ------------------------------------------------------------
# 主程序
# ------------------------------------------------------------
st.title("🇹🇭 泰国彩票智能决策")
st.caption("基于统计学与蒙特卡洛模拟的分析工具")

# 读取数据 (复用逻辑)
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
    st.error("没有找到历史数据文件 (historical_data.csv)。请先运行主程序更新数据。")
    st.stop()

st.success(f"💾 数据已加载：最新一期 **{df.iloc[0]['date']}** (共 {len(df)} 期)")

# 分析逻辑
all_2digits = []
for idx, row in df.iterrows():
    val = str(row['prize_2digits']).strip()
    if len(val) == 1: val = "0" + val
    if val and val.lower() != 'nan':
        all_2digits.append(val)

counter_2 = collections.Counter(all_2digits)
most_common = counter_2.most_common(5)

# -----------------------------------------------
# 1. 核心预测 (精简版)
# -----------------------------------------------
st.divider()
st.subheader("🎲 选号助手")

tab1, tab2 = st.tabs(["🔥 趋势策略 (追热)", "🧪 随机策略 (防守)"])

with tab1:
    st.write("根据历史热度加权推荐：")
    cols = st.columns(3)
    # Weighted Random logic simulates the "Trend" strategy
    population = list(counter_2.keys())
    weights = list(counter_2.values())
    trend_picks = random.choices(population, weights=weights, k=3)
    for i, num in enumerate(trend_picks):
        cols[i].metric(label=f"推荐 {i+1}", value=num)
    st.caption("*逻辑：假设热号会继续热（赌徒谬误利用）*")

with tab2:
    st.write("完全数学随机推荐：")
    cols = st.columns(3)
    rand_picks = [f"{random.randint(0,99):02d}" for _ in range(3)]
    for i, num in enumerate(rand_picks):
        cols[i].metric(label=f"随机 {i+1}", value=num)
    st.caption("*逻辑：承认独立事件，避免思维偏差*")

# -----------------------------------------------
# 2. 数学价值表 (新增)
# -----------------------------------------------
st.divider()
st.subheader("📊 奖金结构与数学真相")
st.markdown("这是彩票的**真实价值表**。它揭示了为什么长期看来“买得越多亏得越多”。")

# 构造数据表
data_ev = {
    "奖项": ["一等奖 (1st Prize)", "二等奖 (2nd Prize)", "三等奖 (3rd Prize)", "四等奖 (4th Prize)", "五等奖 (5th Prize)", "邻近奖 (Side Prize)", "前/后三 (3 Digits)", "末两位 (2 Digits)"],
    "奖金 (THB)": [6000000, 200000, 80000, 40000, 20000, 100000, 4000, 2000],
    "中奖率 (百万分之)": [1, 5, 10, 50, 100, 2, 4000, 10000],
    "中奖规则简述": [
        "6位数字全中 (必须完全一致)", 
        "6位数字", 
        "6位数字", 
        "6位数字", 
        "6位数字", 
        "头奖号码 ±1 (例如头奖999，邻近为998/000)", 
        "前3位 或 后3位 (各抽2次，共4次机会)", 
        "最后2位数字"
    ]
}
df_ev = pd.DataFrame(data_ev)

# 计算贡献价值
# 贡献价值 = 奖金 * (中奖率 / 1,000,000)
df_ev["贡献价值 (THB)"] = df_ev["奖金 (THB)"] * (df_ev["中奖率 (百万分之)"] / 1000000)
df_ev["中奖率 (精简)"] = df_ev["中奖率 (百万分之)"].apply(lambda x: f"1/{int(1000000/x)}" if x > 0 else "0")

# 调整列顺序
df_display = df_ev[["奖项", "中奖规则简述", "奖金 (THB)", "中奖率 (精简)", "贡献价值 (THB)"]]

st.dataframe(df_display, hide_index=True)

# 汇总计算
total_ev = df_ev["贡献价值 (THB)"].sum()
ticket_price = 80
loss_per_ticket = ticket_price - total_ev

st.info(f"""
💡 **核心结论**：
- 一张售价 **{ticket_price} THB** 的彩票，其实际数学价值仅为 **{total_ev:.2f} THB**。
- 您每买一张，理论上就直接“亏损”了 **{loss_per_ticket:.2f} THB**。
- **末两位奖** (2 Digits) 贡献了最大的价值 (20 THB)，比头奖的贡献 (6 THB) 还高。
""")

# -----------------------------------------------
# 3. 模拟器
# -----------------------------------------------
st.divider()
st.subheader("💰 5年回测模拟")
years_sim = st.slider("假如我过去坚持买多少年？", 1, 10, 5)
cols_sim = st.columns(2)
with cols_sim[0]:
    if st.button("开始模拟"):
        weeks = years_sim * 24 # 每年约24期
        cost = weeks * 80 # 每期买1张
        
        # 简单概率模拟
        wins = 0
        for _ in range(weeks):
            # 简化：只模拟中末两位 (1%概率) 和 前后三 (0.4%)
            r = random.random()
            if r < 0.01: wins += 2000
            elif r < 0.014: wins += 4000
        
        net = wins - cost
        st.metric("总投入", f"{cost} THB")
        st.metric("总回报", f"{wins} THB")
        st.metric("净盈亏", f"{net} THB", delta_color="normal" if net >= 0 else "inverse")
        
        if net < 0:
            st.warning("📉 长期来看，这是个负和游戏。")
        else:
            st.balloons()
            st.success("🎉 运气爆表！但请记得这是极小概率事件。")

st.markdown("---")
st.caption("🔒 私有部署 | 仅限授权访问 | Math doesn't lie.")
