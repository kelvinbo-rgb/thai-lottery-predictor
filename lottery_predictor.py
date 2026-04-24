# ------------------------------------------------------------
# thai-lottery-predictor / lottery_predictor.py
# ------------------------------------------------------------
import csv
import ast
import collections
import datetime
import random
import sys
import os
import re
import requests
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import credentials, firestore
from glo_scraper import GLOScraper

# --- Firestore Initialization ---
if not firebase_admin._apps:
    firebase_admin.initialize_app()
db = firestore.client()
COLLECTION_NAME = "lottery_history"

# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------
DATA_FILE = "historical_data.csv"
KAPOOK_HISTORY_URL = "https://lottery.kapook.com/history"

# ------------------------------------------------------------
# Date Utilities
# ------------------------------------------------------------
def parse_date(date_str: str) -> Optional[datetime.date]:
    """Parse date string in various formats to datetime.date object."""
    if not date_str:
        return None
    
    # Try M/D/YYYY format (e.g., 11/1/2025)
    try:
        return datetime.datetime.strptime(date_str.strip(), "%m/%d/%Y").date()
    except ValueError:
        pass
    
    # Try YYYY-MM-DD format (e.g., 2025-11-01)
    try:
        return datetime.datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
    except ValueError:
        pass
    
    # Try D/M/YYYY format
    try:
        return datetime.datetime.strptime(date_str.strip(), "%d/%m/%Y").date()
    except ValueError:
        pass
    
    return None


def format_date_for_csv(d: datetime.date) -> str:
    """Format date to M/D/YYYY for CSV storage."""
    return f"{d.month}/{d.day}/{d.year}"


def format_date_iso(d: datetime.date) -> str:
    """Format date to YYYY-MM-DD for display."""
    return d.strftime("%Y-%m-%d")


# ------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------
def load_data(filepath: str = None) -> List[Dict[str, str]]:
    """Load historical data from Firestore (descending by date)."""
    print("☁️ Fetching historical data from Firestore...")
    try:
        docs = db.collection(COLLECTION_NAME).order_by("date", direction=firestore.Query.DESCENDING).stream()
        data = []
        for doc in docs:
            d = doc.to_dict()
            # Ensure lists are strings to maintain compatibility with legacy parsing
            for key in ["prize_pre_3digit", "prize_sub_3digits", "nearby_1st", "prize_2nd", "prize_3rd", "prize_4th", "prize_5th"]:
                if key in d and isinstance(d[key], list):
                    d[key] = str(d[key])
            data.append(d)
        return data
    except Exception as e:
        print(f"❌ Firestore Load Error: {e}")
        return []


def parse_list_string(s: str) -> List[str]:
    """Safely parse a string representation of a Python list."""
    try:
        if not s:
            return []
        return ast.literal_eval(s)
    except Exception:
        return []


def save_new_draw(filepath: str, draw_data: Dict[str, Any]) -> None:
    """Save a new draw result to Firestore."""
    try:
        doc_id = draw_data["date"]
        # Ensure data is Firestore-friendly (converting string lists back to actual lists)
        db_row = {
            "date": draw_data["date"],
            "prize_1st": draw_data["prize_1st"],
            "prize_pre_3digit": draw_data["prize_pre_3digit"] if isinstance(draw_data["prize_pre_3digit"], list) else parse_list_string(str(draw_data["prize_pre_3digit"])),
            "prize_sub_3digits": draw_data["prize_sub_3digits"] if isinstance(draw_data["prize_sub_3digits"], list) else parse_list_string(str(draw_data["prize_sub_3digits"])),
            "prize_2digits": draw_data["prize_2digits"],
            "nearby_1st": draw_data.get("nearby_1st", []),
            "prize_2nd": draw_data.get("prize_2nd", []),
            "prize_3rd": draw_data.get("prize_3rd", []),
            "prize_4th": draw_data.get("prize_4th", []),
            "prize_5th": draw_data.get("prize_5th", []),
            "updated_at": firestore.SERVER_TIMESTAMP
        }
        db.collection(COLLECTION_NAME).document(doc_id).set(db_row)
        print(f"✅ Saved results for {doc_id} to Firestore.")
    except Exception as e:
        print(f"❌ Firestore Save Error: {e}")


def input_new_draw() -> Dict[str, Any] | None:
    """Prompt the user to manually input a new draw."""
    print("\n=== 录入新一期开奖数据 ===")
    print("提示: 只需录入主要奖项用于预测。")
    try:
        date = input("输入日期 (格式 M/D/YYYY, 例如 12/16/2025): ").strip()
        if not date:
            return None
        p1 = input("输入一等奖 (6位数): ").strip()
        print("输入前3位 (3 Digits Prefix):")
        p_pre_str = input("  请输入2个号码，用空格分开 (例如 '123 456'): ").strip()
        p_pre = p_pre_str.split() if p_pre_str else []
        print("输入后3位 (3 Digits Suffix):")
        p_sub_str = input("  请输入2个号码，用空格分开: ").strip()
        p_sub = p_sub_str.split() if p_sub_str else []
        p2 = input("输入后2位 (2 Digits Suffix): ").strip()
        return {
            "date": date,
            "prize_1st": p1,
            "prize_pre_3digit": p_pre,
            "prize_sub_3digits": p_sub,
            "prize_2digits": p2,
        }
    except Exception as e:
        print(f"输入错误: {e}")
        return None


def analyze_2digits(data: List[Dict[str, str]]):
    """Analyze 2-digit prize frequencies and recency."""
    history = []
    for row in data:
        val = str(row.get("prize_2digits", "")).strip()
        if val:
            if len(val) == 1:
                val = "0" + val
            history.append(val)
    total_draws = len(history)
    counter = collections.Counter(history)
    # last appearance (index from newest -> oldest)
    last_seen = {}
    for idx, num in enumerate(history):
        if num not in last_seen:
            last_seen[num] = idx
    most_common = counter.most_common(10)
    # recency (cold numbers)
    all_numbers = [f"{i:02d}" for i in range(100)]
    recency_list = []
    for num in all_numbers:
        seen_idx = last_seen.get(num, total_draws + 1)
        recency_list.append((num, seen_idx))
    recency_list.sort(key=lambda x: x[1], reverse=True)
    most_due = recency_list[:10]
    return most_common, most_due, counter


def analyze_3digits(data: List[Dict[str, str]]):
    """Analyze 3-digit prize frequencies (both prefix and suffix)."""
    all_3digits = []
    for row in data:
        pre = parse_list_string(row.get("prize_pre_3digit", "[]"))
        sub = parse_list_string(row.get("prize_sub_3digits", "[]"))
        if isinstance(pre, list):
            all_3digits.extend(pre)
        if isinstance(sub, list):
            all_3digits.extend(sub)
    counter = collections.Counter(all_3digits)
    return counter.most_common(10)

    counter = collections.Counter(all_3digits)
    return counter.most_common(10)


def perform_backtest(data: List[Dict[str, str]], years: int = 5):
    """
    Rolling Window Backtest: Simulate playing the lottery over the past N years
    using different strategies.
    
    1. Trend Strategy: Pick numbers based on weighted frequency of previous draws.
    2. Random Strategy: Pick numbers purely randomly.
    """
    print("\n" + "=" * 30)
    print(f"      ⏪ 历史回测 (过去 {years} 年)      ")
    print("=" * 30)
    
    # 1. 准备数据
    # 按日期从小到大排序 (Oldest -> Newest) 以便进行滚动回测
    chronological_data = sorted(data, key=lambda x: parse_date(x.get("date", "")) or datetime.date.min)
    
    # 找到起始点 (N年前)
    latest_date = parse_date(chronological_data[-1]["date"])
    start_date = latest_date.replace(year=latest_date.year - years)
    
    # 找到起始索引
    start_idx = 0
    for i, row in enumerate(chronological_data):
        d = parse_date(row["date"])
        if d and d >= start_date:
            start_idx = i
            break
            
    test_set = chronological_data[start_idx:]
    if not test_set:
        print("数据不足，无法回测。")
        return

    print(f"回测区间: {start_date} 至 {latest_date}")
    print(f"回测期数: {len(test_set)} 期")
    print("策略设定: 每期购买 3 注 2位数号码 (成本 240 THB), 中奖得 2000 THB")
    
    results = {
        "Trend": {"cost": 0, "win": 0, "hits": 0},
        "Random": {"cost": 0, "win": 0, "hits": 0}
    }
    
    # 2. 开始滚动回测
    for i in range(len(test_set)):
        # 当前要预测的这一期（“未来”）
        target_draw = test_set[i]
        target_val = str(target_draw.get("prize_2digits", "")).strip()
        if len(target_val) == 1: target_val = "0" + target_val
        
        # 可用的历史数据（截止到这一期之前的所有数据）
        # 注意：这里我们使用 start_idx + i 之前的所有数据作为“已知历史”
        # 这样严谨地模拟了当时只能看到过去数据的情况
        history_slice = chronological_data[:start_idx + i]
        
        # --- 策略 A: 趋势加权 (Trend) ---
        # 实时计算当时的热度
        history_nums = []
        for row in history_slice:
            val = str(row.get("prize_2digits", "")).strip()
            if val:
                if len(val) == 1: val = "0" + val
                history_nums.append(val)
        
        if history_nums:
            counter = collections.Counter(history_nums)
            pop = list(counter.keys())
            wgt = list(counter.values())
            # 模拟用户当时的随机选择（加权）
            picks_trend = random.choices(pop, weights=wgt, k=3)
        else:
            picks_trend = [f"{random.randint(0, 99):02d}" for _ in range(3)]
            
        # --- 策略 B: 完全随机 (Random) ---
        picks_random = [f"{random.randint(0, 99):02d}" for _ in range(3)]
        
        # --- 结算 ---
        # 成本
        results["Trend"]["cost"] += 240 # 买3注
        results["Random"]["cost"] += 240
        
        # 检查中奖
        if target_val in picks_trend:
            results["Trend"]["win"] += 2000
            results["Trend"]["hits"] += 1
            
        if target_val in picks_random:
            results["Random"]["win"] += 2000
            results["Random"]["hits"] += 1

    # 3. 输出结果
    for strat_name in ["Trend", "Random"]:
        res = results[strat_name]
        net = res["win"] - res["cost"]
        roi = (net / res["cost"]) * 100 if res["cost"] > 0 else 0
        print(f"\n[{strat_name} 策略]")
        print(f"  中奖次数: {res['hits']} / {len(test_set)}")
        print(f"  总投入: {res['cost']} | 总回报: {res['win']}")
        print(f"  净盈亏: {net} THB (ROI: {roi:.2f}%)")

    # 结论分析
    diff = results["Trend"]["hits"] - results["Random"]["hits"]
    print("\n🧐 [回测结论]")
    if abs(diff) <= 2: # 差异极小
        print("  两种策略表现几乎一致！这再次验证了彩票的随机游走性质。")
        print("  历史趋势并没有带来显著的超额收益。")
    elif diff > 0:
        print(f"  趋势策略略微领先 ({diff} 次)，但这可能仅仅是运气波动。")
    else:
        print(f"  随机策略竟然反超了 ({abs(diff)} 次)！说明追热号并不总是有效。")


def perform_simulation_and_analysis():
    """
    Perform a Monte Carlo simulation (Theoretical Probability) 
    to demonstrate long-term outcomes and Expected Value (EV).
    Includes ALL prize tiers (Jackpot, etc.) for accuracy.
    """
    print("\n" + "=" * 30)
    print("      💰 纯概率模拟 (含头奖全概率)      ")
    print("=" * 30)
    print("说明: 本次模拟包含了从【一等奖】到【末两位】的所有中奖可能。")
    print("      每期买 1 张，完全随机，看看运气如何。")
    
    # 完整版泰国彩票奖金结构 (Ticket Price 80 THB)
    # 概率基于 1,000,000 张作为一个完整组
    ticket_price = 80
    prizes = [
        {"name": "一等奖",   "prize": 6000000, "count": 1},
        {"name": "二等奖",   "prize": 200000,  "count": 5},
        {"name": "三等奖",   "prize": 80000,   "count": 10},
        {"name": "四等奖",   "prize": 40000,   "count": 50},
        {"name": "五等奖",   "prize": 20000,   "count": 100},
        {"name": "邻近奖",   "prize": 100000,  "count": 2},
        {"name": "前/后三",  "prize": 4000,    "count": 4000}, # 2个前三 + 2个后三 (各1000张)
        {"name": "末两位",   "prize": 2000,    "count": 10000},
    ]
    
    # 1. 计算精确期望值 (EV)
    total_value_in_pool = 0
    total_tickets = 1000000
    
    for p in prizes:
        total_value_in_pool += p["prize"] * p["count"]
        
    expected_return = total_value_in_pool / total_tickets
    loss_per_ticket = ticket_price - expected_return
    roi = (expected_return - ticket_price) / ticket_price * 100
    
    print(f"🎫 单张彩票真实数学价值: {expected_return:.2f} THB")
    print(f"   (其中一等奖贡献 6.0 THB，末两位贡献 20.0 THB)")
    print(f"💸 实际票价成本: {ticket_price} THB")
    print(f"📉 每买一张平均亏损: {loss_per_ticket:.2f} THB (ROI: {roi:.2f}%)")
    
    # 2. 模拟未来 5 年 (120期)，每期买 1 张
    print("\n[模拟] 假设每期坚持买 1 张，持续 5 年 (120期)...")
    total_cost = 0
    total_win = 0
    jackpot_hit = False
    
    simulations = 120
    for _ in range(simulations):
        total_cost += ticket_price
        
        # 模拟一次抽奖 (生成 0 到 999,999 的随机数)
        # 假设我们买的号码是 000000 (任意一个固定号码效果一样)
        winning_number = random.randint(0, 999999)
        
        # 简化判定逻辑：直接按概率判定是否中奖
        # 这种方法虽然不像对比数字那样直观，但在数学上是等价且高效的
        
        rand_val = random.random() # 0.0 到 1.0
        
        # 判定是否中各级奖项 (互斥叠加近似法，或者独立判定)
        # 为简单起见，我们独立判定每个奖项（因为一张票可能同时中多个奖）
        # 比如中了一等奖，也必然中末两位吗？不一定，泰国彩票规则比较独立。
        
        current_win = 0
        
        # 1. 末两位 (1/100)
        if random.random() < (10000 / 1000000):
            current_win += 2000
            
        # 2. 前/后三 (4/1000)
        if random.random() < (4000 / 1000000):
            current_win += 4000
            
        # 3. 一等奖 (1/1,000,000) - 极难！
        if random.random() < (1 / 1000000):
            current_win += 6000000
            jackpot_hit = True
            print("   🤯 天呐！模拟中竟然中了一等奖 (600万)！")
            
        # 4. 其他小奖 (概率总和约为 167/1,000,000)
        # 二等~五等 + 邻近
        other_prob = (5+10+50+100+2) / 1000000
        if random.random() < other_prob:
            # 简单给个平均值 30000 吧，因为种类太多
            current_win += 30000
            
        total_win += current_win

    net_profit = total_win - total_cost
    
    print(f"   总投入: {total_cost} THB")
    print(f"   总奖金: {total_win} THB")
    print(f"   净盈亏: {net_profit} THB")
    
    if jackpot_hit:
        print("   💡 点评: 这次模拟属于极度罕见的【幸存者偏差】。请勿当真！")
    elif net_profit > 0:
        print("   💡 点评: 运气不错，小赚一笔！主要是靠运气而非策略。")
    else:
        print("   💡 点评: 即使算上所有大奖概率，长期看依然是亏损的。")
        
    print("\n>>> 最终建议: 将彩票视为【消费】而非【投资】。祝您好运！")


def perform_chi_square_test(data: List[Dict[str, str]]):
    """
    Perform a Chi-Square Goodness of Fit Test on 2-digit numbers (00-99).
    Null Hypothesis (H0): The lottery is fair (all numbers have equal probability).
    Alternative Hypothesis (H1): The lottery is biased (some numbers appear significantly more/less).
    """
    history = []
    for row in data:
        val = str(row.get("prize_2digits", "")).strip()
        if val:
            if len(val) == 1: val = "0" + val
            history.append(val)
    
    total_draws = len(history)
    if total_draws == 0:
        return

    # Expected frequency for each number (00-99) if perfectly random
    expected = total_draws / 100.0
    
    # Observed frequency
    counter = collections.Counter(history)
    
    # Calculate Chi-Square Statistic: sum((Observed - Expected)^2 / Expected)
    chi_square_stat = 0.0
    for i in range(100):
        num_str = f"{i:02d}"
        observed = counter.get(num_str, 0)
        chi_square_stat += ((observed - expected) ** 2) / expected

    # Degrees of Freedom = Number of categories - 1 = 100 - 1 = 99
    # Critical Value for df=99 at p=0.05 is approximately 124.34
    critical_value = 124.34
    
    print(f"样本总量: {total_draws} 期")
    print(f"卡方统计量 (Chi-Square): {chi_square_stat:.2f}")
    print(f"临界值 (p=0.05, df=99): {critical_value}")
    
    if chi_square_stat < critical_value:
        print("\n✅ [结论] 分布均匀 (接受假设 H0)")
        print("   数据表现为真正的随机分布。历史“热号”只是统计噪音，不代表未来趋势。")
        print("   建议：使用【完全随机推荐】策略。")
    else:
        print("\n⚠️ [结论] 发现偏差 (拒绝假设 H0)")
        print("   数据分布存在显著不均匀性。可能有物理偏差或样本巧合。")
        print("   建议：稍微关注“热号”或“冷号”，但仍需谨慎。")



# ------------------------------------------------------------
# Web Scraping - Kapook (2568 / 2025)
# ------------------------------------------------------------
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://lottery.kapook.com/",
    "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7"
}

# Thai month names to number mapping
THAI_MONTHS = {
    "มกราคม": 1, "กุมภาพันธ์": 2, "มีนาคม": 3, "เมษายน": 4,
    "พฤษภาคม": 5, "มิถุนายน": 6, "กรกฎาคม": 7, "สิงหาคม": 8,
    "กันยายน": 9, "ตุลาคม": 10, "พฤศจิกายน": 11, "ธันวาคม": 12
}


def parse_thai_date(thai_date_str: str) -> Optional[datetime.date]:
    """Parse Thai date string like '1 ธันวาคม 2568' to datetime.date."""
    try:
        parts = thai_date_str.strip().split()
        if len(parts) < 3:
            return None
        day = int(parts[0])
        month = THAI_MONTHS.get(parts[1], 0)
        thai_year = int(parts[2])
        gregorian_year = thai_year - 543  # Convert Thai year to Gregorian
        if month == 0:
            return None
        return datetime.date(gregorian_year, month, day)
    except Exception:
        return None


def get_kapook_draw_links() -> List[Dict[str, Any]]:
    """Get list of draw date links from Kapook history page."""
    try:
        resp = requests.get(KAPOOK_HISTORY_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"⚠️ 无法访问 Kapook 网站: {e}")
        return []
    
    soup = BeautifulSoup(resp.text, "html.parser")
    links = []
    
    # Find all links that match the pattern /check/DDMMYY
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        if "/check/" in href:
            # Extract date code from URL like /check/011268
            match = re.search(r"/check/(\d{6})", href)
            if match:
                date_code = match.group(1)
                # Parse DDMMYY format
                day = int(date_code[0:2])
                month = int(date_code[2:4])
                thai_year_short = int(date_code[4:6])
                thai_year = 2500 + thai_year_short  # e.g., 68 -> 2568
                gregorian_year = thai_year - 543  # 2568 -> 2025
                
                try:
                    draw_date = datetime.date(gregorian_year, month, day)
                    full_url = f"https://lottery.kapook.com/check/{date_code}"
                    links.append({
                        "date": draw_date,
                        "url": full_url,
                        "date_code": date_code
                    })
                except ValueError:
                    continue
    
    # Remove duplicates and sort by date (newest first)
    seen = set()
    unique_links = []
    for link in links:
        if link["date_code"] not in seen:
            seen.add(link["date_code"])
            unique_links.append(link)
    
    unique_links.sort(key=lambda x: x["date"], reverse=True)
    return unique_links


def fetch_draw_data_from_kapook(url: str, expected_date: datetime.date) -> Optional[Dict[str, Any]]:
    """Fetch draw data from a specific Kapook draw page."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"  ⚠️ 无法访问 {url}: {e}")
        return None
    
    soup = BeautifulSoup(resp.text, "html.parser")
    
    # Find prize numbers in the page
    # The page structure uses specific div classes for each prize
    
    # Try to find first prize (6 digits)
    first_prize = None
    last_two = None
    first_three = []
    last_three = []
    
    # Look for the prize numbers in the page text
    text = soup.get_text()
    
    # Find 6-digit first prize
    first_prize_match = re.search(r'รางวัลที่\s*1[^\d]*(\d{6})', text)
    if first_prize_match:
        first_prize = first_prize_match.group(1)
    
    # Find last 2 digits
    last_two_match = re.search(r'เลขท้าย\s*2\s*ตัว[^\d]*(\d{2})', text)
    if last_two_match:
        last_two = last_two_match.group(1)
    
    # Find first 3 digits (usually 2 numbers)
    first_three_matches = re.findall(r'เลขหน้า\s*3\s*ตัว[^\d]*(\d{3})[^\d]*(\d{3})?', text)
    if first_three_matches:
        for match in first_three_matches:
            for num in match:
                if num:
                    first_three.append(num)
    
    # Find last 3 digits (usually 2 numbers)
    last_three_matches = re.findall(r'เลขท้าย\s*3\s*ตัว[^\d]*(\d{3})[^\d]*(\d{3})?', text)
    if last_three_matches:
        for match in last_three_matches:
            for num in match:
                if num:
                    last_three.append(num)
    
    # If we couldn't find the data, try alternative patterns
    if not first_prize:
        # Try finding any 6-digit number that could be the first prize
        all_six_digit = re.findall(r'\b(\d{6})\b', text)
        if all_six_digit:
            first_prize = all_six_digit[0]
    
    if not last_two:
        # Try finding 2-digit patterns
        two_digit_matches = re.findall(r'\b(\d{2})\b', text)
        if two_digit_matches:
            # Usually the last two digits appear after the first prize
            last_two = two_digit_matches[0] if len(two_digit_matches) > 0 else None
    
    if first_prize and last_two:
        return {
            "date": format_date_for_csv(expected_date),
            "prize_1st": first_prize,
            "prize_pre_3digit": first_three if first_three else ["000", "000"],
            "prize_sub_3digits": last_three if last_three else ["000", "000"],
            "prize_2digits": last_two,
        }
    
    return None


def auto_update_data() -> None:
    """Update local CSV with any missing draws from Kapook."""
    data = load_data(DATA_FILE)
    if not data:
        print("⚠️ 数据库为空，无法确定最新日期。请手动输入数据。")
        return
    
    # Parse all existing dates
    existing_dates = set()
    latest_date = None
    for row in data:
        d = parse_date(row.get("date", ""))
        if d:
            existing_dates.add(d)
            if latest_date is None or d > latest_date:
                latest_date = d
    
    if not latest_date:
        print("⚠️ 无法解析数据库中的日期。")
        return
    
    print(f"当前最新日期为 {format_date_for_csv(latest_date)}，开始从 Kapook 拉取缺失记录…")
    
    # Get all draw links from Kapook
    print("正在获取 Kapook 开奖日期列表...")
    draw_links = get_kapook_draw_links()
    
    if not draw_links:
        print("⚠️ 无法从 Kapook 获取开奖日期列表。")
        return
    
    print(f"找到 {len(draw_links)} 个开奖日期链接。")
    
    # Filter to current year and previous year draws that are missing
    current_year = datetime.date.today().year
    missing_draws = []
    for link in draw_links:
        if link["date"].year >= (current_year - 1) and link["date"] not in existing_dates:
            missing_draws.append(link)
    
    if not missing_draws:
        print("🔎 没有发现新记录，数据库已经是最新的。")
        return
    
    print(f"发现 {len(missing_draws)} 个缺失的历史记录，开始抓取...")
    
    # Fetch data for each missing draw
    new_draws = []
    for link in missing_draws:
        print(f"  正在抓取 {format_date_for_csv(link['date'])}...")
        draw_data = fetch_draw_data_from_kapook(link["url"], link["date"])
        if draw_data:
            new_draws.append(draw_data)
            print(f"    ✓ 成功获取数据: 头奖={draw_data['prize_1st']}, 末两位={draw_data['prize_2digits']}")
        else:
            print(f"    ✗ 无法解析数据，跳过")
    
    if not new_draws:
        print("⚠️ 未能成功抓取任何新数据。")
        return
    
    # Save new draws to CSV
    for draw in sorted(new_draws, key=lambda x: parse_date(x["date"]) or datetime.date.min):
        save_new_draw(DATA_FILE, draw)
    
    print(f"🎉 已成功写入 {len(new_draws)} 条新记录！")


def sort_data_by_date(data: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Sort data by date (newest first)."""
    def get_date_key(row):
        d = parse_date(row.get("date", ""))
        if d:
            return d
        return datetime.date.min
    
    return sorted(data, key=get_date_key, reverse=True)



# ------------------------------------------------------------
# Access Control (Privacy Protection)
# ------------------------------------------------------------
def check_access_permission():
    """
    Simulate a privacy lock.
    1. Checks for a Password.
    2. Checks if current time is within allowed window (Optional).
    """
    # 1. 设定密码 (您可以随时修改这个密码)
    # Pro Tip: 在手机上使用时，可以防止别人拿你手机乱看
    SECRET_PASSWORD = "888" 
    
    # 2. 设定允许访问的时间段 (例如: 每天 08:00 到 22:00)
    # 如果不需要时间限制，可以将 START_HOUR 设为 0, END_HOUR 设为 24
    START_HOUR = 0 
    END_HOUR = 24
    
    # --- 检查时间 ---
    now = datetime.datetime.now()
    if not (START_HOUR <= now.hour < END_HOUR):
        print(f"⛔ 访问被拒绝: 当前时间 {now.strftime('%H:%M')} 不在允许访问时段 ({START_HOUR}:00-{END_HOUR}:00)。")
        sys.exit(1)
        
    # --- 检查密码 ---
    # 注意: 在命令行模式下会显示输入字符。在 Web App 模式下会是隐藏的圆点。
    print("\n🔒 系统已锁定 (Privacy Lock)")
    user_input = input("请输入访问密码: ").strip()
    
    if user_input != SECRET_PASSWORD:
        print("❌ 密码错误！拒绝访问。")
        sys.exit(1)
    
    print("🔓 验证通过！欢迎回来。\n")


# ------------------------------------------------------------
# Main Execution Flow
# ------------------------------------------------------------
def main() -> None:
    # 🔒 启动前先检查权限
    check_access_permission()
    
    print("正在加载历史数据...")
    data = load_data(DATA_FILE)
    data = sort_data_by_date(data)
    
    if data:
        print(f"当前数据库共 {len(data)} 条记录。")
        # Get the actual latest date
        latest_date = parse_date(data[0].get("date", ""))
        if latest_date:
            print(f"最新一期记录日期: {format_date_for_csv(latest_date)}")
        else:
            print(f"最新一期记录日期: {data[0].get('date', 'Unknown')}")
    
    print("\n[功能选择]")
    print("1. 🔮 直接开始预测")
    print("2. 📝 录入新开奖数据")
    print("3. 🌐 自动从 Kapook 抓取缺失数据并更新数据库")
    choice = input("请输入选项 (1/2/3): ").strip()
    
    if choice == "2":
        new_draw = input_new_draw()
        if new_draw:
            save_new_draw(DATA_FILE, new_draw)
            data = load_data(DATA_FILE)
            data = sort_data_by_date(data)
            print("数据已更新，即将开始预测...")
    elif choice == "3":
        auto_update_data()
        data = load_data(DATA_FILE)
        data = sort_data_by_date(data)
        print("数据已更新，即将开始预测...")
    
    # ---------------------------------------------------------
    print("\n" + "=" * 30)
    print("      正在分析数据模型         ")
    print("=" * 30)
    
    # 2-Digit Analysis
    print("\n[分析] 2位数奖项 (00-99)...")
    top_freq_2, top_due_2, counter_2 = analyze_2digits(data)
    print("\n=== 2位数预测 (基于大数据频率 - Hot) ===")
    print("Top 5 热门号码 (出现次数最多):")
    for num, count in top_freq_2[:5]:
        print(f"  号码 {num}: 出现 {count} 次")
    print("\n=== 2位数预测 (基于遗漏值 - Cold) ===")
    print("Top 5 冷门号码 (最久未开出):")
    for num, draws_ago in top_due_2[:5]:
        print(f"  号码 {num}: 已经 {draws_ago} 期未出现")
    # Weighted Random Choice
    population = list(counter_2.keys())
    weights = list(counter_2.values())
    
    print("\n=== 🔮 号码推荐策略 ===")
    
    # Strategy 1: Weighted (Trend following)
    if population:
        prediction_weighted = random.choices(population, weights=weights, k=3)
        print(f"1. [趋势策略] 综合算法推荐 (追热): {', '.join(set(prediction_weighted))}")
        print("   (逻辑: 假设历史存在惯性，权重偏向热号)")

    # Strategy 2: True Random (Scientific)
    true_random = [f"{random.randint(0, 99):02d}" for _ in range(3)]
    print(f"2. [科学策略] 完全随机推荐 (数学最优): {', '.join(set(true_random))}")
    print("   (逻辑: 承认独立事件本质，拒绝赌徒谬误)")

    # ---------------------------------------------------------
    print("\n" + "=" * 30)
    print("      🧪 科学有效性检验 (Beta)      ")
    print("=" * 30)
    
    perform_chi_square_test(data)
    
    # 3-Digit Analysis
    print("\n[分析] 3位数奖项...")
    top_freq_3 = analyze_3digits(data)
    print("\n=== 3位数热门推荐 ===")
    for num, count in top_freq_3[:5]:
        print(f"  号码 {num}: 出现 {count} 次")
    print("\n预测完成。")
    
    # 投资回报与风险模拟
    perform_backtest(data, years=5)
    perform_simulation_and_analysis()


if __name__ == "__main__":
    main()jules_session_7382999441564755154