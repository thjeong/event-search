import os, re, json, asyncio
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai

json_pat = re.compile(r'(\{.*?\}|\[.*?\])', re.DOTALL)

event_list = json.loads(open('resources/event_list.json', 'r').read())

POOL_SIZE = 5
event_pool = []
for k in range(POOL_SIZE):
    index_of_k = [idx for idx in range(len(event_list)) if idx % POOL_SIZE == k]
    #print(k, index_of_k)
    event_pool.append([event_list[idx] for idx in index_of_k])

# API 키 설정
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))  # 👉 본인의 API 키로 교체

# 모델 인스턴스 생성
#model = genai.GenerativeModel("gemini-2.5-flash")

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

async def call_model(query, k):
    prompt = query + """ - 목록에서 해당하는 event만 뽑아줘. 다른 말은 하지마 : """ + str(event_pool[k])
    model = genai.GenerativeModel("gemini-2.5-flash")
    resp = await model.generate_content_async(prompt)
    return json_pat.findall(resp.text)[0]

@app.post("/api/event-agent/search", response_model=List[SearchResponse])
async def search(request: Request):

    query = request.query
    results = await asyncio.gather(*(call_model(query, k) for k in range(POOL_SIZE)))
    results = [item for sublist in results for item in sublist]  # flatten
    return [SearchResponse(**item) for item in results]

@app.get("/health")
def health():
    return "ok", 200

# 로컬 실행용 (Cloud Run에서는 Procfile이 gunicorn을 실행함)
# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))