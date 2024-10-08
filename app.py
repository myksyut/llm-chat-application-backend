import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json

from chat import chat_with_bot_async

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://llm-chat-application.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    question: str
    history: list

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    async def event_generator():
        async for chunk in chat_with_bot_async(request.question, request.history):
            # チャンクがすでにJSON形式の場合はそのまま送信
            if chunk.startswith("data: {"):
                yield chunk
            else:
                # テキストチャンクの場合は従来通りエスケープして送信
                escaped_chunk = json.dumps({"text": chunk})
                yield f"data: {escaped_chunk}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)