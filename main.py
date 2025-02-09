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
    "다이어트": "칼로리 조절과 균형 잡힌 영양을 고려한 식단을 추천해줘.",
    "당 줄이기": "혈당을 안정적으로 유지할 수 있는 저당 식단을 추천해줘.",
    "근육량 증가": "근육 성장을 위한 고단백 식단을 추천해줘.",
    "나트륨 줄이기": "저염식을 고려한 건강한 식단을 추천해줘."
}

@app.get("/recommend")
async def recommend_diet(goal: str):
    """
    사용자의 목표에 맞는 3가지 식단을 추천하는 API (아침, 점심, 저녁의 영양정보와 영양팁을 각각 제공)
    """
    try:
        guideline = goal_guidelines.get(goal, "건강한 식단을 추천해줘.")

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "당신은 건강한 식단 전문가입니다."},
                {
                    "role": "user",
                    "content": f"나는 {goal}을 목표로 하고 있어. {guideline} 3가지 식단을 추천해줘."
                },
                {
                    "role": "user",
                    "content": """
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

        # GPT 전체 응답(문자열)
        full_text = response.choices[0].message.content

        # "### 식단 2:"나 "### 식단 3:"이 등장하기 직전을 경계로 split
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
