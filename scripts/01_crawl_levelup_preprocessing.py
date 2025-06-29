import pandas as pd
import os

# 절대 경로 기반 CSV 파일 경로
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path = os.path.join(base_dir, 'data', 'raw', 'crawl_nahonja_levelup.csv')

df = pd.read_csv(path)

# 연관 댓글 수의 숫자 단위 콤마 제거 적용
def remove_comma(x):
    return x.replace(',','')

df['연관 댓글 수'] = df['연관 댓글 수'].apply(remove_comma)

# 문자 '댓글 달기'를 0으로 바꿔주는 함수 적용
def str_to_int(x):
    return x.replace('댓글 달기','0')
    
df['연관 댓글 수'] = df['연관 댓글 수'].apply(str_to_int)

# 좋아요 수의 숫자 단위 콤마 제거 적용

df['좋아요 수'] = df['좋아요 수'].apply(remove_comma)

# 조건문을 적용시켜서 단위 '만' 전처리 적용
def remove_man(value):
    value = str(value).strip()
    if '만' in value:
        # 단위 '만' 제거 후 float 변환 * 10000, int 변환
        return int(float(value.replace('만', '')) * 10000)
    else:
        # 콤마 제거 후 int 변환
        return int(value.replace(',', ''))

    
df['좋아요 수'] = df['좋아요 수'].apply(remove_man)

# 날짜 컬럼을 datetime 형식으로 변환
df['날짜'] = pd.to_datetime(df['날짜'], format='%y.%m.%d')


# 정렬용 회차 번호 전처리 코드
import pandas as pd
import re

def process_episode_order(row):
    text = row['화수']
    # 괄호 제거
    text_clean = re.sub(r"\(.*?\)", "", text)

    # 시리즈 구분
    if "후일담" in text_clean:
        series = "후일담"
    elif "외전" in text_clean:
        series = "외전"
    else:
        series = "본편"

    # 회차 번호 추출
    match = re.search(r"(\d+)\s*화", text_clean)
    if match:
        episode_number = int(match.group(1))
    else:
        episode_number = 0  # 또는 NaN 처리

    # 정렬용 회차 번호 생성 (총 회차 271편 = 본편 244편 + 외전 21편 + 후일담 6편)
    if series == "본편":
        episode_order = episode_number
    elif series == "외전":
        episode_order = 244 + episode_number
    elif series == "후일담":
        episode_order = 265 + episode_number
    else:
        episode_order = None

    return pd.Series([series, episode_number, episode_order],
                     index=["시리즈", "회차 번호", "정렬용 회차 번호"])

# 데이터프레임 df가 있다고 가정
df[["시리즈", "회차 번호", "정렬용 회차 번호"]] = df.apply(process_episode_order, axis=1)


# 이후 정렬:
df_sorted = df.sort_values(by="정렬용 회차 번호", ascending=True).reset_index(drop=True)

#---정렬용 회차 번호 컬럼의 숫자가 우리가 생각하는 회차 순서라고 생각하면 편하다---
#댓글 전처리 시작

# 댓글에 \n을 띄어쓰기로 변환시키는 코드
def enter_to_space(x):
    return x.replace('\n',' ')

df_sorted['댓글'] = df_sorted['댓글'].apply(enter_to_space)

# 여러 개의 연속된 공백(스페이스, 개행, 탭 등)을 스페이스 1개로 치환 & 문자열 앞뒤의 공백을 제거
df_sorted['댓글'] = df_sorted['댓글'].str.replace(r"\s+", " ", regex=True).str.strip()

# 저장 경로 설정
output_folder = os.path.join('data', 'processed')
os.makedirs(output_folder, exist_ok=True)

# CSV 경로 설정
csv_path = os.path.join(output_folder, 'processed_nahonja_levelup.csv')

# CSV로 저장
df_sorted.to_csv(csv_path, index=False, encoding='utf-8-sig')
