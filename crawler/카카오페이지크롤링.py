from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from tqdm import tqdm
import pandas as pd
import os
import time

# 1. 드라이버 설정 (자동 설치)
options = Options()
options.add_argument('--headless')  # ✅ Jupyter용
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--window-size=1920,1080')

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get("https://page.kakao.com/content/48787313")
novel_title = driver.title.strip()
print(f"📚 웹소설 제목: {novel_title}")
time.sleep(5)

# 2. 목표 개수 & 저장소
MAX_COMMENTS = 100
all_comments = set()

# 3. tqdm 프로그레스바 생성
progress_bar = tqdm(total=MAX_COMMENTS, desc="댓글 수집 중", unit="개")

# 4. 수집 루프
while True:
    time.sleep(2)

    comment_elements = driver.find_elements(
        By.XPATH,
        '//span[contains(@class, "font-medium2") and contains(@class, "whitespace-pre-wrap")]'
    )

    for elem in comment_elements:
        text = elem.text.strip()
        if text and text not in all_comments:
            all_comments.add(text)
            tqdm.write(f"[{len(all_comments)}] {text}")
            progress_bar.update(1)

        if len(all_comments) >= MAX_COMMENTS:
            progress_bar.close()
            print("\n✅ 댓글 100개 수집 완료. 종료합니다.")
            break

    if len(all_comments) >= MAX_COMMENTS:
        break

    # 5. 다음 버튼 클릭 시도
    button_index = len(all_comments) + 1
    xpath = f'//*[@id="__next"]/div/div[2]/div[1]/div/div[2]/div[2]/div[3]/div/div[2]/div[{button_index}]'

    try:
        next_button = driver.find_element(By.XPATH, xpath)
        driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", next_button)
        tqdm.write("🔁 다음 댓글 페이지 로딩 중...\n")
        time.sleep(3)
    except (NoSuchElementException, ElementNotInteractableException):
        tqdm.write("❌ 더 이상 다음 버튼이 없거나 클릭 불가. 종료합니다.")
        break

# 종료
progress_bar.close()
driver.quit()

# 6. CSV 저장
output_dir = "data/raw"
os.makedirs(output_dir, exist_ok=True)

output_path = os.path.join(output_dir, "novel_comments.csv")
df = pd.DataFrame({"novel": [novel_title] * len(all_comments), "comment": list(all_comments)})
df.to_csv(output_path, index=False, encoding="utf-8-sig")

print(f"\n💾 댓글 저장 완료: {output_path}")