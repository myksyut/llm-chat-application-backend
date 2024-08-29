import os
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_groq import ChatGroq

# Grok llama model
LLM_MODEL = "llama-3.1-70b-versatile"

# Retriever settings
TOP_K = 5

load_dotenv()

# プロンプトテンプレート
system_prompt = (
    '''
    あなたは、情報の検索を支援する AI アシスタントです。
    出力はマークダウン形式
    '''
)
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{question}"),
    ]
)

# RAGチャットボットを実行
async def chat_with_bot_async(question: str):
    # LLM
    chat_model = ChatGroq(model_name=LLM_MODEL)

    # RAG Chain
    rag_chain = (
        prompt
        | chat_model
        | StrOutputParser()
    )

    # プロンプトテンプレートに基づいて応答を生成（ストリーミング）
    async for chunk in rag_chain.astream(question):
        yield chunk