
import streamlit as st
import pandas as pd
import random
import collections
import os
import scipy.stats as stats
import datetime
import ast # 用于解析 ['123', '456'] 格式的字符串

# ------------------------------------------------------------
# 🎨 界面样式优化 (CSS)
# ------------------------------------------------------------
st.set_page_config(page_title="Thai Lottery", page_icon="💰", layout="centered")

# Helper function to strip all leading whitespace from HTML lines
def clean_html(html_str):
    return "\n".join([line.strip() for line in html_str.split("\n")])

# 强制去除顶部留白 + 优化移动端显示
st.markdown(clean_html("""
<style>
.block-container {
padding-top: 2.5rem !important;
padding-bottom: 2rem !important;
}
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
h1 {
padding-bottom: 0px !important;
}
.section-header {
font-size: 1.3em;
font-weight: 600;
margin-bottom: 0;
}
.section-sub {
font-size: 0.9em;
color: #666;
margin-top: -5px;
margin-bottom: 15px;
display: block;
}
/* Smart Picker 样式 */
.custom-grid-container {
display: flex;
justify-content: space-between;
margin-bottom: 10px;
}
.custom-metric-card {
width: 98%; 
background-color: #f9f9f9; 
padding: 10px;
border-radius: 8px;
border: 1px solid #eee;
text-align: left;
}
.metric-label { font-size: 0.8em; color: #666; margin-bottom: 2px; }
.metric-value { font-size: 1.8em; font-weight: 700; color: #333; line-height: 1.2; }
.metric-delta { font-size: 0.8em; color: #28a745; font-weight: 500; }
.grid-header { font-size: 1.0em; font-weight: 600; color: #333; }
.grid-sub { font-size: 0.75em; color: #888; font-weight: 400; margin-bottom: 8px; }
    
/* 净盈亏 样式 (Backtest) */
.net-profit-box-bt {
padding: 5px 0px;
}
.net-profit-label-bt { font-size: 0.85em; color: #666; }
.net-profit-value-bt { font-size: 1.2em; font-weight: 700; }
    
/* 净盈亏 样式 (Monte Carlo) */
.net-profit-box-mc {
padding: 0px 0px; 
}
.net-profit-label-mc { 
font-size: 14px;
color: rgb(49, 51, 63);
margin-bottom: 4px;
}
.net-profit-value-mc { 
font-size: 2rem; 
font-weight: 600;
line-height: 1.2;
}

.np-pos { color: #09ab3b; } 
.np-neg { color: #ff2b2b; } 
    
/* 科学检验 样式 */
.sci-box {
background-color: #f0f2f6;
padding: 15px;
border-radius: 5px;
border-left: 4px solid #555;
font-family: monospace;
font-size: 0.9em;
margin-bottom: 10px;
}
.sci-title { font-weight: bold; font-size: 1.1em; color: #333; margin-bottom: 8px; border-bottom: 1px dashed #999; padding-bottom: 5px;}
.sci-row { display: flex; justify-content: space-between; margin-bottom: 4px; }
.sci-val { font-weight: bold; }
/* 避免 f-string 冲突，尽量少在 style 里写 {} */
.sci-conclusion-pass { margin-top: 10px; font-weight: bold; color: #09ab3b; }
.sci-conclusion-fail { margin-top: 10px; font-weight: bold; color: #ff2b2b; }
.sci-desc { margin-top: 5px; line-height: 1.4; }
.sci-advice { margin-top: 5px; color: #666; font-style: italic; }

/* Footer small - slightly larger */
.footer-advice {
text-align: center;
color: #888;
font-size: 1.0em; /* 增大一点: 0.85em -> 1.0em */
margin-top: 20px;
border-top: 1px solid #eee;
padding-top: 10px;
}
</style>
"""), unsafe_allow_html=True)

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
        "data_latest": "งวดประจำวันที่ {}",
        "latest_1st_title": "รางวัลที่ 1",
        "latest_prefix_title": "เลขหน้า 3 ตัว",
        "latest_suffix_title": "เลขท้าย 3 ตัว",
        "latest_2d_title": "เลขท้าย 2 ตัว",
        "tab_trend": "🔥 แนวโน้ม",
        "tab_random": "🧪 สุ่ม",
        "tab_hot": "📊 เลขมาแรง",
        "trend_desc": "🧬 กฎแห่งแรงเฉื่อย (Inertia)\nเชื่อว่าตัวเลขที่มี 'พลังงาน' จะยังคงออกซ้ำ",
        "random_desc": "🎲 กฎแห่งความโกลาหล (Entropy)\nทุกตัวเลขมีโอกาสเท่ากัน ไม่มีใครรู้อนาคต",
        "hot_desc": "📈 กฎจำนวนมาก (Law of Large Numbers)\nสถิติระยะยาวชี้เป้าตัวเลขที่แข็งแกร่งที่สุด",
        "rec_label_trend": "Trend #{}",
        "rec_label_radom": "Rand #{}",
        "rec_label_hot": "Hot #{}",
        "reason": "{} ครั้ง",
        "reason_rnd": "สุ่ม",
        "reason_hot": "ออกบ่อยสุด",
        "ev_title": "📊 ความจริงทางคณิตศาสตร์",
        "ev_desc": "ตารางแสดงมูลค่าจริงของสลากฯ เมื่อเทียบกับราคาขาย",
        "ev_col_prize": "รางวัล",
        "ev_col_rule": "กติกา",
        "ev_col_amount": "เงิน",
        "ev_col_prob": "โอกาส",
        "ev_col_value": "มูลค่า",
        "ev_conclusion_text": "ราคาขาย 80 บาท แต่มูลค่าทางคณิตศาสตร์เพียง {:.2f} บาท\nทุกใบที่คุณซื้อ คือการขาดทุนทางทฤษฎี {:.2f} บาท",
        "col_2d_title": "เลขท้าย 2 ตัว",
        "col_3d_title": "เลขท้าย 3 ตัว",
        "prob_2d": "โอกาส 1/100",
        "prob_3d": "โอกาส 1/250",
        "stats_hot": "🔥 เลขมาแรง (Hot):",
        "stats_hot_desc": "สถิติย้อนหลังสูงสุด",
        "bt_title_main": "⏪ ทดสอบย้อนหลัง",
        "bt_title_sub": "Historical Backtest",
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
        "sim_title_main": "🎲 การจำลอง Monte Carlo",
        "sim_title_sub": "Monte Carlo Simulation",
        "sim_desc": "จำลองเหตุการณ์ในอนาคตด้วยความน่าจะเป็นทางคณิตศาสตร์",
        "sim_desc_long": "โมเดลความน่าจะเป็น (Probability Model) คำนวณโอกาสถูกรางวัลทุกประเภท รวมถึงรางวัลที่ 1",
        "sim_intro": """
        การจำลองนี้ครอบคลุมรางวัลทั้งหมดตั้งแต่ **[รางวัลที่ 1]** ถึง **[เลขท้าย 2 ตัว]** 
        ซื้อ 1 ใบต่องวด แบบสุ่มทั้งหมด มาดูกันว่าดวงจะเป็นอย่างไร
        """,
        "sim_btn": "เริ่ม Monte Carlo",
        "sim_narration": "📝 สมมติฐาน: คุณซื้อหวยงวดละ 1 ใบ (80 บาท) ต่อเนื่องเป็นเวลา {} ปี...",
        "sim_lbl_cost": "ต้นทุนรวม",
        "sim_lbl_return": "เงินรางวัลรวม",
        "sim_lbl_net": "กำไรสุทธิ",
        "sim_res_loss": "💡 ผลลัพธ์: ขาดทุน (เป็นปกติของการพนัน)",
        "sim_res_win": "💡 ผลลัพธ์: กำไร (คุณโชคดีมาก!)",
        "sim_jackpot": "🤯 แจ็กพอตแตก! (ถูกรางวัลที่ 1)",
        "val_title_main": "🧪 การทดสอบทางวิทยาศาสตร์ (Beta)",
        "val_title_sub": "Scientific Validation",
        "sci_title": "ผลการทดสอบ Chi-Square",
        "sci_samples": "จำนวนกลุ่มตัวอย่าง:",
        "sci_stat": "ค่าสถิติ Chi-Square:",
        "sci_crit": "ค่าวิกฤต (p=0.05):",
        "sci_res_pass": "✅ [สรุป] การกระจายตัวแบบสุ่ม (ยอมรับสมมติฐาน H0)",
        "sci_exp_pass": "ข้อมูลแสดงให้เห็นถึงการกระจายแบบสุ่มที่แท้จริง 'เลขเด็ด' ในอดีตเป็นเพียงความบังเอิญ",
        "sci_advice": "คำแนะนำ: ใช้กลยุทธ์ 'สุ่มตัวเลข' (Random)",
        "sci_res_fail": "❌ [สรุป] พบความผิดปกติทางสถิติ",
        "final_rec": "💬 คำแนะนำสุดท้าย: หวยคือ 'ความบันเทิง' ไม่ใช่ 'การลงทุน' | ขอให้โชคดี!",
        "footer": "🔒 Private Access Only | 888"
    },
    "中文": {
        "title": "💰 泰国彩票AI智能策略",
        "password_label": "请输入访问密码:",
        "password_error": "😕 密码错误",
        "data_loaded": "💾 数据已加载",
        "data_total_fmt": " (共 {} 期)",
        "data_latest": "最新开奖日期: {}",
        "latest_1st_title": "一等奖",
        "latest_prefix_title": "前三位数",
        "latest_suffix_title": "后三位数",
        "latest_2d_title": "两位数",
        "tab_trend": "🔥 趋势策略",
        "tab_random": "🧪 随机策略",
        "tab_hot": "📊 热门策略",
        "trend_desc": "**🧬 历史惯性定律 (Inertia)**\n假设数字存在“热度”，近期频繁出现的数字具有动量，未来可能继续出现。",
        "random_desc": "**🎲 最大熵原理 (Entropy)**\n承认每次开奖都是独立事件，使用量子级真随机算法，消除人为偏见。",
        "hot_desc": "**📈 大数定律 (Law of Large Numbers)**\n基于长期大样本统计，筛选出历史概率分布中表现最强势的“黄金号码”。",
        "rec_label_trend": "推荐 ({})",
        "rec_label_radom": "随机 ({})",
        "rec_label_hot": "热门 ({})",
        "reason": "出现 {} 次",
        "reason_rnd": "纯随机",
        "reason_hot": "历史最热",
        "ev_title": "📊 奖金结构与数学真相",
        "ev_desc": "这是彩票的真实价值表。",
        "ev_col_prize": "奖项",
        "ev_col_rule": "规则",
        "ev_col_amount": "奖金",
        "ev_col_prob": "中奖率",
        "ev_col_value": "贡献价值",
        "ev_conclusion_text": "一张售价 80 THB 的彩票，数学价值仅 {:.2f} THB。\n每买一张，理论亏损 {:.2f} THB。",
        "col_2d_title": "两位数",
        "col_3d_title": "三位数",
        "prob_2d": "概率 1/100",
        "prob_3d": "概率 1/250",
        "stats_hot": "🔥 热门号码速览:",
        "stats_hot_desc": "Top 5 出现频率",
        "bt_title_main": "⏪ 历史回测",
        "bt_title_sub": "Historical Backtest",
        "bt_years_label": "回测过去多少年数据？",
        "bt_btn": "开始回测",
        "bt_header_info": "📋 回测详情",
        "bt_info_range": "• 回测区间: {} 至 {}",
        "bt_info_count": "• 回测期数: {} 期",
        "bt_info_cfg": "⚙️ 策略设定: 每期买 3 注 (2位数)",
        "bt_info_cost_desc": "• 单期成本: 240 THB \n• 中奖奖金: 2,000 THB",
        "bt_strat_trend": "🔥 趋势策略",
        "bt_strat_rand": "🧪 随机策略",
        "bt_lbl_hits": "中奖次数:",
        "bt_lbl_invest": "总投入:",
        "bt_lbl_return": "总回报:",
        "bt_lbl_net": "净盈亏:",
        "bt_lbl_roi": "回报率 (ROI):",
        "bt_comparison": "🧐 回测结论:",
        "bt_con_equal": "两种策略表现持平！再次验证了彩票的随机游走性质。",
        "bt_con_trend": "趋势策略略微领先 (可能是运气波动)。",
        "bt_con_rand": "随机策略竟然反超了！说明追热号并不总是有效。",
        "sim_title_main": "🎲 蒙特卡洛模拟",
        "sim_title_sub": "Monte Carlo Simulation",
        "sim_desc": "基于数学期望的纯概率模拟 (含头奖)",
        "sim_desc_long": "概率模型 (Probability Model) 计算包含头奖在内的所有中奖机会。",
        "sim_intro": """
        本次模拟包含了从 **【一等奖】** 到 **【末两位】** 的所有中奖可能。
        每期买 1 张，完全随机，看看运气如何。
        """,
        "sim_btn": "运行模拟",
        "sim_narration": "📝 模拟假设: 您坚持买彩票 {} 年，每期坚持买 1 张 (80 THB)...",
        "sim_lbl_cost": "总投入",
        "sim_lbl_return": "总奖金",
        "sim_lbl_net": "净盈亏",
        "sim_res_loss": "💡 点评: 长期参与大概率亏损。请保持娱乐心态。",
        "sim_res_win": "💡 点评: 运气不错，小赚一笔！主要是靠运气。",
        "sim_jackpot": "🤯 天呐！中了头奖 (Jackpot)！",
        "val_title_main": "🧪 科学有效性检验 (Beta)",
        "val_title_sub": "Scientific Validation",
        "sci_title": "Chi-Square 检验报告",
        "sci_samples": "样本总量:",
        "sci_stat": "卡方统计量 (Chi-Square):",
        "sci_crit": "临界值 (p=0.05):",
        "sci_res_pass": "✅ [结论] 分布均匀 (接受假设 H0)",
        "sci_exp_pass": "数据表现为真正的随机分布。历史“热号”只是统计噪音，不代表未来趋势。",
        "sci_advice": "建议：使用【完全随机推荐】策略。",
        "sci_res_fail": "❌ [结论] 发现统计异常",
        "final_rec": "💬 最终建议: 将彩票视为【消费】而非【投资】。| 祝您好运!",
        "footer": "🔒 Private Access Only | 888"
    },
    "English": {
        "title": "💰 Thai Lottery AI Strategy",
        "password_label": "Enter Password:",
        "password_error": "😕 Incorrect Password",
        "data_loaded": "💾 Data Loaded",
        "data_total_fmt": " (Total {})",
        "data_latest": "Draw Date: {}",
        "latest_1st_title": "1st Prize",
        "latest_prefix_title": "3-Digit Prefix",
        "latest_suffix_title": "3-Digit Suffix",
        "latest_2d_title": "2 Digits",
        "tab_trend": "🔥 Trend",
        "tab_random": "🧪 Random",
        "tab_hot": "📊 Hot",
        "trend_desc": "**🧬 Theory of Inertia**\nAssuming numbers follow momentum. What has happened frequently may continue to happen.",
        "random_desc": "**🎲 Theory of Entropy**\nRecognizing that each draw is independent. True chaos is the only fairness.",
        "hot_desc": "**📈 Law of Large Numbers**\nIdentifying the strongest numbers from long-term historical distribution.",
        "rec_label_trend": "Trend #{}",
        "rec_label_radom": "Rand #{}",
        "rec_label_hot": "Hot #{}",
        "reason": "{} Hits",
        "reason_rnd": "Random",
        "reason_hot": "Top Hit",
        "ev_title": "📊 Math & Truth",
        "ev_desc": "The real mathematical value of a lottery ticket.",
        "ev_col_prize": "Prize",
        "ev_col_rule": "Rule",
        "ev_col_amount": "Amount",
        "ev_col_prob": "Prob.",
        "ev_col_value": "Value",
        "ev_conclusion_text": "Ticket Price: 80 THB, Real Value: {:.2f} THB.\nTheoretical loss per ticket: {:.2f} THB.",
        "col_2d_title": "2 Digits",
        "col_3d_title": "3 Digits",
        "prob_2d": "Prob: 1/100",
        "prob_3d": "Prob: 1/250",
        "stats_hot": "🔥 Hot Numbers:",
        "stats_hot_desc": "Most Frequent",
        "bt_title_main": "⏪ Historical Backtest",
        "bt_title_sub": "Simulation",
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
        "sim_title_main": "🎲 Monte Carlo Simulation",
        "sim_title_sub": "Probabilistic Model",
        "sim_desc": "Pure probability simulation including Jackpot chances.",
        "sim_desc_long": "Calculates winning chances for all prizes including Jackpot.",
        "sim_intro": """
        This simulation covers all possibilities from **[1st Prize]** to **[Last 2 Digits]**.
        Buying 1 ticket per draw, completely random. Let's test your luck.
        """,
        "sim_btn": "Run Simulation",
        "sim_narration": "📝 Assumption: Buying 1 ticket (80 THB) per draw for {} years...",
        "sim_lbl_cost": "Total Cost",
        "sim_lbl_return": "Total Return",
        "sim_lbl_net": "Net Profit",
        "sim_res_loss": "💡 Comment: Long term loss is expected.",
        "sim_res_win": "💡 Comment: Lucky!",
        "sim_jackpot": "🤯 JACKPOT HIT!",
        "val_title_main": "🧪 Scientific Validation (Beta)",
        "val_title_sub": "Scientific Validation",
        "sci_title": "Chi-Square Test Report",
        "sci_samples": "Total Samples:",
        "sci_stat": "Chi-Square Stat:",
        "sci_crit": "Critical Value (p=0.05):",
        "sci_res_pass": "✅ [Conclusion] Uniform Distribution (Accept H0)",
        "sci_exp_pass": "Data behaves as true random. 'Hot numbers' are just noise.",
        "sci_advice": "Recommendation: Use 'Random Strategy'.",
        "sci_res_fail": "❌ [Conclusion] Deviation detected",
        "final_rec": "💬 Final Advice: Treat lottery as consumption, not investment. | Good Luck!",
        "footer": "🔒 Private Access Only | 888"
    }
}

# 语言选择 (Top)
if "lang_choice" not in st.session_state:
    st.session_state.lang_choice = "ภาษาไทย"

c1, c2 = st.columns([3, 1])
with c2:
    options = ["ภาษาไทย", "中文", "English"]
    # Fix: Use key to bind directly to session_state for one-click updates
    st.selectbox("Language", options, key="lang_choice", label_visibility="collapsed")

T = LANG[st.session_state.lang_choice]

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
# 主标题 & 最新数据
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
    df = df.reset_index(drop=True)
    return df

df = load_data()
if df.empty:
    st.error("No Data Found.")
    st.stop()

# 显示最新一期结果
latest = df.iloc[0]
latest_date_str = latest['date']
latest_1st = str(latest['prize_1st']).zfill(6)
latest_2d = str(latest['prize_2digits']).zfill(2)

# 解析 前三 / 后三
latest_prefix = [] # item is string
latest_suffix = [] # item is string

# prefix parsing (prize_pre_3digit)
if 'prize_pre_3digit' in latest:
    raw_pre = str(latest['prize_pre_3digit']).strip()
    if raw_pre.startswith('[') and raw_pre.endswith(']'):
         try: latest_prefix = ast.literal_eval(raw_pre)
         except: latest_prefix = []
    elif raw_pre.isdigit(): latest_prefix = [raw_pre]

# suffix parsing (prize_sub_3digits)
if 'prize_sub_3digits' in latest:
    raw_sub = str(latest['prize_sub_3digits']).strip()
    if raw_sub.startswith('[') and raw_sub.endswith(']'):
         try: latest_suffix = ast.literal_eval(raw_sub)
         except: latest_suffix = []
    elif raw_sub.isdigit(): latest_suffix = [raw_sub]

# Ensure lists (fallback)
if not isinstance(latest_prefix, list): latest_prefix = []
if not isinstance(latest_suffix, list): latest_suffix = []

# Format display strings
prefix_str = " ".join([str(x) for x in latest_prefix]) if latest_prefix else "-"
suffix_str = " ".join([str(x) for x in latest_suffix]) if latest_suffix else "-"

st.success(f"{T['data_loaded']}{T['data_total_fmt'].format(len(df))}")

# --- Official Style Latest Draw Header ---
st.markdown(clean_html(f"""
<style>
.latest-draw-container {{
background-color: #fff;
border: 1px solid #ddd;
border-radius: 12px;
padding: 15px;
text-align: center;
margin-bottom: 20px;
box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}}
.latest-date {{
font-size: 1.0em;
color: #555;
margin-bottom: 15px;
font-weight: 500;
}}
.prize-1st-box {{
margin-bottom: 20px;
}}
.result-number-1st {{
font-size: 2.5em;
font-weight: 800;
color: #173858; /* Official Blue */
letter-spacing: 3px;
}}
.result-title {{
font-size: 0.9em;
color: #173858;
margin-bottom: 2px;
}}
    
/* 3-Col Layout for sub prizes */
.sub-prizes-row {{
display: flex;
justify-content: space-around;
flex-wrap: wrap; 
border-top: 1px solid #eee;
padding-top: 15px;
}}
.sub-prize-item {{
text-align: center;
min-width: 30%;
margin-bottom: 10px;
}}
.sub-number {{
font-size: 1.4em;
font-weight: 700;
color: #173858;
letter-spacing: 1px;
}}
.sub-number-2d {{
font-size: 1.6em; /* Slightly larger for 2D */
font-weight: 800;
color: #173858;
}}
</style>

<div class="latest-draw-container">
<div class="latest-date">{T['data_latest'].format(latest_date_str)}</div>
    
<!-- 1st Prize -->
<div class="prize-1st-box">
<div class="result-title">{T['latest_1st_title']}</div>
<div class="result-number-1st">{latest_1st}</div>
</div>
    
<!-- Sub Prizes -->
<div class="sub-prizes-row">
<div class="sub-prize-item">
<div class="result-title">{T['latest_prefix_title']}</div>
<div class="sub-number">{prefix_str}</div>
</div>
<div class="sub-prize-item">
<div class="result-title">{T['latest_suffix_title']}</div>
<div class="sub-number">{suffix_str}</div>
</div>
<div class="sub-prize-item">
<div class="result-title">{T['latest_2d_title']}</div>
<div class="sub-number sub-number-2d">{latest_2d}</div>
</div>
</div>
</div>
"""), unsafe_allow_html=True)


# -----------------------------------------------
# 数据处理核心 (Robust Parsing)
# -----------------------------------------------
all_2digits = []
all_3digits = []

# 明确的列名，根据 CSV 文件结构
col_prefix = 'prize_pre_3digit' # singular
col_suffix = 'prize_sub_3digits' # plural

for idx, row in df.iterrows():
    # 1. 2 Digits
    val = str(row['prize_2digits']).strip()
    if len(val) == 1: val = "0" + val
    if val and val.lower() != 'nan':
        all_2digits.append(val)
    
    # 2. 3 Digits (List Parsing)
    # 处理 prize_pre_3digit
    if col_prefix in df.columns:
        raw_pre = str(row[col_prefix]).strip()
        try:
            # 尝试解析 "['449', '328']"
            if raw_pre.startswith('[') and raw_pre.endswith(']'):
                items = ast.literal_eval(raw_pre)
                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, str) and item.isdigit() and len(item) == 3:
                            all_3digits.append(item)
            elif raw_pre.isdigit() and len(raw_pre) == 3: # 如果只是纯数字
                 all_3digits.append(raw_pre)
        except:
            pass # Ignore parsing errors

    # 处理 prize_sub_3digits
    if col_suffix in df.columns:
        raw_sub = str(row[col_suffix]).strip()
        try:
            if raw_sub.startswith('[') and raw_sub.endswith(']'):
                items = ast.literal_eval(raw_sub)
                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, str) and item.isdigit() and len(item) == 3:
                            all_3digits.append(item)
            elif raw_sub.isdigit() and len(raw_sub) == 3:
                 all_3digits.append(raw_sub)
        except:
            pass

counter_2 = collections.Counter(all_2digits)
counter_3 = collections.Counter(all_3digits)

# -----------------------------------------------
# 1. 智能决策中心 (AI Strategy Center)
# -----------------------------------------------
st.divider()

# Tab Layout
tab1, tab2, tab3 = st.tabs([T["tab_trend"], T["tab_random"], T["tab_hot"]])


def show_picker_grid_card(picks_2, picks_3, reasons_2, reasons_3, desc):
    st.markdown(f"<div style='margin-bottom:15px; font-size:0.95em; color:#444;'>{desc}</div>", unsafe_allow_html=True)
    
    # 2 Digits / 3 Digits Layout Custom Flexbox for Mobile Support
    # Left Block: 2 Digits
    
    left_html = f"""<div style="flex:1; margin-right:5px;">
        <div class='grid-header'>{T['col_2d_title']}</div>
        <div class='grid-sub'>{T['prob_2d']}</div>
    """
    for i in range(3):
        p = picks_2[i] if i < len(picks_2) else "--"
        r = reasons_2[i] if i < len(reasons_2) else ""
        delta_html = f"<div class='metric-delta'>↑ {r}</div>" if r else ""
        left_html += f"""
        <div class="custom-metric-card" style="width:100%; margin-bottom:10px;">
            <div class="metric-label">{T['rec_label_trend'].format(i+1) if 'Trend' in desc else (T['rec_label_radom'].format(i+1) if 'Random' in desc else T['rec_label_hot'].format(i+1))}</div>
            <div class="metric-value">{p}</div>
            {delta_html}
        </div>
        """
    left_html += "</div>"
    
    # Right Block: 3 Digits
    right_html = f"""<div style="flex:1; margin-left:5px;">
        <div class='grid-header'>{T['col_3d_title']}</div>
        <div class='grid-sub'>{T['prob_3d']}</div>
    """
    for i in range(3):
        p = picks_3[i] if i < len(picks_3) else "--"
        r = reasons_3[i] if i < len(reasons_3) else ""
        delta_html = f"<div class='metric-delta'>↑ {r}</div>" if r else ""
        right_html += f"""
        <div class="custom-metric-card" style="width:100%; margin-bottom:10px;">
            <div class="metric-label">{T['rec_label_trend'].format(i+1) if 'Trend' in desc else (T['rec_label_radom'].format(i+1) if 'Random' in desc else T['rec_label_hot'].format(i+1))}</div>
            <div class="metric-value">{p}</div>
            {delta_html}
        </div>
        """
    right_html += "</div>"
    
    # Container with flex
    st.markdown(f"""
        <div style="display:flex; flex-direction:row; justify-content:space-between;">
            {left_html}
            {right_html}
        </div>
    """, unsafe_allow_html=True)


# --- 1. Trend Strategy Data ---
pop2 = list(counter_2.keys())
w2 = list(counter_2.values())
t_picks_2 = random.choices(pop2, weights=w2, k=3) if pop2 else ["--"]*3
t_reasons_2 = [T['reason'].format(counter_2[p]) for p in t_picks_2]

pop3 = list(counter_3.keys())
w3 = list(counter_3.values())
if not pop3:
    pop3 = [f"{random.randint(0,999):03d}" for _ in range(100)]
    w3 = [1]*100
t_picks_3 = random.choices(pop3, weights=w3, k=3)
t_reasons_3 = [T['reason'].format(counter_3.get(p, 0)) for p in t_picks_3]

# --- 2. Random Strategy Data ---
r_picks_2 = [f"{random.randint(0,99):02d}" for _ in range(3)]
r_reasons_2 = [T['reason_rnd']] * 3
r_picks_3 = [f"{random.randint(0,999):03d}" for _ in range(3)]
r_reasons_3 = [T['reason_rnd']] * 3

# --- 3. Hot Stats Data ---
h_picks_2 = [k for k,v in counter_2.most_common(3)]
h_reasons_2 = [T['reason'].format(counter_2[k]) for k in h_picks_2]
h_picks_3 = [k for k,v in counter_3.most_common(3)]
h_reasons_3 = [T['reason'].format(counter_3[k]) for k in h_picks_3]
# Pad if empty
while len(h_picks_2) < 3: h_picks_2.append("--"); h_reasons_2.append("")
while len(h_picks_3) < 3: h_picks_3.append("--"); h_reasons_3.append("")

with tab1:
    show_picker_grid_card(t_picks_2, t_picks_3, t_reasons_2, t_reasons_3, T["trend_desc"])

with tab2:
    show_picker_grid_card(r_picks_2, r_picks_3, r_reasons_2, r_reasons_3, T["random_desc"])

with tab3:
     show_picker_grid_card(h_picks_2, h_picks_3, h_reasons_2, h_reasons_3, T["hot_desc"])


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
    p_names = ["รางวัลที่ 1", "รางวัลที่ 2", "รางวัลที่ 3", "รางวัลที่ 4", "รางวัลที่ 5", "ข้างเคียง", "3ตัวน/ล", "2 ตัวท้าย"] 
    p_rules = ["ตรงทุกตัว", "6 หลัก", "6 หลัก", "6 หลัก", "6 หลัก", "ใกล้เคียง", "3 ตัว", "2 ตัว"]
else:
    p_names = ["1st Prize", "2nd Prize", "3rd Prize", "4th Prize", "5th Prize", "Side Prize", "3 Digits", "2 Digits"]
    p_rules = ["All Match", "6 Digits", "6 Digits", "6 Digits", "6 Digits", "+/- 1", "Prefix/Suffix", "Last 2"]

data_ev = {
    T["ev_col_prize"]: p_names,
    T["ev_col_rule"]: p_rules,
    T["ev_col_amount"]: [6000000, 200000, 80000, 40000, 20000, 100000, 4000, 2000],
    T["ev_col_prob"]: [1, 5, 10, 50, 100, 2, 4000, 10000], 
}
df_ev = pd.DataFrame(data_ev)
df_ev[T["ev_col_value"]] = df_ev[T["ev_col_amount"]] * (df_ev[T["ev_col_prob"]] / 1000000)
df_ev[T["ev_col_prob"]] = df_ev[T["ev_col_prob"]].apply(lambda x: f"1/{int(1000000/x)}") 

st.dataframe(
    df_ev[[T["ev_col_prize"], T["ev_col_rule"], T["ev_col_amount"], T["ev_col_prob"], T["ev_col_value"]]], 
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
st.markdown(clean_html(f"""
<div class='section-header'>{T['bt_title_main']}</div>
<div class='section-sub'>{T['bt_title_sub']}</div>
"""), unsafe_allow_html=True)

years_back = st.slider(T["bt_years_label"], 1, 10, 5)

if st.button(T["bt_btn"]):
    with st.spinner("Calculating..."):
        chron_data = df.sort_values('date_obj', ascending=True)
        latest_date = chron_data.iloc[-1]['date_obj']
        start_date = latest_date - pd.DateOffset(years=years_back)
        test_set = chron_data[chron_data['date_obj'] >= start_date]
        
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
            
        def show_stats(name, res):
            net = res["win"] - res["cost"]
            roi = (net / res["cost"]) * 100 if res["cost"] > 0 else 0
            
            net_color = "np-pos" if net >= 0 else "np-neg"
            net_sign = "+" if net >= 0 else ""

            st.markdown(f"##### {name}")
            c1, c2 = st.columns(2)
            c1.write(f"- {T['bt_lbl_hits']} **{res['hits']} / {len(test_set)}**")
            c1.write(f"- {T['bt_lbl_invest']} {res['cost']:,}")
            c2.write(f"- {T['bt_lbl_return']} {res['win']:,}")
            c2.markdown(f"""
                <div class='net-profit-box-bt'>
                    <div class='net-profit-label-bt'>{T['bt_lbl_net']}</div>
                    <div class='net-profit-value-bt {net_color}'>{net_sign}{net:,} THB</div>
                </div>
            """, unsafe_allow_html=True)
            st.write(f"- {T['bt_lbl_roi']} **{roi:.2f}%**")
            st.divider()

        show_stats(T["bt_strat_trend"], results["Trend"])
        show_stats(T["bt_strat_rand"], results["Random"])
        
        st.markdown(f"**{T['bt_comparison']}**")
        diff = results["Trend"]["hits"] - results["Random"]["hits"]
        if abs(diff) <= 1: st.info(T["bt_con_equal"])
        elif diff > 1: st.warning(T["bt_con_trend"])
        else: st.error(T["bt_con_rand"])

# -----------------------------------------------
# 4. Monte Carlo Simulation
# -----------------------------------------------
st.divider()
st.markdown(clean_html(f"""
<div class='section-header'>{T['sim_title_main']}</div>
<div class='section-sub'>{T['sim_title_sub']}</div>
"""), unsafe_allow_html=True)
st.markdown(T["sim_desc_long"]) 
st.info(T["sim_intro"]) # Expanded Intro

if st.button(T["sim_btn"]):
    years_mc = 5
    st.markdown(T["sim_narration"].format(years_mc))
    simulations = int(120 * (years_mc/5) * 5)
    
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
    net_color = "np-pos" if net_profit >= 0 else "np-neg"
    net_sign = "+" if net_profit >= 0 else ""
    
    c1, c2, c3 = st.columns(3)
    c1.metric(T["sim_lbl_cost"], f"{total_cost:,}")
    c2.metric(T["sim_lbl_return"], f"{total_win:,}")
    c3.markdown(f"""
        <div class='net-profit-box-mc'>
            <div class='net-profit-label-mc'>{T['sim_lbl_net']}</div>
            <div class='net-profit-value-mc {net_color}'>{net_sign}{net_profit:,}</div>
        </div>
    """, unsafe_allow_html=True)
    
    if jackpot_hit:
        st.balloons()
        st.success(T["sim_jackpot"])
    elif net_profit > 0:
        st.success(T["sim_res_win"])
    else:
        st.warning(T["sim_res_loss"])

# -----------------------------------------------
# 5. Scientific Validation (Chi-Square) - Exact Fix
# -----------------------------------------------
st.divider()
st.markdown(clean_html(f"""
<div class='section-header'>{T['val_title_main']}</div>
<div class='section-sub'>{T['val_title_sub']}</div>
"""), unsafe_allow_html=True)

observed_counts = collections.Counter(all_2digits)
for i in range(100):
    k = f"{i:02d}"
    if k not in observed_counts: observed_counts[k] = 0

obs = [observed_counts[f"{i:02d}"] for i in range(100)]
exp = [len(df)/100] * 100
chi2, p_value = stats.chisquare(obs, f_exp=exp)
degrees_of_freedom = 99
critical_value = stats.chi2.ppf(0.95, degrees_of_freedom)

# Fix HTML rendering issues by removing indentation inside the string
res_class = "sci-conclusion-pass" if p_value > 0.05 else "sci-conclusion-fail"
res_msg = T['sci_res_pass'] if p_value > 0.05 else T['sci_res_fail']

html_report = clean_html(f"""
<div class="sci-box">
<div class="sci-title">{T['sci_title']}</div>
<div class="sci-row">
<span>{T['sci_samples']}</span>
<span class="sci-val">{len(df)}</span>
</div>
<div class="sci-row">
<span>{T['sci_stat']}</span>
<span class="sci-val">{chi2:.2f}</span>
</div>
<div class="sci-row">
<span>{T['sci_crit']}</span>
<span class="sci-val">{critical_value:.2f}</span>
</div>
<div class="{res_class}">
{res_msg}
</div>
<div class="sci-desc">
{T['sci_exp_pass']}
</div>
<div class="sci-advice">
{T['sci_advice']}
</div>
</div>
""")
# Ensure no extra whitespace at start
html_report = html_report.strip()

st.markdown(html_report, unsafe_allow_html=True)


# -----------------------------------------------
# Footer (Larger font)
# -----------------------------------------------
st.markdown(clean_html(f"""
<div class="footer-advice">
{T['final_rec']}<br>
{T['footer']}
</div>
"""), unsafe_allow_html=True)
