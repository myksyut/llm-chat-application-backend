import os
import re
import logging
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

async def chat_with_bot_async(question: str, history: list):
    logger.info(f"Starting chat with question: {question}")
    logger.debug(f"Chat history: {history}")

    llm = ChatGroq(model_name=LLM_MODEL)
    logger.info(f"Initialized ChatGroq with model: {LLM_MODEL}")

    graph = Neo4jGraph(
        url=os.environ["NEO4J_URI"],
        username=os.environ["NEO4J_USERNAME"],
        password=os.environ["NEO4J_PASSWORD"]
    )
    logger.info("Connected to Neo4j graph")

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

    logger.debug("Created query generation chain")

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
        RunnablePassthrough.assign(query=queryGenChain)
        | RunnablePassthrough.assign(response=lambda x: graph.query(clean_query(x["query"])))
        | response_prompt
        | llm
        | StrOutputParser()
    )

    logger.info("Starting to stream response")
    async for chunk in chain.astream({"question": question, "history": history}):
        logger.debug(f"Yielding chunk: {chunk}")
        yield chunk

    logger.info("Finished streaming response")