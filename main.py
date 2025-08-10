import os, time, re, json, asyncio
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
#import google.generativeai as genai
from google import genai
from utils import parse_lenient_json

#json_pat = re.compile(r'(\{.*?\}|\[.*?\])', re.DOTALL)

event_list = json.loads(open('resources/event_list.json', 'r', encoding='utf-8').read())
event_dict = {event['event_id']: event for event in event_list}
event_detail = json.loads(open('resources/event_detail.json', 'r', encoding='utf-8').read())

SEARCHABLE_KEYS = ['event_id', 'detail']
POOL_SIZE = 4
event_pool = []
for k in range(POOL_SIZE):
    index_of_k = [idx for idx in range(len(event_list)) if idx % POOL_SIZE == k]
    #print(k, index_of_k)
    event_pool.append([{key: event_list[idx][key] for key in SEARCHABLE_KEYS} for idx in index_of_k])

# API 키 설정
#genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))  # 👉 본인의 API 키로 교체
# 모델 인스턴스 생성
#model = genai.GenerativeModel("gemini-2.5-flash")

PROJECT_ID = "eco-diode-468322-s5"  # @param {type: "string", placeholder: "[your-project-id]", isTemplate: true}
#if not PROJECT_ID or PROJECT_ID == "[your-project-id]":
#PROJECT_ID = str(os.environ.get("GOOGLE_CLOUD_PROJECT"))
print(PROJECT_ID)

LOCATION = "global"

client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

if not client.vertexai:
    print("Using Gemini Developer API.")
elif client._api_client.project:
    print(
        f"Using Vertex AI with project: {client._api_client.project} in location: {client._api_client.location}"
    )
elif client._api_client.api_key:
    print(
        f"Using Vertex AI in express mode with API key: {client._api_client.api_key[:5]}...{client._api_client.api_key[-5:]}"
    )

# Pydantic 모델 정의
class SearchRequest(BaseModel):
    query: str

class SearchResponse(BaseModel):
    title: str
    url: str
    name: str
    detail: str
    precaution: str
    event_type: str
    start_at: str
    end_at: str
    event_id: str

class QuestionRequest(BaseModel):
    question: str

class QuestionResponse(BaseModel):
    event_id: str
    answer: str

# FastAPI 앱 초기화
app = FastAPI(
    title="신한카드 추천 API",
    description="신한카드 추천 및 이벤트 정보를 제공하는 API 서비스",
    version="1.0.0"
)

async def call_model(query, k):
    #time.sleep(k * 0.2)
    prompt = query + """ - 목록에서 해당하는 event_id만 list로 만들어줘. 다른 말은 하지마 : """ + str(event_pool[k])
    
    MODEL_ID = "gemini-2.5-flash-lite"

    resp = await client.aio.models.generate_content(
    model=MODEL_ID,
    contents=prompt)
    #resp = await model.generate_content_async(prompt)
    resp = parse_lenient_json(resp.text)
    return resp if len(resp) > 0 else []

@app.post("/api/event-agent/search", response_model=List[SearchResponse])
async def search(request: SearchRequest):

    query = request.query
    results = await asyncio.gather(*(call_model(query, k) for k in range(POOL_SIZE)))
    results = [item for sublist in results for item in sublist]  # flatten event_ids
    results = [event_dict[event_id] for event_id in results]
    return [SearchResponse(**item) for item in results]

@app.post("/api/event-agent/events/{event_id}/details", response_model=QuestionResponse)
async def question(event_id: str, request: QuestionRequest):
    event_doc = event_detail.get(event_id, '')
    if event_doc == '':
        raise HTTPException(status_code=404, detail="Event not found")
    
    query = request.question
    prompt = query + """ : (다음 내용만 참고해서 1문장으로만 답변해. 다른 말은 하지마) """ + event_doc
    
    MODEL_ID = "gemini-2.5-flash"

    resp = await client.aio.models.generate_content(
    model=MODEL_ID, contents=prompt)
    return QuestionResponse(event_id=event_id, answer=resp.text)

@app.get("/health")
def health():
    return "ok", 200

# 로컬 실행용 (Cloud Run에서는 Procfile이 gunicorn을 실행함)
# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))