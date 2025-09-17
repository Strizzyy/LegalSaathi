from flask import Flask, render_template, request, jsonify
from neo4j import GraphDatabase
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from pyvis.network import Network
import random
import ssl
import json
from datetime import datetime
from langchain_community.llms.vllm import VLLMOpenAI
from langchain_community.vectorstores import Neo4jVector
from langchain.schema import HumanMessage
from sentence_transformers import SentenceTransformer
from langchain.embeddings.base import Embeddings
from typing import List, Tuple
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.output_parsers import StrOutputParser
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from flask_cors import CORS
import textwrap
import os
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
import numpy as np
import re
from openai import OpenAI
import logging
from flashrank import Ranker, RerankRequest
from tqdm import tqdm
from pydantic import BaseModel, Field
tqdm().disable = True
import gc
import time
import pandas as pd
from threading import Lock
from click import prompt
from neo4j.exceptions import CypherSyntaxError, DatabaseError, ServiceUnavailable
import json

# # Configure logging
# log_file = 'app.log'
# if not os.path.exists(log_file):
#     open(log_file, 'a').close()
# logging.basicConfig(
#     filename=log_file,
#     level=logging.DEBUG,
#     format='%(asctime)s - %(levelname)s - %(message)s'
# )


logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

uri ="neo4j+s://5e878423.databases.neo4j.io"
user = "neo4j"
password ="zzajdK09jqhhwwkM13IWqbIGvQgIZL5pqee3Il_FLvU"

# Custom Embeddings Class
class SentenceTransformerEmbeddings(Embeddings):
    def __init__(self, model_name='sentence-transformers/all-mpnet-base-v2'):
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(texts)
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        embedding = self.model.encode([text])[0]
        return embedding.tolist()

embeddings = SentenceTransformerEmbeddings()

graph = Neo4jGraph(
    url=uri,
    username=user,
    password=password
)

vector_index_chunk = Neo4jVector.from_existing_graph(
    embeddings,
    search_type="hybrid",
    node_label="CHUNK",
    text_node_properties=["content"],
    embedding_node_property="embedding_new",
    url=uri,
    username=user,
    password=password
)

driver = GraphDatabase.driver(
    uri,
    auth=(user, password)
)

# vLLM initialization
llm = VLLMOpenAI(
    openai_api_key="EMPTY",
    openai_api_base="http://172.25.0.211:8002/v1",
    model_name="meta-llama/Llama-3.1-8B-Instruct",
    temperature=0.1,
    max_tokens=40,
    seed=123,
    presence_penalty=1.8
)

# Initialize FlashRank reranker
cache_dir = "E:/Secondary download/intern/vll/cache"
os.makedirs(cache_dir, exist_ok=True)
reranker = Ranker(model_name="ms-marco-MiniLM-L-12-v2", cache_dir=cache_dir)
logger.info("FlashRank reranker initialized with model: ms-marco-MiniLM-L-12-v2")

# JSON schemas for structured output
entities_schema = {
    "type": "object",
    "properties": {
        "names": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Extract all legal entities and related information that appear in the text"
        },
        "case": {
            "type": "string", 
            "description": "Extract the case name or ID mentioned in the text, if any"
        }
    },
    "required": ["names", "case"],
    "additionalProperties": False
}

relevance_schema = {
    "type": "object",
    "properties": {
        "is_relevant": {
            "type": "boolean",
            "description": "Whether the generated output is relevant to the user query (true for yes, false for no)"
        }
    },
    "required": ["is_relevant"],
    "additionalProperties": False
}

class Entities(BaseModel):
    """Identifying information about entities and cases."""
    names: List[str] = Field(description="Extract all legal entities and related information that appear in the text")
    case: str = Field(default="", description="Extract the case name or ID mentioned in the text, if any")

class RelevanceCheck(BaseModel):
    """Result of checking if the output is relevant to the user query."""
    is_relevant: bool = Field(default=" ", description="Whether the generated output is relevant to the user query (true for yes, false for no)")
    

# Function to extract structured data using vLLM with JSON schema
def extract_entities_structured(question: str) -> Entities:
    prompt = f"""
    You are an expert in extracting named entities and case information from legal text. Extract all legal entities (e.g., person names, organizations) and the case name or ID (e.g., CRRFC-18-2018, CRA-247-2019, 56/2018, WP-16200-2024, or similar formats like [A-Z]+-###-YYYY or ###/YYYY) mentioned ONLY in the input text.

    Return the extracted information in JSON format:
    {{
        "names": ["Legal Entity 1", "Legal Entity 2", ...],
        "case": "Case Name or ID"
    }}
    If no case ID is mentioned, return an empty string for the case field.

    Input: {question}
    """
    try:
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": question}
        ]
        completion = client.chat.completions.create(
            model="meta-llama/Llama-3.1-8B-Instruct",
            messages=messages,
            temperature=0,
            max_tokens=500,
            extra_body={"guided_json": entities_schema}
        )
        response = completion.choices[0].message.content.strip()
        logger.debug(f"Raw entity extraction response: {response}")
        
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(0))
            case = data.get("case", "")
            # Fallback: Extract case ID using regex if LLM fails
            if not case:
                case_match = re.search(r'([A-Z]+-?\d+[-/]\d{4}|[A-Z]+-\d{4,}-\d{4}|\d+/\d{4})', question, re.IGNORECASE)
                case = case_match.group(0) if case_match else ""
            return Entities(names=data.get("names", []), case=case)
        else:
            logger.debug("No valid JSON found in entity extraction response")
            return Entities(names=[], case="")
    except Exception as e:
        logger.error(f"Error in structured entity extraction: {e}")
        return Entities(names=[], case="")

# Alternative relevance check using OpenAI client (more consistent with your other functions)
def check_relevance_structured(user_input: str, cypher_query: str, output: str) -> RelevanceCheck:
    # Preprocess output to remove contradictory prefix
    cleaned_output = re.sub(r"I cannot answer this based on the provided context\.\s*--\s*I can answer it\s*", "", output).strip()
    
    # Simplified system prompt
    system_prompt = f"""You are an expert evaluator. Determine if the output answers the user's question.

User Question: {user_input}
Output: {cleaned_output}

Rules:
- If the output provides a relevant answer to the question: return true
- If the output says "I cannot answer" or is irrelevant: return false
- Ignore technical details like Cypher queries

Return only JSON format: {{"is_relevant": true}} or {{"is_relevant": false}}"""
    
    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        completion = client.chat.completions.create(
            model="meta-llama/Llama-3.1-8B-Instruct",
            messages=messages,
            temperature=0,
            max_tokens=50,
            top_p=0.9,
            frequency_penalty=0.1,
            extra_body={
                "guided_json": relevance_schema,
                "chat_template_kwargs": {"enable_thinking": True},
            }
        )
        
        response = completion.choices[0].message.content.strip()
        print(f"Raw relevance check response: {response}")
        
        # Parse JSON response
        try:
            data = json.loads(response)
            return RelevanceCheck(is_relevant=data.get("is_relevant", False))
        except json.JSONDecodeError:
            # Fallback parsing
            if "true" in response.lower():
                return RelevanceCheck(is_relevant=True)
            elif "false" in response.lower():
                return RelevanceCheck(is_relevant=False)
            else:
                print("Could not determine relevance, defaulting to False")
                return RelevanceCheck(is_relevant=False)
                
    except Exception as e:
        print(f"Error in relevance check: {e}")
        return RelevanceCheck(is_relevant=False)

# Utility Functions
def remove_lucene_chars(text: str) -> str:
    chars = ['+', '-', '&', '|', '!', '(', ')', '{', '}', '[', ']', '^', '"', '~', '*', '?', ':', '\\', '/']
    for char in chars:
        text = text.replace(char, ' ')
    return text

def generate_full_text_query(input: str) -> str:
    words = [el for el in remove_lucene_chars(input).split() if el]
    if not words:
        return ""
    full_text_query = ""
    for word in words[:-1]:
        full_text_query += f" {word}~2 AND"
    full_text_query += f" {words[-1]}~2"
    return full_text_query.strip()

# Structured Retriever
def structured_retriever(question: str) -> str:
    try:
        entities = extract_entities_structured(question)
        print(f"Entities: {entities}")

        if not entities or (not entities.names and not entities.case):
            return "No entities or case found"

        result = ""
        # Process entities and case separately
        items_to_query = entities.names + ([entities.case] if entities.case else [])
        
        for item in items_to_query:
            query = generate_full_text_query(item)
            if not query.strip():
                print(f"Empty query generated for item '{item}', skipping execution.")
                continue

            try:
                # Query for entities
                response = graph.query(
                    """
                    CALL db.index.fulltext.queryNodes('entity', $query, {limit: 2})
                    YIELD node, score
                    CALL () {
                        WITH node
                        MATCH (node)-[r:!HAS_DESCRIPTION & !HAS_EVENT & !HAS_ORDER & !HAS_ANALYSIS & !HAS_GROUND & !HAS_FACT & !HAS_CHUNK]->(neighbor)
                        RETURN node as nod ,type(r) as relation,neighbor as neigh
                        UNION ALL
                        WITH node
                        MATCH (node)<-[r:!HAS_DESCRIPTION & !HAS_EVENT & !HAS_ORDER & !HAS_ANALYSIS & !HAS_GROUND & !HAS_FACT & !HAS_CHUNK]-(neighbor)
                        RETURN node as nod ,type(r) as relation,neighbor as neigh
                    }
                    RETURN nod, relation, neigh LIMIT 30;
                    """,
                    {"query": query}
                )
                # Query for case_key
                response2 = graph.query(
                    """
                    CALL db.index.fulltext.queryNodes('case_key', $query, {limit: 2})
                    YIELD node, score
                    CALL () {
                        WITH node
                        MATCH (node)-[r:!HAS_DESCRIPTION & !HAS_EVENT & !HAS_ORDER & !HAS_ANALYSIS & !HAS_GROUND & !HAS_FACT & !HAS_CHUNK]->(neighbor)
                        RETURN node as nod ,type(r) as relation,neighbor as neigh
                        UNION ALL
                        WITH node
                        MATCH (node)<-[r:!HAS_DESCRIPTION & !HAS_EVENT & !HAS_ORDER & !HAS_ANALYSIS & !HAS_GROUND & !HAS_FACT & !HAS_CHUNK]-(neighbor)
                        RETURN node as nod ,type(r) as relation,neighbor as neigh
                    }
                    RETURN nod, relation, neigh LIMIT 50;
                    """,
                    {"query": query}
                )
                print(f"response1-> {response} and \n response2-> {response2}")

                if response2 or response:
                    result_part1 = ""
                    result_part2 = ""
                    for el in response2:
                        nod = el.get('nod', {})
                        relation = el.get('relation', '')
                        neigh = el.get('neigh', {})
                        result_part1 += f"{nod} - {relation} - {neigh}\n"
                    for el in response:
                        nod = el.get('nod', {})
                        relation = el.get('relation', '')
                        neigh = el.get('neigh', {})
                        result_part2 += f"{nod} - {relation} - {neigh}\n"
                    result += result_part1 + result_part2
                    print(result)
                else:
                    print(f"No results for query: {query}")
            except Exception as query_error:
                print(f"Error executing query for item '{item}': {query_error}")

        return result if result.strip() else "No structured data found"

    except Exception as e:
        print(f"Error in structured retriever: {str(e)}")
        return "Error retrieving structured data"

def cosine_similarity(a, b):
    """Compute cosine similarity between two vectors."""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def apply_reranker(query: str, chunks: List[dict]) -> List[dict]:
    try:
        if not chunks:
            return chunks
        # Limit to top 10 chunks by similarity
        chunks = sorted(chunks, key=lambda x: x["similarity_score"], reverse=True)[:10]
        passages = [
            {"text": chunk["content"], "meta": {"index": idx}} for idx, chunk in enumerate(chunks)
        ]
        rerank_request = RerankRequest(query=query, passages=passages)
        reranked_results = reranker.rerank(rerank_request)
        for result in reranked_results:
            original_index = result["meta"]["index"]
            chunks[original_index]["reranker_score"] = float(result["score"])
        # Sort chunks by reranker score in descending order

        sorted_chunks = sorted(chunks, key=lambda x: x["reranker_score"], reverse=True)

        logger.debug(f"Reranked chunks: {[chunk['reranker_score'] for chunk in sorted_chunks]}")

        return sorted_chunks
    except Exception as e:
        logger.error(f"FlashRank reranker failed: {str(e)}")
        logger.debug(f"Returning original chunks without reranking")
        return chunks   

#retriever function to handle both structured and unstructured data retrieval
def retriever(question: str):
    logger.debug(f"Search query: {question}")
    try:
        entities = extract_entities_structured(question)
        logger.debug(f"Entities and Case: {entities}")

        # Structured data retrieval
        structured_data = structured_retriever(question)
        logger.debug(f"Structured data: {structured_data}")

        unstructured_data = []
        chunk_details = []
        case_id = entities.case if entities.case else None
        if case_id:
            logger.debug(f"Retrieving chunks for case: {case_id}")
            # Query to get chunks for the specific case
            case_chunks_query = """
            MATCH (c:CASE)
            WHERE toLower(c.Case_Number) = toLower($case_id) OR c.Case_Number =~ '(?i).*' + $case_id + '.*'
            MATCH (c)-[:HAS_CHUNK]->(ch:CHUNK)
            RETURN ch.content AS content, ch.embedding_new AS embedding
            LIMIT 100
            """
            with driver.session() as session:
             case_chunks = session.run(case_chunks_query, {"case_id": case_id}).data()
            
            if case_chunks:
                query_embedding = embeddings.embed_query(question)
                for chunk in case_chunks:
                    chunk_embedding = chunk["embedding"]
                    score = cosine_similarity(query_embedding, chunk_embedding)
                    chunk_details.append({
                        "content": chunk["content"],
                        "case_id": case_id,
                        "similarity_score": float(score),
                        "reranker_score": 0.0
                    })
            else:
                logger.debug(f"No chunks found for case: {case_id}")

        # Handle entity queries with multiple cases
        if entities.names and not chunk_details:
            logger.debug(f"Processing entities: {entities.names}")
            for entity in entities.names:
                entity_cases_query = """
                CALL db.index.fulltext.queryNodes('entity', $entity_name, {limit: 10})
                YIELD node, score
                WITH node
                MATCH (node)-[]-(c:CASE)
                RETURN c.Case_Number AS case_number
                """
                entity_cases = graph.query(entity_cases_query, {"entity_name": entity})
                case_numbers = [record["case_number"] for record in entity_cases]
                
                if case_numbers:
                    logger.debug(f"Found cases for {entity}: {case_numbers}")
                    for case_number in case_numbers:
                        case_chunks_query = """
                        MATCH (c:CASE {Case_Number: $case_number})
                        MATCH (c)-[:HAS_CHUNK]->(ch:CHUNK)
                        RETURN ch.content AS content, ch.embedding_new AS embedding
                        LIMIT 100
                        """
                        case_chunks = graph.query(case_chunks_query, {"case_number": case_number})
                        if case_chunks:
                            query_embedding = embeddings.embed_query(question)
                            for chunk in case_chunks:
                                chunk_embedding = chunk["embedding"]
                                score = cosine_similarity(query_embedding, chunk_embedding)
                                chunk_details.append({
                                    "content": chunk["content"],
                                    "case_id": case_number,
                                    "similarity_score": float(score),
                                    "reranker_score": 0.0
                                })
                        else:
                            logger.debug(f"No chunks found for {entity} in case: {case_number}")
                else:
                    logger.debug(f"No cases found for entity: {entity}")

        # Fallback to general similarity search
        if not chunk_details:
            logger.debug("No case or entity chunks found, performing general similarity search")
            search_results = vector_index_chunk.similarity_search_with_score(question, k=10)
            chunk_details = [
                {"content": doc.page_content, "case_id": None, "similarity_score": float(score), "reranker_score": 0.0}
                for doc, score in search_results
            ]

        # Apply reranker
        logger.debug(f"Applying reranker to {len(chunk_details)} chunks")
        chunk_details = apply_reranker(question, chunk_details)
        
        # Select top 5 chunks
        for chunk in chunk_details[:5]:
            content = chunk["content"]
            formatted_content = f"Case {chunk['case_id']}: {content}" if chunk["case_id"] else content
            unstructured_data.append(formatted_content)
        
        final_data = f"Structured data:\n{structured_data}\n\nUnstructured data:\n{'#Chunk '.join(unstructured_data)}"
        logger.debug(f"Final data: {final_data}")
        logger.debug(f"Chunk details: {json.dumps(chunk_details[:5], indent=2)}")
        return final_data, chunk_details[:5]
        gc.collect()
    except Exception as e:
        logger.error(f"Error in retriever: {str(e)}")
        return f"Error retrieving data: {str(e)}", []

        # Fallback to general similarity search if no case or entity chunks
        if not unstructured_data:
            print("No case or entity chunks found, performing general similarity search")
            unstructured_data = [el.page_content for el in vector_index_chunk.similarity_search(question, k=5)]

        final_data = f"""Structured data:\n{structured_data}\n\nUnstructured data:\n{"#Chunk ".join(unstructured_data)}"""
        print(f"Final data: {final_data}")
        return final_data
    except Exception as e:
        print(f"Error in retriever: {str(e)}")
        return f"Error retrieving data: {str(e)}"

# Function to retrieve data and create the graph
def create_graph(query):
    # Create the Pyvis network object
    net = Network(height="750px", width="100%", bgcolor="#ffffff", font_color="black")
    physics_options = {
        "physics": {
            "enabled": True,
            "barnesHut": {
                "theta": 0.5,
                "gravitationalConstant": -10000,
                "centralGravity": 0.3,
                "springLength": 600,
                "springConstant": 0.1,
                "damping": 0.09,
                "avoidOverlap": 1
            },
        }
    }

    net.set_options(json.dumps(physics_options))
    # Custom color scheme based on node type
    color_map = {
        'CASE': '#ADD8E6',
        'CIVIL': '#FFB6C1',
        'CRIMINAL': '#DDA0DD',
        'PENDING': '#FFD700',
        'DISPOSED': '#98FB98',
        'ANALYSIS': '#1f77b4',
        'ARGUMENTS': '#ff7f0e',
        'COURT': '#d62728',
        'DATE': '#9467bd',
        'DECISION': '#8c564b',
        'DOCUMENT': '#e377c2',
        'FACT': '#FFE135',
        'GPE': '#2E8B57',
        'GROUND': '#17becf',
        'JUDGE': '#FF6B6B',
        'LAWYER': '#32CD32',
        'ORDER': '#9370DB',
        'PARTICULAR': '#FFA500',
        'PETITIONER': '#BDB76B',
        'PRAYER': '#CD853F',
        'PRE_RELIED': '#87CEEB',
        'PRECEDENT': '#FF69B4',
        'PROVISION': '#A0522D',
        'RESPONDENT': '#4682B4',
        'RLC': '#FF8C00',
        'STATUTE': '#20B2AA',
        'SUBJECT': '#DAA520',
        'WITNESS': '#6495ED'
    }

    # Helper function to get truncated label
    def get_truncated_label(n, n_type):
        if 'name' in n: return n['name'][:20] + "..." if len(n['name']) > 20 else n['name']
        if 'purpose' in n: return n['purpose'][:20] + "..." if len(n['purpose']) > 20 else n['purpose']
        if 'Case_Number' in n: return n['Case_Number'][:20] + "..." if len(n['Case_Number']) > 20 else n['Case_Number']
        if 'Case_Type' in n: return n['Case_Type'][:20] + "..." if len(n['Case_Type']) > 20 else n['Case_Type']
        if 'CNR_No' in n: return n['CNR_No'][:20] + "..." if len(n['CNR_No']) > 20 else n['CNR_No']
        if 'Name_of_the_State' in n: return n['Name_of_the_State'][:20] + "..." if len(n['Name_of_the_State']) > 20 else n['Name_of_the_State']

        return n_type

    # Helper function to format properties for display in title
    def format_properties(n):
        return "\n".join([f"{key}: {value}" for key, value in n.items()])

    # Retrieve nodes and edges from Neo4j
    with driver.session() as session:
        result = session.run(query)
        for record in result:
            print(record)
            for node_label in ['n', 'm']:
                node = record[node_label]
                print(node_label)
                print(node)
                n_id = node.id
                n_type = list(node.labels)[0]
                n_properties = node.items()
                
                n_label_display = get_truncated_label(dict(n_properties), n_type)
                n_color = color_map.get(n_type, '#D3D3D3')
                net.add_node(n_id, 
                             label=n_label_display, 
                             title=f"Type: {n_type}\nProperties:\n{format_properties(dict(n_properties))}", 
                             color=n_color)
            rel = record['r']
            net.add_edge(record['n'].id, record['m'].id, title=f"{rel.type}", color="#888888")
    
    timestamp = datetime.now().strftime("%H%M%S")
    output_path = f'saved_graphs/knowledge_graph_{timestamp}.html'
    net.save_graph(output_path)
    return net

@app.route('/')
def index():
    queries = {
        'case_numbers': "MATCH (n:CASE) RETURN DISTINCT n.Case_Number AS name",
        'provisions': "MATCH (n:PROVISION) RETURN DISTINCT n.name AS name",
        'subjects': "MATCH (n:SUBJECT) RETURN DISTINCT n.name AS name",
        'judges': "MATCH (n:JUDGE) RETURN DISTINCT n.name AS name"
    }
    
    results = {}
    with driver.session() as session:
        for key, query in queries.items():
            result = session.run(query)
            results[key] = [record["name"] for record in result]
        print(results)
    return render_template('final_index.html', **results)

@app.route('/overall_graph', methods=['GET'])
def overall_graph():
    query = """
    MATCH (n)-[r]->(m)
    RETURN n, r, m
    LIMIT 1000
    """
    graph_html = create_graph(query)
    return graph_html.generate_html()

@app.route('/search_graph', methods=['POST'])
def search_graph():
    case_numbers = request.form.getlist('case_numbers')
    provisions = request.form.getlist('provisions')
    subjects = request.form.getlist('subjects')
    judges = request.form.getlist('judges')

    conditions = []
    if case_numbers:
        conditions.append(f"n:CASE AND n.Case_Number IN {case_numbers}")
    if provisions:
        conditions.append(f"n:PROVISION AND n.name IN {provisions}")
    if subjects:
        conditions.append(f"n:SUBJECT AND n.name IN {subjects}")
    if judges:
        conditions.append(f"n:JUDGE AND n.name IN {judges}")
    
    where_clause = " OR ".join(conditions)
    
    query = f"""
    MATCH (n)-[r]-(m)
    WHERE {where_clause}
    RETURN n, r, m
    LIMIT 1000
    """
    
    graph_html = create_graph(query)
    return graph_html.generate_html()

@app.route('/search_text', methods=['POST'])
def search_text():
    text = request.form.get('text')
    print(text)
    query = f"""
    MATCH (n)-[r]-(m)
    WHERE 
    NOT 'CHUNK' IN labels(n) AND
    NOT 'CHUNK' IN labels(m) AND
    (
        any(prop IN keys(n) WHERE toLower(toString(n[prop])) CONTAINS toLower('{text}')) OR
        any(prop IN keys(m) WHERE toLower(toString(m[prop])) CONTAINS toLower('{text}'))
    )
    RETURN n, r, m
    LIMIT 1000
    """
    graph_html = create_graph(query)
    return graph_html.generate_html()

@app.route('/add_node', methods=['POST'])
def add_node():
    node1_type = request.form.get('node1_type')
    node1_name = request.form.get('node1_name')
    relation_name = request.form.get('relation_name')
    node2_type = request.form.get('node2_type')
    node2_name = request.form.get('node2_name')
    if node1_type == "CASE" and node2_type != "CASE":   
        query = f"""
    MERGE (n1:{node1_type} {{Case_Number: '{node1_name}'}})
    MERGE (n2:{node2_type} {{name: '{node2_name}'}})
    MERGE (n1)-[r:{relation_name}]->(n2)
    """
    elif node2_type == "CASE" and node1_type != "CASE":
        query = f"""
    MERGE (n1:{node1_type} {{name: '{node1_name}'}})
    MERGE (n2:{node2_type} {{Case_Number: '{node2_name}'}})
    MERGE (n1)-[r:{relation_name}]->(n2)
    """
    elif node1_type == "CASE" and node2_type == "CASE": 
        query = f"""
        MERGE (n1:{node1_type} {{Case_Number: '{node1_name}'}})
        MERGE (n2:{node2_type} {{Case_Number: '{node2_name}'}})
        MERGE (n1)-[r:{relation_name}]->(n2)
        """
    else:
        query = f"""
        MERGE (n1:{node1_type} {{name: '{node1_name}'}})
        MERGE (n2:{node2_type} {{name: '{node2_name}'}})
        MERGE (n1)-[r:{relation_name}]->(n2)
        """
    with driver.session() as session:
        session.run(query)
    
    return jsonify({'status': 'Node and relationship added'})

@app.route('/delete_node', methods=['POST'])
def delete_node():
    node_type = request.form.get('node_type')
    node_name = request.form.get('node_name')
    if node_type == "CASE":
        query = f"""
        MATCH (n:{node_type} {{Case_Number: '{node_name}'}})
        DETACH DELETE n
        """
    else:
        query = f"""
        MATCH (n:{node_type} {{name: '{node_name}'}})
        DETACH DELETE n
        """
    with driver.session() as session:
        session.run(query)
    
    return jsonify({'status': 'Node deleted'})

# Initialize OpenAI client for vLLM server
client = OpenAI(
    base_url="http://172.25.0.211:8002/v1",
    api_key="EMPTY",  # No API key needed for local vLLM
)

# QA generation template system prompt for chat format
QA_GENERATION_TEMPLATE = """You are a RAG CHATBOT. Answer questions using the provided context by following the given step-by-step reasoning process internally, but only output the final answer.
 
(The following is the step-by-step reasoning process. Do not include this in your response.)
 
INTERNAL REASONING PROCESS:

Step 1: Understand the Question  

- Figure out what the user is asking.  
- Identify the main topic (e.g. case, person, statute).  
- Identify what details are needed (e.g. age, date, name).  

Step 2: Check the CYPHER

- Evaluate if the provided CYPHER is relevant to the user's question.  
- Ensure the CYPHER targets the correct entities or relationships needed to answer the question.

Step 3: Check the Context  

- Look at the CONTEXT provided.  
- See if it contains the details needed to answer the question.  
- Ensure the CONTEXT aligns with both the CYPHER query additionally.

Step 4: Decide the Answer  
- If CONTEXT has what is needed, use it to form the answer.  
- If CONTEXT does not have what is needed, say: "I cannot answer this based on the provided context."  

Step 5: Write the Answer  
- Give a direct and clear answer.  
- Use bullet points or numbers if there are multiple items.  
- Include key facts (e.g. names, dates, numbers).  
 
RESPONSE RULES:  
- Provide direct, concise answers when context contains relevant information.  
- If context truly lacks the answer: Respond with "I cannot answer this based on the provided context."  
- Examine structured data carefully — return all list or dictionary items when relevant.  
- IMPORTANT: For multiple items: use bullet points (•) or numbered lists.  
- Be concise but include specific details (names, numbers, dates) when available.  
- Only output your final answer, no reasoning steps.  
 
**Question:**  
{query}

**CYPHER:**  

{cypher_query}
 
**CONTEXT:**  
{context}
 
**Answer:**
"""

# Simple Cypher generation template for chat format
SIMPLE_CYPHER_GENERATION_TEMPLATE = """You are a Neo4j Cypher query generator. Generate accurate Cypher queries based on natural language questions using the SCHEMA provided below.

Schema:
{schema}

###RULES###
- When matching string properties like names, use case-insensitive matching with `toLower()` unless exact case is confirmed.
- Prefer using `WHERE toLower(node.property) CONTAINS toLower('value')` for name lookups, especially when users provide only partial or lowercase names.
- Avoid assuming exact casing, prefixes (like "SMT." or "MR."), or formatting in names and textual fields.
- Do not return any explanation, just return the Cypher query.
- Make sure that statutes are acts and provisions are sections of acts.
- Carefully study the nodes and relationships in the provided "Schema". Use only these nodes and relationships when creating the Cypher query. Do not invent or assume any nodes, labels, or relationships that are not present in the schema.

Examples:
User input: Find the lawyer in crrfc 7
Cypher query: MATCH (c:CASE {{Case_Number: 'crrfc 7'}})-[:HAS_LAWYER]-(l:LAWYER) RETURN c AS nod, l AS lawyer LIMIT 50

User input: Who is the judge in CR 221 2024
Cypher query: MATCH (c:CASE {{Case_Number: 'CR 221 2024'}})-[:HAS_JUDGE]-(judge:JUDGE) RETURN c AS nod, judge AS judge LIMIT 50

User input: What is the name and Advocate Bar Number of the Lawyer representing Karuna Gehlot?
Cypher query: MATCH (p:PETITIONER) WHERE toLower(p.name) CONTAINS toLower('Karuna Gehlot') MATCH (p)-[:REPRESENTED_BY]->(l:LAWYER) RETURN l.name AS name, l.Advocate_Bar_No_ AS Advocate_Bar_Number LIMIT 50

User input: Find the case with statute 'Hindu Marriage Act'
Cypher query: MATCH (s:STATUTE)<-[:HAS_STATUTE]-(c:CASE) WHERE toLower(s.name) = toLower('Hindu Marriage Act') RETURN c

User input: {query}
Cypher query:"""
# Full-text Cypher generation template for chat format
FULL_TEXT_CYPHER_GENERATION_TEMPLATE = """You are a Neo4j Graph Database Expert. Given an input question, generate a Cypher query using one of the predefined full-text indexes: "case_key" or "entity", depending on context. Use "case_key" for specific case numbers (e.g., "CR 221 2024", "crrfc 7", "FIR 23"). Use "entity" for people, places, or other named entities (e.g., "Karuna Gelhot", "Delhi Police"). Return only the Cypher query, nothing else. Occasionally, an error like "Failed to write data to connection" may occur due to network issues; if so, retry the query.

Schema:
{schema}

Examples:
User input: Find the lawyer in crrfc 7
Cypher query: CALL db.index.fulltext.queryNodes('case_key', "crrfc 7", {{limit: 10}}) YIELD node, score WITH node MATCH (node)-[]-(lawyer:LAWYER) RETURN node AS nod, lawyer AS lawyer LIMIT 50

User input: Who is the judge in CR 221 2024
Cypher query: CALL db.index.fulltext.queryNodes('case_key', "CR 221 2024", {{limit: 10}}) YIELD node, score WITH node MATCH (node)-[]-(judge:JUDGE) RETURN node AS nod, judge AS judge LIMIT 50

User input: Who is Karuna Gelhot
Cypher query: CALL db.index.fulltext.queryNodes('entity', "Karuna Gelhot", {{limit: 10}}) YIELD node, score RETURN node AS nod LIMIT 50

User input: {query}
Cypher query:"""

# Function to generate simple Cypher query using chat template
def generate_simple_cypher(query, schema, feedback=None):
    try:
        prompt = SIMPLE_CYPHER_GENERATION_TEMPLATE.format(schema=schema, query=query, feedback=feedback)
        logger.debug("prompt entered")
        
        if feedback:
            # Handle feedback and limit length
            safe_feedback = ' '.join(str(item) for item in feedback)[:200].replace('\n', ' ')
            prompt += f"\n\nNote: The previous attempt failed: {safe_feedback}. Adjust the query accordingly."

        logger.debug("feedback is present")

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"User input: {query}\nCypher query:"}
        ]

        logger.debug("output present")
        
        completion = client.chat.completions.create(
            model="meta-llama/Llama-3.1-8B-Instruct",
            messages=messages,
            temperature=0.2 if feedback else 0,  # Slightly higher temp for retries
            max_tokens=150,
            top_p=0.9,
            frequency_penalty=0.1,
            extra_body={"chat_template_kwargs": {"enable_thinking": True}},
        )
        print("Completion started")

        output = completion.choices[0].message.content.strip()
        # Write prompt and output to vllm_prompt.txt
        with open("vllm_prompt.txt", "w") as f:
            f.write(f"Prompt:\n{prompt}\n\nOutput:\n{output}")
        return output
    except Exception as e:
        print(f"Error generating simple Cypher query: {str(e)}")
        return None

   

# Function to generate full-text Cypher query using chat template
def generate_full_text_cypher(query, schema):
    entities = extract_entities_structured(query)
    index = "case_key" if entities.case else "entity"
    prompt = FULL_TEXT_CYPHER_GENERATION_TEMPLATE.format(schema=schema, query=query, index=index)
    try:
        messages = [
            {"role": "system", "content": FULL_TEXT_CYPHER_GENERATION_TEMPLATE.format(schema=schema, query=query)},
            {"role": "user", "content": f"User input: {query}\nCypher query:"}
        ]

        logger.debug("output in process")

        completion = client.chat.completions.create(
            model="meta-llama/Llama-3.1-8B-Instruct",
            messages=messages,
            temperature=0,
            max_tokens=100,
            top_p=0.9,
            frequency_penalty=0.1,
            extra_body={
                "chat_template_kwargs": {"enable_thinking": True},
            }
        )

        logger.debug("completion started")

        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating full-text Cypher query: {str(e)}")
        return None
# Global list to store timing data and lock for thread-safety
timing_data = []
data_lock = Lock()

# Function to save timing data to Excel
def save_timing_to_excel(filename="E:/Secondary download/intern/vll/query_timings.xlsx"):
    with data_lock:
        df = pd.DataFrame(timing_data)
        if os.path.exists(filename):
            # Append to existing file
            with pd.ExcelWriter(filename, mode='a', if_sheet_exists='replace') as writer:
                df.to_excel(writer, sheet_name="Timings", index=False)
        else:
            # Create new file
            df.to_excel(filename, sheet_name="Timings", index=False)


@app.route('/graph_qa', methods=['POST'])
def graph_qa():
    query = request.form.get('query')
    if not query:
        return jsonify({"error": "Missing 'query' field"}), 400
    query = remove_lucene_chars(query)
    
    max_retries = 2
    attempt = 0
    simple_cypher_time = 0.0
    full_text_cypher_time = 0.0
    structured_unstructured_time = 0.0
    response=""
    feedback_list = []
    last_query = None

    # Try simple Cypher query
    while attempt < max_retries:
     try:
        start_time = time.time()
        chain_query = generate_simple_cypher(query, graph.schema, feedback=feedback_list)
        if not chain_query:
            feedback = "Failed to generate a valid Cypher query"
            feedback_list.append(feedback)
            break

        logger.debug(f"Attempt {attempt + 1}: Simple cypher query: {chain_query}")
        context = graph.query(chain_query)
        logger.debug(f"Attempt {attempt + 1}: Simple cypher query context: {context}")

        if context:
            messages = [
                {"role": "system", "content": "You are a helpful RAG chatbot."},
                {"role": "user", "content": QA_GENERATION_TEMPLATE.format(
                    query=query, cypher_query=chain_query, context=context)}
            ]

            completion = client.chat.completions.create(
                model="meta-llama/Llama-3.1-8B-Instruct",
                messages=messages,
                temperature=0,
                max_tokens=500,
                top_p=0.9,
                frequency_penalty=0.1,
                extra_body={"chat_template_kwargs": {"enable_thinking": True}}
            )

            response_result = completion.choices[0].message.content.strip()
            cleaned_response = re.sub(
                r"I cannot answer this based on the provided context\.\s*--\s*I can answer it\s*", "", response_result
            ).strip()

            logger.debug(f"Generated Answer:\n{cleaned_response}")

            with open("Qa_gen.txt", "w") as f:
                f.write(json.dumps(QA_GENERATION_TEMPLATE.format(
                    query=query, cypher_query=chain_query, context=context, answer=cleaned_response
                ), indent=2))

            relevance_result = check_relevance_structured(query, chain_query, cleaned_response)
            logger.debug(f"Relevance check: {relevance_result}")

            if relevance_result.is_relevant:
                response = cleaned_response
                feedback_list.append("Query succeeded with relevant response")
                with data_lock:
                    timing_data.append({
                        "Query": query,
                        "Response": response,
                        "Simple_Cypher_Time": simple_cypher_time,
                        "Full_Text_Cypher_Time": full_text_cypher_time,
                        "Structured_Unstructured_Time": structured_unstructured_time
                    })
                save_timing_to_excel()
                return jsonify({"response": response, "chunks": []})
            else:
                feedback = f"Response not relevant for query: {chain_query}"
                feedback_list.append(feedback)
                logger.debug(feedback)
        else:
            feedback = f"Empty result or no matching nodes for query: {chain_query}"
            feedback_list.append(feedback)
            logger.debug(feedback)

     except CypherSyntaxError as syntax_error:
        feedback = f"Cypher syntax error in query '{chain_query}': {str(syntax_error)}"
        feedback_list.append(feedback)
        logger.error(feedback)

     except ServiceUnavailable as service_error:
        feedback = f"Database unavailable: {str(service_error)}"
        feedback_list.append(feedback)
        logger.error(feedback)
        break  # Don't retry if DB is down

     except DatabaseError as db_error:
        feedback = f"Database error: {str(db_error)}"
        feedback_list.append(feedback)
        logger.error(feedback)

     except Exception as e:
        feedback = f"Unexpected error: {str(e)}"
        feedback_list.append(feedback)
        logger.error(feedback)

    simple_cypher_time = time.time() - start_time
    logger.debug(f"Retrying simple cypher... Attempt {attempt + 1}")
    attempt += 1

    # Try full-text Cypher query
    attempt = 0
    while attempt < max_retries:
        try:
            start_time = time.time()
            chain_query = generate_full_text_cypher(query, graph.schema,feedback=feedback_list)
            if not chain_query:
                # log_output_and_schema(query, chain_query, context, errors, relevance_result, cleaned_response, graph.schema)
                logger.debug("No valid full-text Cypher query generated")
                break

            logger.debug(f"Full-text cypher query chain_query: {chain_query}")
            context = graph.query(chain_query)
            logger.debug(f"Full-text cypher query context: {context}")

            if chain_query and context:
                messages = [
                    {"role": "system", "content": QA_GENERATION_TEMPLATE},
                    {"role": "user", "content": f"Context: {context}\n\nQuestion: {query}\n\nAnswer:"}
                ]
                completion = client.chat.completions.create(
                    model="meta-llama/Llama-3.1-8B-Instruct",
                    messages=messages,
                    temperature=0,
                    max_tokens=500,
                    top_p=0.9,
                    frequency_penalty=0.1,
                    extra_body={"chat_template_kwargs": {"enable_thinking": True}}
                )
                response_result = completion.choices[0].message.content.strip()
                cleaned_response = re.sub(
                    r"I cannot answer this based on the provided context\.\s*--\s*I can answer it\s*", "", response_result
                     ).strip()
                logger.debug(f"Simple cypher raw response: {response_result}")
                logger.debug(f"Simple cypher cleaned response: {cleaned_response}")
                # Save QA generation details for analysis
                with open("Qa_gen.txt", "w") as f:
                 f.write(json.dumps(QA_GENERATION_TEMPLATE.format(
                  query=query,
                  cypher_query=chain_query,
                  context=context,
                  answer=cleaned_response
                 ), indent=2))
                relevance_result = check_relevance_structured(query, chain_query, response_result)
                logger.debug(f"Full-text cypher response result: {response_result}")
                full_text_cypher_time = time.time() - start_time

                if relevance_result.is_relevant:
                    response = cleaned_response

                    with data_lock:
                        timing_data.append({
                            "Query": query,
                            "Response": response,
                            "Simple_Cypher_Time": simple_cypher_time,
                            "Full_Text_Cypher_Time": full_text_cypher_time,
                            "Structured_Unstructured_Time": structured_unstructured_time
                        })
                    save_timing_to_excel()
                    return jsonify({"response": response, "chunks": []})
                else:
                    logger.debug("Full-text cypher output not relevant, falling back to structured/unstructured retriever")
                    break
            else:
                logger.debug("Full-text cypher query returned no results")
                break
              
        except Exception as e:
            logger.error(f"Error in full-text cypher query: {str(e)}")
            break

    full_text_cypher_time = time.time() - start_time
    attempt += 1
    logger.debug(f"Retrying full-text cypher... Attempt {attempt}")

    # Fallback to structured/unstructured retriever
    logger.debug("Falling back to structured/unstructured retriever")
    start_time = time.time()
    context, chunks = retriever(query)
    if "Error retrieving data" in context:
        response = "I cannot answer this based on the provided context."
        structured_unstructured_time = time.time() - start_time
        with data_lock:
            timing_data.append({
                "Query": query,
                "Response": response,
                "Simple_Cypher_Time": simple_cypher_time,
                "Full_Text_Cypher_Time": full_text_cypher_time,
                "Structured_Unstructured_Time": structured_unstructured_time
            })

        save_timing_to_excel()
        return jsonify({"response": response, "chunks": []})
    
    try:
        messages = [
            {"role": "system", "content": QA_GENERATION_TEMPLATE},
            {"role": "user", "content": f"Context: {context}\n\nQuestion: {query}\n\nAnswer:"}
        ]
        completion = client.chat.completions.create(
            model="meta-llama/Llama-3.1-8B-Instruct",
            messages=messages,
            temperature=0,
            max_tokens=500,
            top_p=0.9,
            frequency_penalty=0.1,
            extra_body={"chat_template_kwargs": {"enable_thinking": True}}
        )
        response = completion.choices[0].message.content.strip()
        logger.debug(f"Fallback response: {response}")
        structured_unstructured_time = time.time() - start_time
        with data_lock:
            timing_data.append({
                "Query": query,
                "Response": response,
                "Simple_Cypher_Time": simple_cypher_time,
                "Full_Text_Cypher_Time": full_text_cypher_time,
                "Structured_Unstructured_Time": structured_unstructured_time
            })

        save_timing_to_excel()
        return jsonify({"response": response, "chunks": chunks})
    except Exception as e:
        logger.error(f"Error in fallback LLM invocation: {str(e)}")
        response = "I cannot answer this based on the provided context."
        structured_unstructured_time = time.time() - start_time
        with data_lock:
            timing_data.append({
                "Query": query,
                "Response": response,
                "Simple_Cypher_Time": simple_cypher_time,
                "Full_Text_Cypher_Time": full_text_cypher_time,
                "Structured_Unstructured_Time": structured_unstructured_time
            })
        save_timing_to_excel()
        return jsonify({"response": response, "chunks": []})
    
if __name__ == '__main__':
    print("Starting Flask app")
    app.run(host="0.0.0.0", debug=True)

