import os
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai

# API 키 설정
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))  # 👉 본인의 API 키로 교체

# 모델 인스턴스 생성
model = genai.GenerativeModel("gemini-2.5-flash")

# Pydantic 모델 정의
class Request(BaseModel):
    query: str

class SearchResponse(BaseModel):
    response: str
    #session_id: str
    #conversation_history: List[Dict[str, str]]

# FastAPI 앱 초기화
app = FastAPI(
    title="신한카드 추천 API",
    description="신한카드 추천 및 이벤트 정보를 제공하는 API 서비스",
    version="1.0.0"
)

@app.post("/api/event-agent/search", response_model=SearchResponse)
async def search(request: Request):
    query = request.query
    summary = model.generate_content(query)
    return SearchResponse(response=summary.text)

@app.get("/health")
def health():
    return "ok", 200

# 로컬 실행용 (Cloud Run에서는 Procfile이 gunicorn을 실행함)
# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))