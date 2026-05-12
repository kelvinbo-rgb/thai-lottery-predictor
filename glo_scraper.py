import requests
import datetime
import logging
from typing import Optional, Dict, Any

class GLOScraper:
    def __init__(self):
        # 抛弃臃肿的浏览器内核，直接用轻量级 requests
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "Origin": "https://www.glo.or.th",
            "Referer": "https://www.glo.or.th/home-page"  # ✅ 最新的官方主页路由
        }

    def _get_fallback_date(self) -> str:
        """
        Smartly calculates the most recent likely lottery draw date.
        Thai lottery typically draws on the 1st and 16th.
        """
        today = datetime.date.today()
        year, month, day = today.year, today.month, today.day

        if day >= 16:
            return f"{year}-{month:02d}-16"
        elif day >= 2 and month == 5:
            # Special case: May 2nd (Labor Day shift)
            return f"{year}-05-02"
        elif day >= 1:
            return f"{year}-{month:02d}-01"
        else:
            # Go back to previous month
            prev_date = today.replace(day=1) - datetime.timedelta(days=1)
            prev_year, prev_month = prev_date.year, prev_date.month
            # Dec 30 is a common special draw day
            if prev_month == 12:
                return f"{prev_year}-12-30"
            return f"{prev_year}-{prev_month:02d}-16"

    def fetch_latest_results(self, target_date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Fetches lottery results via light-weight requests.
        If target_date is None, it uses GLO's default 'latest' behavior.
        """
        try:
            payload = {"date": target_date} if target_date else {}
            logging.info(f"🚀 Fetching official GLO results via requests (Target: {target_date or 'Latest'})...")
            
            # 使用 requests.post 替代 scrapling，极速且无底层依赖隐患
            response = requests.post(
                "https://www.glo.or.th/api/lottery/getLatestLottery", 
                json=payload,
                headers=self.headers,
                timeout=15
            )
            
            if response.status_code != 200:
                logging.error(f"❌ GLO API Error: Status {response.status_code}")
                return None
                
            data = response.json()
            res_data = data.get("response", {}).get("data", {})
            
            # If Solution A (empty date) returned null, trigger Solution B
            if not res_data and not target_date:
                fallback_date = self._get_fallback_date()
                logging.info(f"🔄 Solution A returned empty. Falling back to Solution B (Date: {fallback_date})...")
                return self.fetch_latest_results(fallback_date)
            
            if not res_data:
                logging.warning(f"⚠️ No results found in response data.")
                return None

            # Extracting with precise keys from GLO response
            actual_date = res_data.get("date", target_date)
            p1 = res_data.get("first", {}).get("number", [{}])[0].get("value", "")
            p2d = res_data.get("last2", {}).get("number", [{}])[0].get("value", "")
            pre3 = [item.get("value") for item in res_data.get("last3f", {}).get("number", [])]
            sub3 = [item.get("value") for item in res_data.get("last3b", {}).get("number", [])]
            
            chart_url = f"https://www.glo.or.th/mission/reward-payment/check-reward?date={actual_date}"

            if not p1:
                logging.warning("⚠️ Prize 1 is empty in the response.")
                return None

            return {
                "date": actual_date,
                "prize_1st": p1,
                "prize_2digits": p2d,
                "prize_pre_3digit": pre3,
                "prize_sub_3digits": sub3,
                "official_chart_url": chart_url,
                "timestamp": datetime.datetime.now().isoformat()
            }

        except Exception as e:
            logging.error(f"❌ Scraper Error: {e}")
            return None

if __name__ == "__main__":
    scraper = GLOScraper()
    print("--- Testing via requests (Latest) ---")
    print(scraper.fetch_latest_results())
