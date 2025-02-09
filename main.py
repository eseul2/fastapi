import re
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import openai
import os
from dotenv import load_dotenv
 

# 환경 변수 로드 확인
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

# OpenAI 클라이언트 선언 (타임아웃 설정 추가)
client = openai.OpenAI(api_key=openai_api_key)

app = FastAPI()

# ✅ CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 목표별 가이드라인을 미리 설정
goal_guidelines = {
    "다이어트": """체중 감량을 위해 하루 **1,300kcal** 기준으로 식단을 구성해줘.
    - **탄수화물, 단백질, 지방 비율**을 **5:3:2**로 맞춰야 해.
    - **단백질 섭취 필수** (닭가슴살, 생선, 달걀, 두부, 콩류, 그릭요거트 등).
    - **트랜스지방(튀긴 음식, 마가린) 피하기, 불포화지방(아보카도, 견과류, 올리브오일) 섭취**.
    - **한식 위주**로 구성하되, 균형 잡힌 영양 섭취가 가능하도록 서양식도 일부 허용.""",

    "당 줄이기": """혈당을 안정적으로 유지할 수 있는 저당 식단을 제공해야 해.
    - **매끼 일정한 시간에 정해진 분량을 규칙적으로 섭취**.
    - 하루 섭취량 안에서 **6가지 식품군을 골고루 포함**.
    - **단당류(설탕, 꿀, 과당) 섭취 제한**.
    - **섬유소가 풍부한 식사를 제공** (채소류, 해조류, 버섯류).
    - **저열량 식품 추천** (곤약, 우뭇가사리, 해조류).
    - **한식 위주**로 구성하되, 필요 시 서양식도 가능.""",

    "근육량 증가": """근육 성장을 위한 **고단백 식단**을 제공해야 해.
    - 하루 **1,900kcal 기준**으로 구성.
    - **단백질 섭취량을 높이고, 탄수화물은 복합탄수화물 중심**으로 제공.
    - **운동 후 빠르게 흡수되는 탄수화물(고구마, 바나나, 현미밥 등)과 단백질을 함께 섭취**.
    - **단백질 비율 40% 이상** (닭가슴살, 소고기, 생선, 계란, 두부, 그릭요거트).
    - **건강한 지방(올리브오일, 견과류, 아보카도) 포함**.""",

    "나트륨 줄이기": """저염식을 고려한 건강한 식단을 추천해야 해.
    - **잡곡밥(현미, 보리) 위주**로 구성하지만, 기호에 따라 쌀밥도 허용.
    - **고기, 생선, 두부 등의 단백질 반찬을 골고루 포함**하되, **기름기와 껍질 제거한 살코기** 사용.
    - **제철 채소 활용** 및 **싱겁게 조리**, **염장식품(김치, 장아찌) 피하기**.
    - **간식은 제철 과일과 저지방 우유**를 활용.
    - **튀김 대신 굽기, 찜, 삶는 조리법 사용** (적당량의 식물성 기름 허용).
    - **하루 염분량은 소금 기준 3g 이하**로 제한.""",
}

@app.get("/recommend")
async def recommend_diet(goal: str):
    """
    사용자의 목표에 맞는 3가지 식단을 추천하는 API (한식 위주, 목표별 세부 조건 반영)
    """
    try:
        guideline = goal_guidelines.get(goal, "건강한 식단을 추천해줘.")

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": """너는는 한국식 건강 식단 전문가야.
                모든 식단은 한식을 기반으로 구성해야 해.
                서양식이 포함될 경우, 한국인의 식생활과 잘 어울리는 음식만 예외적으로 허용할게.
                각 끼니마다 다른 음식으로 구성해줘. 
                한식 예시: 잡곡밥, 나물 반찬, 된장찌개, 불고기, 생선구이, 두부조림 등.
                서양식 예시 (예외적 허용): 그릭요거트, 오트밀, 견과류, 닭가슴살 샐러드 등."""},

                {"role": "user", "content": f"나는 {goal}을 목표로 하고 있어. {guideline} 하루 식단을 추천해줘."},

                {"role": "user", "content": """
각 식단은 다음과 같은 **고정된 형식**을 따라야 해:
### 식단 1:
**아침**:
- 음식1 - [중량 (g), 칼로리 (kcal)]
- 음식2 - [중량 (g), 칼로리 (kcal)]
- 음식3 - [중량 (g), 칼로리 (kcal)]
- 음식4 - [중량 (g), 칼로리 (kcal)]

**아침 영양 정보**:
- 총 칼로리: XX kcal
- 탄수화물: XX g
- 단백질: XX g
- 지방: XX g

**아침 영양 팁**:
- 아침 식사에서 중요한 영양 요소에 대한 설명.

**점심**:
- 음식1 - [중량 (g), 칼로리 (kcal)]
- 음식2 - [중량 (g), 칼로리 (kcal)]
- 음식3 - [중량 (g), 칼로리 (kcal)]
- 음식4 - [중량 (g), 칼로리 (kcal)]

**점심 영양 정보**:
- 총 칼로리: XX kcal
- 탄수화물: XX g
- 단백질: XX g
- 지방: XX g

**점심 영양 팁**:
- 점심 식사에서 중요한 영양 요소에 대한 설명.

**저녁**:
- 음식1 - [중량 (g), 칼로리 (kcal)]
- 음식2 - [중량 (g), 칼로리 (kcal)]
- 음식3 - [중량 (g), 칼로리 (kcal)]
- 음식4 - [중량 (g), 칼로리 (kcal)]

**저녁 영양 정보**:
- 총 칼로리: XX kcal
- 탄수화물: XX g
- 단백질: XX g
- 지방: XX g

**저녁 영양 팁**:
- 저녁 식사에서 중요한 영양 요소에 대한 설명.

### 식단 2:
(동일한 형식)

### 식단 3:
(동일한 형식)
"""
                }
            ]
        )

        # GPT 응답 처리
        full_text = response.choices[0].message.content
        split_texts = re.split(r'(?=### 식단 2:|### 식단 3:)', full_text)

        if len(split_texts) < 3:
            meal_recommendations = [full_text, "", ""]
        else:
            meal_recommendations = [s.strip() for s in split_texts[:3]]

        return JSONResponse(
            content={
                "goal": goal,
                "meal_options": meal_recommendations
            },
            status_code=200
        )

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)