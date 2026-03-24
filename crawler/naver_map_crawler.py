"""
하맘 고객연락자동화 - 업체 정보 크롤러 (Selenium 기반)
B2B 업체 (인테리어, 청소, 커튼, 필름) 정보 수집

네이버 지도의 구조 변경에 대응하는 안정적인 Selenium 자동화 스크립트입니다.
"""

import time
import random
import re
import logging
from base64 import b64decode
import pandas as pd
import sqlite3
from datetime import datetime
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException

# 업종별 검색 키워드
CATEGORY_KEYWORDS = {
    "인테리어": ["인테리어", "인테리어 시공"],
    "청소": ["입주청소", "이사청소", "청소업체"],
    "커튼": ["커튼", "블라인드"],
    "필름": ["단열필름", "유리필름", "필름시공"],
    "어린이집": ["어린이집", "유치원", "놀이학교"],
    "관공서": ["주민센터", "시청", "구청", "보건소", "우체국", "관공서"],
    "시설": ["복지관", "체육센터", "센터", "요양원", "수련관"],
}

class NaverMapCrawler:
    CATEGORY_KEYWORDS = CATEGORY_KEYWORDS

    def __init__(self, headless=False, callback=None):
        self.callback = callback
        self.driver = None
        self._setup_driver(headless)

    def _setup_driver(self, headless):
        import sys
        
        options = Options()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1280,1024")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        if sys.platform.startswith('linux'):
            # Streamlit Cloud (Debian) 환경
            options.binary_location = '/usr/bin/chromium'
            service = Service('/usr/bin/chromedriver')
            self.driver = webdriver.Chrome(service=service, options=options)
        else:
            # Windows / 로컬 환경
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def _log(self, msg, capture=False):
        print(f"[크롤러] {msg}")
        if self.callback:
            screenshot = None
            if capture and self.driver:
                try:
                    screenshot = self.driver.get_screenshot_as_png()
                except:
                    pass
            try:
                self.callback(msg, screenshot=screenshot)
            except TypeError:
                self.callback(msg)

    def _switch_to_search_iframe(self):
        self.driver.switch_to.default_content()
        WebDriverWait(self.driver, 10).until(
            EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, "iframe#searchIframe"))
        )

    def _switch_to_entry_iframe(self):
        self.driver.switch_to.default_content()
        WebDriverWait(self.driver, 10).until(
            EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, "iframe#entryIframe"))
        )

    def search_businesses(self, keyword, region="", max_results=300):
        query = f"{region} {keyword}".strip()
        url = f"https://map.naver.com/p/search/{query}"
        self._log(f"검색 시작: {query} (최대 {max_results}건 전체 스크롤 시도)")
        
        self.driver.get(url)
        time.sleep(3)

        collected = []
        page = 1
        
        try:
            self._switch_to_search_iframe()
        except:
            self._log("검색 영역을 찾을 수 없습니다. 키워드를 확인해주세요.")
            return []

        while len(collected) < max_results:
            self._log(f"--- {page}페이지 스크롤 다운 중 ---")
            
            # 목록 끝까지 스크롤 반복 (네이버는 스크롤해야 목록이 나옴)
            for _ in range(5):
                try:
                    scroll_container = self.driver.find_element(By.CSS_SELECTOR, "#_pcmap_list_scroll_container")
                    self.driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);", scroll_container)
                    time.sleep(1)
                except Exception as e:
                    break
            
            time.sleep(2)
            
            # 목록 파싱 (범용 셀렉터 확장 - 부동산, 병원 등 포함)
            items = self.driver.find_elements(By.CSS_SELECTOR, "#_pcmap_list_scroll_container ul > li.VLTHu, #_pcmap_list_scroll_container ul > li.UEHAh, li[data-laim-exp-id]")
            if not items:
                items = self.driver.find_elements(By.CSS_SELECTOR, "#_pcmap_list_scroll_container li")
            
            self._log(f"현재 페이지에서 {len(items)}개 항목 발견", capture=True)
            
            for index in range(len(items)):
                if len(collected) >= max_results:
                    break
                    
                try:
                    # iframe 재전환 (상세 창 다녀온 후 필요)
                    self._switch_to_search_iframe()
                    
                    # element 갱신
                    current_items = self.driver.find_elements(By.CSS_SELECTOR, "#_pcmap_list_scroll_container ul > li.VLTHu, #_pcmap_list_scroll_container ul > li.UEHAh, li[data-laim-exp-id]")
                    if not current_items:
                        current_items = self.driver.find_elements(By.CSS_SELECTOR, "#_pcmap_list_scroll_container li")
                        
                    if index >= len(current_items):
                        continue
                        
                    item = current_items[index]
                    
                    # 클릭하여 우측 상세정보 열기 (부동산 포함 어떤 구조든 강제 클릭)
                    try:
                        name_el = item.find_element(By.CSS_SELECTOR, "a.place_bluelink, a.U70Fj, a.P7gyV, a.k4f_J, .TYaxT, .YwYLL")
                        name_text = name_el.text.strip()
                        self._log(f"[{len(collected)+1}] 파싱 중: {name_text}")
                        # 텍스트 대신 JS 강제 클릭으로 무조건 상세 페이지 오픈
                        self.driver.execute_script("arguments[0].click();", name_el)
                    except Exception as clk_e:
                        self.driver.execute_script("arguments[0].click();", item.find_element(By.TAG_NAME, "a"))
                    
                    
                    time.sleep(2.5) # 상세 프레임 로딩 대기
                    
                    # 상세 프레임으로 이동하여 정보 수집
                    detail = self._extract_detail_info(name_text)
                    if detail:
                        collected.append(detail)
                        self._log(f"   => 성공: {detail['전화번호']} | {detail['주소'][:15]}", capture=True)
                        
                        # 💡 [실시간 금고 저장] 1건 수집될 때마다 즉시 SQLite DB에 투입 (중간 Stop 방어)
                        try:
                            import sqlite3
                            conn = sqlite3.connect("hamom_database.db", check_same_thread=False)
                            cursor = conn.cursor()
                            cursor.execute('''
                                CREATE TABLE IF NOT EXISTS b2b_crawling_list (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    업체명 TEXT, 카테고리 TEXT, 주소 TEXT, 전화번호 TEXT, 이메일 TEXT,
                                    해시태그 TEXT, 검색카테고리 TEXT, 등록일시 DATETIME DEFAULT CURRENT_TIMESTAMP
                                )
                            ''')
                            # 중복 검사
                            cursor.execute("SELECT id FROM b2b_crawling_list WHERE 업체명=? AND 전화번호=?", (detail['업체명'], detail['전화번호']))
                            if not cursor.fetchone():
                                cursor.execute('''
                                    INSERT INTO b2b_crawling_list (업체명, 카테고리, 주소, 전화번호, 이메일, 해시태그, 검색카테고리)
                                    VALUES (?, ?, ?, ?, ?, ?, ?)
                                ''', (detail.get('업체명',''), detail.get('카테고리',''), detail.get('주소',''), 
                                      detail.get('전화번호',''), detail.get('이메일',''), detail.get('해시태그',''), query))
                                conn.commit()
                            conn.close()
                        except Exception as db_err:
                            self._log(f"DB 저장 에러: {db_err}")
                            
                    else:
                        self._log("   => 실패 (정보 누락)")
                        
                except Exception as e:
                    self._log(f"   => 항목 처리 중 오류: {e}")
                    pass

            if len(collected) >= max_results:
                break
                
            # 다음 페이지 이동
            self._switch_to_search_iframe()
            next_btn = self.driver.find_elements(By.CSS_SELECTOR, ".eUTV2")
            if len(next_btn) > 1 and next_btn[1].get_attribute("aria-disabled") == "false":
                next_btn[1].click()
                time.sleep(2)
                page += 1
            elif self.driver.find_elements(By.CSS_SELECTOR, "a.btn_next:not(.disabled)"):
                self.driver.find_element(By.CSS_SELECTOR, "a.btn_next").click()
                time.sleep(2)
                page += 1
            else:
                self._log("마지막 페이지입니다.")
                break

        return collected

    def _extract_detail_info(self, name_text):
        """entryIframe 내부에서 상세 정보 추출"""
        info = {
            "업체명": name_text,
            "카테고리": "",
            "전화번호": "",
            "이메일": "",
            "주소": "",
            "홈페이지": ""
        }
        
        try:
            self._switch_to_entry_iframe()
            
            # 주소
            try:
                addr_el = self.driver.find_element(By.CSS_SELECTOR, ".LDgIH")
                info["주소"] = addr_el.text.strip()
            except:
                pass
                
            # 카테고리
            try:
                cat_el = self.driver.find_element(By.CSS_SELECTOR, ".DJJvD")
                info["카테고리"] = cat_el.text.strip()
            except:
                pass
                
            # 전화번호
            try:
                phone_el = self.driver.find_element(By.CSS_SELECTOR, ".xlx7Q")
                info["전화번호"] = phone_el.text.strip()
            except:
                pass
                
            # 홈페이지/블로그/인스타 링크 찾기 및 클릭
            try:
                links = self.driver.find_elements(By.CSS_SELECTOR, ".jO09N a, .CHmQA a")
                for link in links:
                    href = link.get_attribute("href")
                    if href and "instagram.com" not in href and "naver.com" not in href:
                        if not info["홈페이지"]:
                            info["홈페이지"] = href
            except:
                pass
                
        except Exception as e:
            self._log(f"상세 정보 파싱 에러: {e}")
            return None
            
        # 홈페이지가 있으면 이메일 파싱 시도
        if info["홈페이지"]:
            info["이메일"] = self._extract_email_from_url(info["홈페이지"])
            
        return info

    def _extract_email_from_url(self, url):
        import requests
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, headers=headers, timeout=5)
            emails = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", resp.text)
            filtered = [
                e for e in set(emails)
                if not any(s in e.lower() for s in ["example", "sentry", "jquery", "png", "jpg", "css"])
            ]
            return filtered[0] if filtered else ""
        except:
            return ""

    def crawl_all_categories(self, region="", max_per_keyword=300, selected_cats=None):
        cats = selected_cats or list(CATEGORY_KEYWORDS.keys())
        all_results = []

        for category in cats:
            keywords = CATEGORY_KEYWORDS.get(category, [category])
            keyword = keywords[0]
            self._log(f"\n=== {category} (키워드: {keyword}) 크롤링 시작 ===")
            results = self.search_businesses(keyword, region, max_per_keyword)
            
            for r in results:
                r["검색카테고리"] = category
            all_results.extend(results)
            
        # 중복 제거
        df = pd.DataFrame(all_results)
        if not df.empty:
            df = df.drop_duplicates(subset=["업체명", "전화번호"])
            all_results = df.to_dict("records")
            
        self._log(f"총 {len(all_results)}건 수집 완료 (중복 제거)")
        return all_results

    def quit(self):
        if self.driver:
            self.driver.quit()
