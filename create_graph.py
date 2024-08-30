from langchain_community.graphs import Neo4jGraph

graph = Neo4jGraph()

create_query = '''
CREATE (p:Person {name: "宮木翔太"})

// 学歴ノードの作成
CREATE (ku:University {name: "九州工業大学"})
CREATE (ou:University {name: "放送大学"})

// 学歴関係の作成
CREATE (p)-[:ENROLLED {date: "2019-04-01"}]->(ku)
CREATE (p)-[:TOOK_LEAVE {date: "2020-03-01"}]->(ku)
CREATE (p)-[:RETURNED {date: "2021-04-01"}]->(ku)
CREATE (p)-[:TRANSFERRED {date: "2022-04-01"}]->(ou)
CREATE (p)-[:EXPECTED_GRADUATION {date: "2024-09-01"}]->(ou)

// 会社ノードの作成
CREATE (dl:Company {name: "株式会社dentalight"})
CREATE (az:Company {name: "Azpower株式会社"})

// 職歴関係の作成
CREATE (p)-[:WORKED_AT {start: "2019-10-01", end: "2023-01-31", position: "アルバイト"}]->(dl)
CREATE (p)-[:WORKS_AT {start: "2023-06-01", position: "アルバイト"}]->(az)

// プロジェクトノードの作成
CREATE (scraping:Project {name: "スクレイピングツールの開発", duration: "2019-10-01 to 2022-07-31"})
CREATE (webApp:Project {name: "歯科医院向けWebアプリケーション開発", duration: "2022-02-01 to 2022-07-31"})
CREATE (slackBot:Project {name: "患者向けSlack botアプリケーションの設計・開発", duration: "2022-07-01 to 2022-08-31"})
CREATE (mobileApp:Project {name: "患者向けスマホアプリの開発・リファクタリング", duration: "2022-08-01 to 2023-01-31"})
CREATE (aiChat:Project {name: "エンタープライズ向け生成AIチャットサービスの開発", duration: "2023-06-01 to present"})

// プロジェクトと会社の関係作成
CREATE (dl)-[:HAS_PROJECT]->(scraping)
CREATE (dl)-[:HAS_PROJECT]->(webApp)
CREATE (dl)-[:HAS_PROJECT]->(slackBot)
CREATE (dl)-[:HAS_PROJECT]->(mobileApp)
CREATE (az)-[:HAS_PROJECT]->(aiChat)

// スキルノードの作成
CREATE (python:Skill {name: "Python"})
CREATE (typescript:Skill {name: "TypeScript"})
CREATE (php:Skill {name: "PHP"})
CREATE (react:Skill {name: "React"})
CREATE (flutter:Skill {name: "Flutter"})
CREATE (sqlServer:Skill {name: "SQL Server"})
CREATE (azure:Skill {name: "Azure"})
CREATE (aws:Skill {name: "AWS"})
CREATE (graphql:Skill {name: "GraphQL"})
CREATE (hasura:Skill {name: "Hasura"})
CREATE (rag:Skill {name: "RAG"})

// スキルとプロジェクトの関係作成
CREATE (scraping)-[:USES_SKILL]->(python)
CREATE (scraping)-[:USES_SKILL]->(sqlServer)
CREATE (webApp)-[:USES_SKILL]->(typescript)
CREATE (webApp)-[:USES_SKILL]->(react)
CREATE (webApp)-[:USES_SKILL]->(sqlServer)
CREATE (webApp)-[:USES_SKILL]->(hasura)
CREATE (webApp)-[:USES_SKILL]->(graphql)
CREATE (webApp)-[:USES_SKILL]->(aws)
CREATE (slackBot)-[:USES_SKILL]->(python)
CREATE (mobileApp)-[:USES_SKILL]->(flutter)
CREATE (aiChat)-[:USES_SKILL]->(azure)
CREATE (aiChat)-[:USES_SKILL]->(python)
CREATE (aiChat)-[:USES_SKILL]->(rag)

// 人物とスキルの関係作成
CREATE (p)-[:HAS_SKILL]->(python)
CREATE (p)-[:HAS_SKILL]->(typescript)
CREATE (p)-[:HAS_SKILL]->(php)
CREATE (p)-[:HAS_SKILL]->(react)
CREATE (p)-[:HAS_SKILL]->(flutter)
CREATE (p)-[:HAS_SKILL]->(sqlServer)
CREATE (p)-[:HAS_SKILL]->(azure)
CREATE (p)-[:HAS_SKILL]->(aws)
CREATE (p)-[:HAS_SKILL]->(graphql)
CREATE (p)-[:HAS_SKILL]->(hasura)
CREATE (p)-[:HAS_SKILL]->(rag)

// 強みノードの作成
CREATE (strength1:Strength {description: "幅広い技術スタックの経験（バックエンド、フロントエンド、モバイルアプリ開発）"})
CREATE (strength2:Strength {description: "クラウドサービスを活用した開発経験"})
CREATE (strength3:Strength {description: "顧客ニーズに基づいたアプリケーション設計・開発能力"})
CREATE (strength4:Strength {description: "新技術の習得と実践的な適用能力（生成AI、クラウドサービス等）"})

// 人物と強みの関係作成
CREATE (p)-[:HAS_STRENGTH]->(strength1)
CREATE (p)-[:HAS_STRENGTH]->(strength2)
CREATE (p)-[:HAS_STRENGTH]->(strength3)
CREATE (p)-[:HAS_STRENGTH]->(strength4)
'''

graph.query(create_query)