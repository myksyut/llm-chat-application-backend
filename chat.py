import os
import re
import logging
import json
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_groq import ChatGroq
from langchain_community.graphs import Neo4jGraph

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Grok llama model
LLM_MODEL = "llama-3.1-70b-versatile"

load_dotenv()

def clean_query(query):
    logger.debug(f"Cleaning query: {query}")
    query = re.sub(r'`[\s\S]*?`', lambda m: m.group(0).strip('`'), query)
    query = query.replace('`', '')
    cleaned_query = query.strip()
    logger.debug(f"Cleaned query: {cleaned_query}")
    return cleaned_query

async def send_process_step(step):
    return f"data: {json.dumps({'process_step': step})}\n\n"

async def initialize_llm_and_graph():
    llm = ChatGroq(model_name=LLM_MODEL)
    logger.info(f"Initialized ChatGroq with model: {LLM_MODEL}")

    graph = Neo4jGraph(
        url=os.environ["NEO4J_URI"],
        username=os.environ["NEO4J_USERNAME"],
        password=os.environ["NEO4J_PASSWORD"]
    )
    logger.info("Connected to Neo4j graph")
    return llm, graph

async def generate_query(llm, graph, question):
    cypher_template = """Neo4jの以下のグラプスキーマに基づいてユーザーの質問に答えるCypherクエリを書いて下さい
    回答にクエリ以外を含めないでください．
    スキーマ:{schema}
    質問:{question}
    Cyperクエリ:
    """

    cypher_prompt = ChatPromptTemplate.from_messages([
        ("system", "入力された質問をCypherクエリに変換して下さい.クエリ以外は生成しないでください"),
        ("system", "クエリが作成できない場合は次のクエリを返して下さい MATCH (n) WHERE 1=0 RETURN n"),
        ("human", cypher_template)
    ])
    logger.debug("Created cypher prompt template")

    queryGenChain = (
        RunnablePassthrough.assign(schema=lambda *_: graph.get_schema)
        | cypher_prompt
        | llm
        | StrOutputParser()
    )
    query = queryGenChain.invoke({"question": question})
    logger.debug("Created query generation chain")
    return query

async def execute_query(graph, query):
    return graph.query(clean_query(query))

async def generate_response(llm, question, history, query, response):
    response_template = """会話履歴、質問、Cypherクエリ、およびクエリ実行結果に基づいて、自然言語で回答を書いてください。:
    会話履歴: {history}
    質問: {question}
    Cypherクエリ: {query}
    クエリ実行結果: {response}"""

    response_prompt = ChatPromptTemplate.from_messages([
        ("system", "入力された会話履歴, 質問、クエリ、クエリ実行結果をもとに、自然言語の答えに変換してください。"),
        ("human", response_template),
    ])

    logger.debug("Created response prompt template")

    chain = (
        response_prompt
        | llm
        | StrOutputParser()
    )

    logger.info("Starting to stream response")
    async for chunk in chain.astream({"question": question, "history": history, "query": query, "response": response}):
        logger.debug(f"Yielding chunk: {chunk}")
        yield f"data: {json.dumps({'text': chunk})}\n\n"

async def chat_with_bot_async(question: str, history: list):
    logger.info(f"Starting chat with question: {question}")
    logger.debug(f"Chat history: {history}")

    process_steps = [
        "リクエスト受信",
        "クエリ生成",
        "データベース検索",
        "レスポンス生成"
    ]

    yield await send_process_step(process_steps[0])

    llm, graph = await initialize_llm_and_graph()

    query = await generate_query(llm, graph, question)
    yield await send_process_step(process_steps[1])

    response = await execute_query(graph, query)
    yield await send_process_step(process_steps[2])

    async for chunk in generate_response(llm, question, history, query, response):
        yield chunk
    yield await send_process_step(process_steps[3])

    logger.info("Finished streaming response")