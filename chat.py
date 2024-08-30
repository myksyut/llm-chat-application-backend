import os
import re
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_groq import ChatGroq
from langchain_community.graphs import Neo4jGraph
# Grok llama model
LLM_MODEL = "llama-3.1-70b-versatile"

load_dotenv()

def clean_query(query):
    # Remove Markdown code block syntax
    query = re.sub(r'```[\s\S]*?```', lambda m: m.group(0).strip('`'), query)
    # Remove any remaining backticks
    query = query.replace('`', '')
    # Strip leading/trailing whitespace
    return query.strip()
# RAGチャットボットを実行
async def chat_with_bot_async(question: str, history: list):
    # LLM
    llm = ChatGroq(model_name=LLM_MODEL)
    graph = Neo4jGraph(
        url=os.environ["NEO4J_URI"],
        username=os.environ["NEO4J_USERNAME"],
        password=os.environ["NEO4J_PASSWORD"]
    )
    # プロンプトテンプレート
    cypher_template = """Neo4jの以下のグラプスキーマに基づいてユーザーの質問に答えるCypherクエリを書いて下さい
    回答にクエリ以外を含めないでください
    スキーマ:{schema}
    質問:{question}
    Cyperクエリ:
    """

    cypher_prompt = ChatPromptTemplate.from_messages(
        [
            ("system","入力された質問をCypherクエリに変換して下さい.クエリ以外は生成しないでください"),
            ("human",cypher_template)
        ]
    )
    queryGenChain = (
        RunnablePassthrough.assign(schema=lambda _:graph.get_schema)
        | cypher_prompt
        | llm
        | StrOutputParser()
    )

    response_template = """会話履歴、質問、Cypherクエリ、およびクエリ実行結果に基づいて、自然言語で回答を書いてください。:
    会話履歴: {history}
    質問: {question}
    Cypherクエリ: {query}
    クエリ実行結果: {response}"""

    response_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "入力された会話履歴, 質問、クエリ、クエリ実行結果をもとに、自然言語の答えに変換してください。",
        ),
        ("human", response_template),
    ]
    )

    chain = (
        RunnablePassthrough.assign(query=queryGenChain)
        | RunnablePassthrough.assign(response=lambda x: graph.query(clean_query(x["query"])))
        | response_prompt
        | llm
        | StrOutputParser()
    )

    # プロンプトテンプレートに基づいて応答を生成（ストリーミング）
    async for chunk in chain.astream({"question": question, "history":history}):
        yield chunk