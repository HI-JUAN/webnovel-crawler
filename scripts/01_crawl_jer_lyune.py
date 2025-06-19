# ipynb -> py 로 변경함 test 필요

import os
import csv
import datetime
import time
import logging

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException, TimeoutException, StaleElementReferenceException
)
from tqdm import tqdm

# ========== 1. 설정 ==========
chrome_driver_path = r'C:\Users\Shim\Downloads\chromedriver-win64\chromedriver-win64\chromedriver.exe'
TARGET_URL = "https://page.kakao.com/content/56505262"
MAX_COMMENTS = 5000        # 실제 수집 목표 (필요시 더 크게)
MAX_MORE_CLICK = 9999      # 사실상 무제한 클릭

# ========== 2. 크롬 옵션 ==========
options = webdriver.ChromeOptions()
# options.add_argument('--headless')  # 필요시 활성화
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--window-size=1920,1080')
prefs = {
    "profile.managed_default_content_settings.images": 2,
    "profile.managed_default_content_settings.stylesheets": 2,
}
options.add_experimental_option("prefs", prefs)

# ========== 3. 저장 경로 ==========
output_folder = os.path.join(os.path.expanduser('~'), 'Downloads', 'kakao_comments')
os.makedirs(output_folder, exist_ok=True)

def get_filename(episode_title):
    now = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    return os.path.join(output_folder, f"[{episode_title}]_댓글_{now}.csv")

def save_comments(episode_title, comments_collected):
    filename = get_filename(episode_title)
    with open(filename, 'w', encoding='utf-8-sig', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['번호', '작성자', '작성일', '댓글', '회차', '좋아요', '대댓글수'])
        for i, item in enumerate(comments_collected, 1):
            writer.writerow([
                i,
                item['user'],
                item['date'],
                item['comment'],
                item['episode'],
                item['like'],
                item['reply']
            ])
    print(f"\n✅ 총 {len(comments_collected)}개 댓글 저장 완료 → {filename}")
    return filename

# ========== 4. 로깅 ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ========== 5. 크롤링 시작 ==========
driver = webdriver.Chrome(service=Service(chrome_driver_path), options=options)
wait = WebDriverWait(driver, 10)
driver.get(TARGET_URL)

try:
    episode_title = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'h2.font-headline1'))
    ).text.strip()
except TimeoutException:
    episode_title = "알수없는회차"
print(f"📌 작품 제목: {episode_title}")

# 1. "더보기" 버튼 끝까지 클릭
more_click_count = 0
while True:
    try:
        more_div = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable(
                (By.XPATH, '(//div[./img[@alt="아래 화살표"]])[last()]')
            )
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", more_div)
        ActionChains(driver).move_to_element(more_div).click().perform()
        time.sleep(1.2)  # 네트워크 상황에 따라 조절
        more_click_count += 1
        if more_click_count >= MAX_MORE_CLICK:
            break
    except TimeoutException:
        logging.info("더 이상 '더보기' 버튼이 없습니다. 모든 댓글을 로드했습니다.")
        break
    except Exception as e:
        logging.error(f"'더보기' 버튼 클릭 중 오류: {e}")
        break

# 2. 전체 댓글 한 번에 수집 (중복·빈 댓글 모두 저장)
comments_collected = []
try:
    comment_blocks = driver.find_elements(By.XPATH, '//div[contains(@class, "flex-col") and contains(@class, "w-full")]')
    print(f"🔎 전체 댓글 블록 수: {len(comment_blocks)}")
    progress_bar = tqdm(total=min(MAX_COMMENTS, len(comment_blocks)), desc="댓글 수집 중", unit="개")
    for block in comment_blocks:
        try:
            user = block.find_element(By.XPATH, './/span[contains(@class, "font-small1-bold")]').text.strip() if block.find_elements(By.XPATH, './/span[contains(@class, "font-small1-bold")]') else ""
            date = block.find_element(By.XPATH, './/span[contains(@class, "font-small2") and contains(@class, "text-el-50")]').text.strip() if block.find_elements(By.XPATH, './/span[contains(@class, "font-small2") and contains(@class, "text-el-50")]') else ""
            comment = block.find_element(By.XPATH, './/span[contains(@class, "font-medium2")]').text.strip() if block.find_elements(By.XPATH, './/span[contains(@class, "font-medium2")]') else ""
            episode = block.find_element(By.XPATH, './/span[contains(@class, "font-small2") and contains(@class, "break-all")]').text.strip() if block.find_elements(By.XPATH, './/span[contains(@class, "font-small2") and contains(@class, "break-all")]') else ""
            like = block.find_element(By.XPATH, './/div[contains(@class,"mr-8pxr")]/span[contains(@class, "font-small2")]').text.strip().replace(',', '') if block.find_elements(By.XPATH, './/div[contains(@class,"mr-8pxr")]/span[contains(@class, "font-small2")]') else "0"
            reply = block.find_element(By.XPATH, './/div[contains(@class,"mr-8pxr")]/following-sibling::div/span[contains(@class, "font-small2")]').text.strip().replace(',', '') if block.find_elements(By.XPATH, './/div[contains(@class,"mr-8pxr")]/following-sibling::div/span[contains(@class, "font-small2")]') else "0"

            comments_collected.append({
                'user': user,
                'date': date,
                'comment': comment,
                'episode': episode,
                'like': like,
                'reply': reply
            })
            progress_bar.update(1)
            if len(comments_collected) >= MAX_COMMENTS:
                break
        except (NoSuchElementException, StaleElementReferenceException) as e:
            logging.warning(f"댓글 파싱 중 예외 발생: {e}")
            continue
        except Exception as e:
            logging.error(f"예상치 못한 댓글 파싱 오류: {e}")
            continue
    progress_bar.close()
except Exception as e:
    logging.error(f"전체 댓글 수집 중 오류: {e}")

# 3. 결과 저장 (브라우저는 종료하지 않음)
save_comments(episode_title, comments_collected)

print("✅ 크롤링이 완료되었습니다. 브라우저는 종료하지 않고 그대로 둡니다.")
