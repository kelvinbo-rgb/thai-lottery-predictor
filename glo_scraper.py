import requests
from bs4 import BeautifulSoup
import re
import datetime
import logging
from typing import Optional, Dict, Any
from curl_cffi import requests as crequests

class GLOScraper:
    """Enhanced Thai Lottery Scraper targeting Sanook/Official sources"""
    
    SANOOK_URL = "https://news.sanook.com/lotto/"
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    }

    def fetch_latest_results(self) -> Optional[Dict[str, Any]]:
        """
        Fetches the latest lottery results and the 'Gene Map' (Result Sheet) image.
        Uses curl_cffi for robust Cloudflare bypass if needed.
        """
        try:
            logging.info("🚀 Fetching latest lottery results from Sanook...")
            # Use curl_cffi to mimic Chrome 124
            response = crequests.get(self.SANOOK_URL, headers=self.HEADERS, impersonate="chrome124", timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 1. Extract Latest Draw Date
            date_text = ""
            date_elem = soup.find("h2", class_="lotto-check__title")
            if date_elem:
                date_text = date_elem.get_text(strip=True)
            
            # --- Thai Date Parsing ---
            # Example: "งวดวันที่ 16 เมษายน 2569"
            thai_months = {
                "มกราคม": 1, "กุมภาพันธ์": 2, "มีนาคม": 3, "เมษายน": 4,
                "พฤษภาคม": 5, "มิถุนายน": 6, "กรกฎาคม": 7, "สิงหาคม": 8,
                "กันยายน": 9, "ตุลาคม": 10, "พฤศจิกายน": 11, "ธันวาคม": 12
            }
            iso_date = datetime.date.today().strftime("%Y-%m-%d")
            match = re.search(r'(\d{1,2})\s+(\w+)\s+(\d{4})', date_text)
            if match:
                day = int(match.group(1))
                month = thai_months.get(match.group(2), 1)
                year = int(match.group(3)) - 543 # 2569 -> 2026
                iso_date = f"{year}-{month:02d}-{day:02d}"
            
            # 2. Extract Prize 1
            p1 = ""
            p1_elem = soup.find("strong", class_="lotto-check__number")
            if p1_elem:
                p1 = p1_elem.get_text(strip=True)
            
            # 3. Extract 2 Digits
            p2d = ""
            p2d_section = soup.find("div", class_="lotto-check__item", string=re.compile("เลขท้าย 2 ตัว"))
            if p2d_section:
                p2d_elem = p2d_section.find_next("strong", class_="lotto-check__number")
                if p2d_elem: p2d = p2d_elem.get_text(strip=True)
            else:
                # Fallback for 2 digits
                all_numbers = soup.find_all("strong", class_="lotto-check__number")
                if len(all_numbers) >= 4:
                    p2d = all_numbers[3].get_text(strip=True)

            # 4. Extract 3 Digits (Prefix and Suffix)
            pre3 = []
            sub3 = []
            # This is simplified, can be expanded to full list
            
            # 5. Extract "Gene Map" (Official Result Sheet Image)
            # Sanook usually has a link to the full image
            chart_url = ""
            img_elem = soup.find("img", alt=re.compile("ใบตรวจหวย"))
            if img_elem:
                chart_url = img_elem.get("src")
            
            if not p1:
                logging.warning("⚠️ Could not find Prize 1, check selectors.")
                return None

            return {
                "date": iso_date,
                "prize_1st": p1,
                "prize_2digits": p2d,
                "official_chart_url": chart_url,
                "timestamp": datetime.datetime.now().isoformat()
            }

        except Exception as e:
            logging.error(f"❌ Scraper Error: {e}")
            return None

if __name__ == "__main__":
    scraper = GLOScraper()
    print(scraper.fetch_latest_results())
