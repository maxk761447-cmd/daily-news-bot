import os
import smtplib
import time
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from google import genai
from google.genai.errors import APIError
import datetime

# 실행 시점의 현재 날짜를 '연도-월-일' 형식으로 가져옵니다 (예: 2026-05-28)
current_date = datetime.datetime.now().strftime("%Y-%m-%d")

# 1. 환경 변수 불러오기
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL")

NAVER_ID = os.environ.get("NAVER_CLIENT_ID")
NAVER_SECRET = os.environ.get("NAVER_CLIENT_SECRET")
KAKAO_KEY = os.environ.get("KAKAO_REST_API_KEY")

GOOGLE_API_KEY = os.environ.get("GOOGLE_SEARCH_API_KEY")
GOOGLE_CX = os.environ.get("GOOGLE_SEARCH_CX")

# ★ [보편적 핵심 키워드] 단편적 주제를 빼고, 언제나 대량의 뉴스가 쏟아지는 거시적 담론 40선
KEYWORDS = [
    # 기업 및 특화 기술 (Vantiva 특화, IT, 과학기술)
    "Vantiva", "LGU+", "SKT", "KT", "셋탑박스", "공유기", "무선 이동통신", "와이파이", "인공지능 트렌드", "글로벌 IT 산업", "첨단 과학 기술", "디지털 혁신", "차세대 인프라 기술",
    "미래 모빌리티", "정보통신 기술", "소프트웨어 산업", "차세대 테크", "컴퓨터 공학", "지능형 연결성", "데이터 경제", "사이버 안보 체계", "자동화 및 로봇공학",

    # 금융 및 거시 경제 (금융, 경제)
    "세계 경제 전망", "국제 금융 시장", "글로벌 증시", "거시경제 지표", "외환 및 환율", "거시경제", "세계 시장 전망", "공급망 재편과 무역", "통화 정책 및 규제",
    "국제 무역 정책", "글로벌 자산 시장", "대기업 경영 동향", "산업 트렌드", "재정 정책", "자산 시장 트렌드", "산업 지형 변화", "원자재 및 에너지 안보", "기업 경영 혁신", "지속 가능한 성장",

    # 정치 및 국제 정세 (정치, 사회, 지리)
    "국제 정치 뉴스", "외교 및 안보", "국제기구 활동", "정부 정책 동향", "지정학적 리스크", "국제 외교 질서", "국가 정책 동향", "글로벌 규제",
    "세계 지리 및 국경", "국가 간 협력", "정치 지형 변화", "법률 및 규제", "국제 분쟁",

    # 사회, 교육, 환경 (사회, 교육, 환경)
    "글로벌 사회 이슈", "현대 교육 제도", "인구 변화 동향", "기후변화와 위기", "에너지 패러다임", "인류 미래", "에너지 패러다임 전환", "미래 교육 혁신", "노동 및 고용 구조",
    "환경 보호 정책", "복지 및 노동", "대도시 사회 문제", "지속 가능한 개발", "인구 구조와 저출산", "생태계 및 생물다양성", "공중 보건 및 의료 과학", "도시 공학의 미래", "지속 가능한 사회",

    # 인문, 역사, 철학, 문화, 예술, 생활 (역사, 문화, 예술, 철학, 인문, 생활, 여가)
    "세계 역사와 문명", "현대 철학 담론", "글로벌 문화 트렌드", "세계 미술과 예술", "인문학 학술", "문명사적 관점", "인류학 및 역사적 발견", "현대 철학적 담론", "인문학적 가치", "글로벌 문화 메가트렌드", "대중문화와 미디어", "글로벌 여가 및 웰니스",
    "대중문화 동향", "문학 및 도서", "현대 라이프스타일", "글로벌 여가 문화", "연예", "여행", "핫플레이스", "개그", "유행어", "TV 드라마", "영화", "세계 유산 및 보존"
]

all_collected_raw_data = []

# 각 키워드별 채널 수집 진행
for kw in KEYWORDS:
    print(f"--- [{kw}] 거시 통찰 담론 수집 중... ---")
    
    # 2-1. 구글 국내 뉴스 (24시간 필터)
    try:
        base_url = "https://news.google.com/rss/search"
        query_with_time = f"{kw} when:24h"
        params = {"q": query_with_time, "hl": "ko", "gl": "KR", "ceid": "KR:ko"}
        rss_url = f"{base_url}?{urllib.parse.urlencode(params)}"
        
        req = urllib.request.Request(rss_url)
        root = ET.fromstring(urllib.request.urlopen(req).read())
        for item in root.findall('.//item')[:1]: 
            all_collected_raw_data.append(f"[출처:국내뉴스/구글] 제목: {item.find('title').text} / 링크: {item.find('link').text}")
    except Exception as e: pass

    # 2-2. 구글 글로벌 외신 뉴스 (24시간 필터)
    try:
        base_url = "https://news.google.com/rss/search"
        query_with_time = f"{kw} when:24h"
        params = {"q": query_with_time, "hl": "en", "gl": "US", "ceid": "US:en"}
        rss_url = f"{base_url}?{urllib.parse.urlencode(params)}"
        
        req = urllib.request.Request(rss_url)
        root = ET.fromstring(urllib.request.urlopen(req).read())
        for item in root.findall('.//item')[:1]: 
            all_collected_raw_data.append(f"[출처:국제뉴스/구글외신] 제목: {item.find('title').text} / 링크: {item.find('link').text}")
    except Exception as e: pass

    # 2-3. 구글 일반 웹 검색 연동
    try:
        encText = urllib.parse.quote(kw)
        url = f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx={GOOGLE_CX}&q={encText}&num=1"
        req = urllib.request.Request(url)
        response = urllib.request.urlopen(req)
        if response.getcode() == 200:
            data = json.loads(response.read().decode('utf-8'))
            for item in data.get('items', []):
                all_collected_raw_data.append(f"[출처:일반웹검색/구글] 제목: {item['title']} / 내용스니펫: {item.get('snippet', '')} / 링크: {item['link']}")
    except Exception as e: pass

    # 2-4. 네이버 뉴스 API (실시간 최신순)
    try:
        encText = urllib.parse.quote(kw)
        url = f"https://openapi.naver.com/v1/search/news.json?query={encText}&display=1&sort=date"
        req = urllib.request.Request(url)
        req.add_header("X-Naver-Client-Id", NAVER_ID)
        req.add_header("X-Naver-Client-Secret", NAVER_SECRET)
        response = urllib.request.urlopen(req)
        if response.getcode() == 200:
            data = json.loads(response.read().decode('utf-8'))
            for item in data.get('items', []):
                title = item['title'].replace("<b>", "").replace("</b>", "").replace("&quot;", '"')
                all_collected_raw_data.append(f"[출처:국내뉴스/네이버] 제목: {title} / 링크: {item['link']}")
    except Exception as e: pass

    # 2-5. 다음(카카오) 웹/뉴스 API
    try:
        encText = urllib.parse.quote(kw)
        url = f"https://dapi.kakao.com/v2/search/web?query={encText}&size=1"
        req = urllib.request.Request(url)
        req.add_header("Authorization", f"KakaoAK {KAKAO_KEY}")
        response = urllib.request.urlopen(req)
        if response.getcode() == 200:
            data = json.loads(response.read().decode('utf-8'))
            for item in data.get('documents', []):
                title = item['title'].replace("<b>", "").replace("</b>", "").replace("&quot;", '"')
                all_collected_raw_data.append(f"[출처:국내뉴스/다음] 제목: {title} / 링크: {item['url']}")
    except Exception as e: pass

    time.sleep(0.3)

# 데이터 병합
raw_context_data = "\n".join(all_collected_raw_data)

# --- 3. 제미나이 2.5 오케스트레이션 분석 엔진 ---
client = genai.Client(api_key=GEMINI_KEY)
prompt = f"""
너는 글로벌 정치, 경제, 사회, 문명의 거시적 흐름과 미시적인 흐름을 예리하게 상세 분석하여 최고 권위의 정책 결정권자들에게 핵심 인텔리전스를 제공하는 글로벌 수석 분석가야.
또한 너는 글로벌 매크로 트렌드와 미디어 빅데이터를 실시간으로 스크리닝하여 정계, 학계, 재계 최고위층에게 보고서를 제공하는 인사이트 브리핑을 제공하는 마스터 인텔리전스 분석가야.
아래 제공되는 광범위한 실시간 로우(Raw) 데이터를 바탕으로 완벽하게 분석하여 지시사항에 맞는 독보적인 구조화 된 리포트를 작성하고,
또한 지식 전반의 시각과 융합적 통찰을 키울 수 있는 격식 있는 구조화 리포트를 빌드해 줘.

[수집된 국내외 통합 실시간 데이터]
{raw_context_data}

[★ 구조화 및 분류 명령]
1. 최상위 목차는 단 두 개, 'I. 실시간 최신 국제 뉴스'와 'II. 실시간 최신 국내 뉴스'로만 이분법적 대분류를 수행하십시오.
2. 국제뉴스와 국내뉴스 각각의 하위 본문에는 아래의 17개 카테고리를 순서대로 '단 하나도 빠짐없이 고정 배치'하여 정밀 지능 매칭을 진행하고, 카테고리마다 괄호로 표시하십시요.
   - [금융, 경제, 사회, 정치, 이슈트렌드, 환경, 역사, 문화, 과학기술, 지리, 예술, 철학, 인문, 생활, 여가, IT, Vantiva 특화이슈]
3. 수집된 다채로운 데이터 풀(Pool)에서 17개 카테고리에 완벽히 부합하는 최신 트렌드를 파악해 노련하게 배치하되, 특정 순수 학술 분과(예: 철학, 지리 등)에 해당하는 당일 실시간 텍스트가 부족할 경우에는 절대로 허위 사실을 지어내지 말고 해당 섹션 제목 옆에 '(금일 관련 주요 이슈 없음)'을 명시하여 보고서의 최고 수준 객관성을 확보하십시오.

[★ 무조건 준수해야 할 편집 가이드라인]
1. 융합적 통찰 도출: 단편적인 팩트 전달을 넘어, 기술의 변화가 사회/경제/인문학에 미치는 상호 유기적인 영향(예: AI 확산이 노동 시장 구조와 철학적 윤리관에 미치는 영향 등)을 깊이 있게 엮어내십시오.
2. 보고서의 첫번째 실시간 최신 국제 뉴스에서 Vantiva 특화이슈는 맨 위에 보여주고, 실시간 최신 국내 뉴스에서는 "Vantiva 특화이슈"를 빼고 "통신사"로 카테고리를 추가로 만들고, 이동통신과 와이파이, 공유기, 셋탑박스 키워드 중심의 소식을 첫번째로 먼저 나열해주세요.
3. 하이엔드 번역 및 의역: 영문 외신 및 글로벌 웹 문서 리포트는 최고급 비즈니스 싱크탱크 보고서 수준의 정제되고 자연스러운 한국어로 전문 번역 및 압축 서술하십시오.
4. 포맷 구성: 분류된 각 카테고리별 핵심 이슈마다 한눈에 트렌드를 읽을 수 있는 요약형 헤드라인 제목과, 가독성이 뛰어난 [주요 핵심 요약 3줄(Bullet points)]을 기술하고, 하단에 원문 링크(Hyperlink)를 깔끔하게 임베딩하십시오. 여러 소스에 분포되어 있다면 출처를 [구글외신, 네이버, 구글일반웹] 형태로 병합 표기하십시오.
5. 소스 코드 표기 금지: 모바일 이메일 뷰어 등에서 완벽한 레이아웃 가독성을 뽐낼 수 있도록 정돈된 HTML 태그(h2, h3, p, ul, li, strong 등)만 사용하여 순수 본문 내용만 최종 리턴하십시오. ```html 같은 코드 블록 마크업 기호는 절대 포함하지 마십시오.
6. 중복 기사 원천 배제: 다양한 포털 채널과 일반 웹문서에 걸쳐 중복 공급된 동일 사건, 동일 보도자료 기반의 글은 완벽하게 필터링하여 가장 심도 있는 단 하나의 완성형 문장군으로 바인딩하십시오. 반드시 비슷하거나 중복 서술은 절대 금지합니다.
7. 마지막으로 결과로 나온 내용 본문을 반드시 읽기 쉽고 보기 좋게 재정렬 해주고, 출처 링크는 줄바꿈 두번해서 나열해주세요.
"""

models_to_try = ['gemini-2.5-flash', 'gemini-1.5-flash']
report_html = None

for model_name in models_to_try:
    print(f"{model_name} 마스터 엔진으로 통합 분석을 시작합니다...")
    success = False
    for attempt in range(3):
        try:
            response = client.models.generate_content(model=model_name, contents=prompt)
            report_html = response.text
            success = True
            print(f"{model_name} 마스터 인사이트 리포트 생성 완료!")
            break
        except APIError as e:
            print(f"[서버 에러] {e.message} (시도 {attempt + 1}/3)")
            if attempt < 2: time.sleep(10)
    if success: break

if not report_html:
    raise Exception("제미나이 리포트 변환 실패")

# --- 4. 이메일 발송 ---
msg = MIMEMultipart()
msg['From'] = EMAIL_USER
msg['To'] = RECEIVER_EMAIL
msg['Subject'] = f"[My Bot] Daily News Report {current_date}"

msg.attach(MIMEText(report_html, 'html'))

try:
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_USER, RECEIVER_EMAIL, msg.as_string())
    print("통합 통찰 리포트 메일 발송 성공!")
except Exception as e:
    print(f"이메일 전송 실패: {e}")
