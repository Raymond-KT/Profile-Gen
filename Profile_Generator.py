import streamlit as st
from openai import OpenAI
from googleapiclient.discovery import build
import requests
from io import BytesIO
from docx import Document
from docx.shared import Inches

# OpenAI API 설정
client = OpenAI(api_key=st.secrets["api_keys"]["openai"])

# Google Custom Search API 설정
def search_image(name, organization, position):
    query = f"{name} {organization} {position}"
    if not query.strip():
        return ""
    try:
        service = build("customsearch", "v1", developerKey=st.secrets["api_keys"]["google_custom_search"])
        res = service.cse().list(
            q=query,
            cx=st.secrets["api_keys"]["google_custom_search"],
            searchType="image",
            num=1
        ).execute()
        return res['items'][0]['link']
    except Exception as e:
        st.error(f"이미지 검색 중 오류가 발생했습니다: {e}")
        return ""

def search_additional_info(query):
    try:
        service = build("customsearch", "v1", developerKey=st.secrets["api_keys"]["google_custom_search"])
        res = service.cse().list(
            q=query,
            cx=st.secrets["api_keys"]["google_custom_search"],
            num=1
        ).execute()
        return res['items'][0]['snippet']
    except Exception as e:
        st.error(f"추가 정보 검색 중 오류가 발생했습니다: {e}")
        return ""

st.title('Profile Generator')

name = st.text_input('이름')
organization = st.text_input('소속')
position = st.text_input('직위')

profile_text = ""
image_url = ""

if st.button('프로필 생성'):
    if not name or not organization or not position:
        st.error("이름, 소속, 직위 정보를 모두 입력해 주세요.")
    else:
        additional_info = search_additional_info(f"{name} {organization} {position}")

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": f"""
GPT는 사용자가 제공한 이름, 소속, 직위 정보를 기반으로 대상 인물의 정형화된 한글 프로필을 생성한다. 프로필은 크게 기본사항과 인물평으로 구성되며, 워드 기준 총 2페이지로 분량을 맞춘다.

### 기본사항 (1페이지)

* **기본사항(연령, 학력), 주요 이력, 프로필 사진**을 포함한다.
* 프로필 사진은 해당 인물의 얼굴이 크게 보이는 단독 사진을 활용하며, 최신의 증명사진 양식의 사진을 우선하고, 얼굴을 가리지 않는 깔끔한 사진을 선정한다.
* 기본사항은 '1. 기본사항'을 표시하고 한칸 아래로 내려 연령과 고등학교 이상의 학력을 '-'를 사용해 구분하여 최근 순으로 구성한다.
  * 연령은 (현재연도 - 생년)을 기준으로 하며, '00세 ('00年生)'으로 표기한다.
  * 학력은 졸업 연도를 명시하고, 불확실한 정보는 '추정'으로 표기한다.
* 주요 이력은 '2. 주요이력'을 표시하고 한칸 아래로 내려 주요 경력사항(7개~10개)를 '-'를 사용해 구분하여 최근 순으로 구성한다.
  * 경력은 소속, 직위(혹은 직책)과 입사년월 ~ 퇴사년월을 명시하고, 불확실한 정보는 '추정'으로 표기한다.
  * 유사 경력은 최근 또는 고위직 기준으로 표기한다.

### 인물평 (2페이지)

!중요! 인물평은 '3. 인물평'을 표시하고 한칸 아래로 내려 **경력과 역량 기반 평가, 인품 기반 평가, 최근 근황 평가**로 나누어 작성하며, 각각의 항목은 명확한 핵심 메시지와 2~3개의 상세 메시지를 포함한다. ###인물평 아래 핵심 메시지와 상세 메시지만 나오도록 하고, **'경력 기반 평가, 인품 기반 평가, 최근 근황 평가' 문구는 표기하지 않는다.** 인물평의 문장은 명사로 끝맺음을 한다.

#### 경력과 역량 기반 평가

* □를 사용하여 핵심 메시지를 종합적이고 명료하게 작성한다.
* '-'를 사용하여 구체적인 Fact, 사례, 숫자 등으로 핵심 메시지를 뒷받침한다.

#### 인품 기반 평가

* □를 사용하여 대상 인물의 인품을 종합적이고 균형 있게 평가한 핵심 메시지를 작성한다.
* '-'를 사용하여 구체적인 사례와 평가를 기반으로 세부적인 설명을 제공한다.

#### 최근 근황 평가

* □를 사용하여 최근 2년 이내의 중요한 근황을 종합적으로 평가한 핵심 메시지를 작성한다.
* '-'를 사용하여 특정 사건의 발생 시기(년, 월)를 명시하고, 일반적으로 알려지지 않은 개념이나 사건은 부연설명을 포함하여 구체적으로 작성한다.

### 정보 출처 및 정확성

* GPT는 정보를 확인하기 위해 아래 웹 검색 정보를 활용한다. 
웹 검색 정보: {additional_info}
* 불확실하거나 논란이 있는 정보는 '추정' 또는 '논란 있음' 또는 '확인 필요'로 명시한다.

### 점검 및 문체

* 완성된 프로필은 오류가 없는지 2회 점검하며, 단편적이지 않고 입체적으로 서술되었는지 재확인한다.
* 완성 후 인물평에 중요한 정보가 누락되지 않았는지, 더 입체적으로 구성할 수 있는지 재확인한다.  
* 문체는 포멀하며, 기존 인물평 예시와 유사한 톤&매너를 유지한다.

위의 작성원칙을 반드시 준수하여 GPT가 프로필을 생성하도록 한다.

이름: {name}, 소속: {organization}, 직위: {position}

"""}
                ]
            )
            profile_text = response.choices[0].message.content
        except Exception as e:
            st.error(f"프로필 생성 중 오류가 발생했습니다: {e}")
            profile_text = "프로필 생성에 실패했습니다."

        image_url = search_image(name, organization, position)
        if image_url:
            st.image(image_url, caption='프로필 사진')

        # Display the profile text only once
        st.text_area('프로필', profile_text, height=1000, key='profile_text_area')
