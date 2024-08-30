import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 既存のコードをインポート
from chat import chat_with_bot_async

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000",
                   "https://llm-chat-application.vercel.app/"],  # フロントエンドのURLに置き換えてください
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    question: str  # 'query' から 'question' に変更

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    async def event_generator():
        async for chunk in chat_with_bot_async(request.question):
            yield f"data: {chunk}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)