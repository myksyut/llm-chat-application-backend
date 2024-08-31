import asyncio
import logging
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
from chat import chat_with_bot_async

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    logger.info(f"Received chat request with question: {request.question}")
    logger.debug(f"Chat history: {request.history}")

    async def event_generator():
        try:
            async for chunk in chat_with_bot_async(request.question, request.history):
                escaped_chunk = json.dumps({"text": chunk})
                logger.debug(f"Sending chunk: {escaped_chunk}")
                yield f"data: {escaped_chunk}\n\n"
        except Exception as e:
            logger.error(f"Error in event generator: {str(e)}", exc_info=True)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    logger.info("Returning StreamingResponse")
    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting the FastAPI application")
    uvicorn.run(app, host="0.0.0.0", port=8000)