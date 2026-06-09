# app.py
# Project 1-oda RAG pipeline + Monitoring layer serkirom
# Ovvoru step-um time measure panrom

import streamlit as st
import time
from datetime import datetime
from dotenv import load_dotenv
import os

# Monitoring imports
from src.monitoring.tracer import TraceContext
from src.monitoring.cost_tracker import calculate_cost
from src.monitoring.quality_scorer import analyze_sentiment, calculate_quality_score
from src.database.db import initialize_database, save_trace

# RAG imports - Project 1-la irunthu
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import ChatPromptTemplate
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder
import numpy as np

load_dotenv()

# DB initialize pannu - app start-la
initialize_database()

# Page config
st.set_page_config(
    page_title="RAG + Monitoring 📊",
    page_icon="📊",
    layout="wide"
)

st.title("📊 RAG with Full Observability")
st.caption("Every query tracked — latency, cost, quality, sentiment")

SYSTEM_PROMPT = """You are a helpful assistant. Answer ONLY from the context below.
Every claim must have a citation: [Source: filename, Page: X]
If answer not found, say: "I cannot find this information in the provided documents"

Context:
{context}
"""


@st.cache_resource
def setup_rag():
    """RAG components ore oru time setup"""

    # Documents load pannu
    from pathlib import Path
    docs = []
    for f in Path("data").rglob("*.txt"):
        loader = TextLoader(str(f), encoding="utf-8")
        docs.extend(loader.load())

    # Split pann
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)

    # Vector store
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vector_store = Chroma.from_documents(chunks, embeddings, persist_directory="./chroma_db")

    # BM25
    tokenized = [c.page_content.lower().split() for c in chunks]
    bm25 = BM25Okapi(tokenized)

    # Reranker
    reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

    # LLM
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

    return vector_store, bm25, chunks, reranker, llm


def monitored_query(question: str) -> dict:
    """
    # RAG query + automatic monitoring
    # ovvoru step-um time measure panrom
    """

    # Trace context start pannu - stopwatch on!
    trace = TraceContext(query=question)

    try:
        vector_store, bm25, chunks, reranker, llm = setup_rag()

        # ─── STEP 1: RETRIEVAL ───
        trace.start_retrieval()

        # Vector search
        vector_results = vector_store.similarity_search_with_score(question, k=10)

        # BM25 search
        tokenized_query = question.lower().split()
        bm25_scores = bm25.get_scores(tokenized_query)
        top_bm25_idx = np.argsort(bm25_scores)[::-1][:10]

        # Hybrid combine pannu
        combined = {}
        chunk_map = {}

        for rank, (doc, score) in enumerate(vector_results):
            cid = doc.page_content[:80]
            combined[cid] = combined.get(cid, 0) + 0.6 * (1 / (rank + 60))
            chunk_map[cid] = doc

        for rank, idx in enumerate(top_bm25_idx):
            if bm25_scores[idx] > 0:
                cid = chunks[idx].page_content[:80]
                combined[cid] = combined.get(cid, 0) + 0.4 * (1 / (rank + 60))
                chunk_map[cid] = chunks[idx]

        hybrid_results = sorted(combined.items(), key=lambda x: x[1], reverse=True)[:10]
        hybrid_docs = [{"chunk": chunk_map[cid]} for cid, _ in hybrid_results]

        trace.end_retrieval()  # Search mudinjathu - time record!

        # ─── STEP 2: RERANKING ───
        trace.start_reranking()

        pairs = [(question, r["chunk"].page_content) for r in hybrid_docs]
        scores = reranker.predict(pairs)

        for i, r in enumerate(hybrid_docs):
            r["rerank_score"] = float(scores[i])

        reranked = sorted(hybrid_docs, key=lambda x: x["rerank_score"], reverse=True)[:5]

        trace.end_reranking()  # Rerank mudinjathu!

        # ─── STEP 3: GENERATION ───
        trace.start_generation()

        # Context format pannu
        context_parts = []
        for i, r in enumerate(reranked):
            chunk = r["chunk"]
            source = os.path.basename(chunk.metadata.get("source", "Unknown"))
            page = chunk.metadata.get("page", "N/A")
            context_parts.append(f"[Doc {i + 1}] Source: {source}, Page: {page}\n{chunk.page_content}")
        context = "\n---\n".join(context_parts)

        # LLM call pannu
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", "{question}")
        ])
        chain = prompt | llm
        response = chain.invoke({"context": context, "question": question})
        answer = response.content

        trace.end_generation()  # LLM mudinjathu!

        # ─── STEP 4: CALCULATE METRICS ───
        trace.finish()  # Total time record!

        # Token count (approximate)
        prompt_tokens = len(context.split()) + len(question.split())
        completion_tokens = len(answer.split())

        # Cost calculate pannu
        cost_info = calculate_cost("gpt-3.5-turbo", prompt_tokens, completion_tokens)

        # Quality check
        has_citation = "[Source:" in answer or "Source:" in answer
        quality_score = calculate_quality_score(answer, has_citation, len(reranked))

        # Sentiment analyze pannu
        sentiment = analyze_sentiment(question)

        # ─── STEP 5: DATABASE-LA SAVE ───
        trace_data = {
            "timestamp": datetime.now().isoformat(),
            "query": question,
            "answer": answer,
            "total_latency_ms": trace.total_latency_ms,
            "retrieval_latency_ms": trace.retrieval_latency_ms,
            "reranking_latency_ms": trace.reranking_latency_ms,
            "generation_latency_ms": trace.generation_latency_ms,
            "prompt_tokens": cost_info["prompt_tokens"],
            "completion_tokens": cost_info["completion_tokens"],
            "total_tokens": cost_info["total_tokens"],
            "cost_usd": cost_info["cost_usd"],
            "num_sources": len(reranked),
            "has_citation": 1 if has_citation else 0,
            "quality_score": quality_score,
            "sentiment_label": sentiment["sentiment_label"],
            "sentiment_score": sentiment["sentiment_score"],
            "status": "success",
            "error_message": None
        }

        save_trace(trace_data)  # DB-la save!

        return {
            "answer": answer,
            "metrics": trace_data,
            "sources": reranked
        }

    except Exception as e:
        # Error-um track panrom!
        trace.finish()

        error_trace = {
            "timestamp": datetime.now().isoformat(),
            "query": question,
            "answer": "",
            "total_latency_ms": trace.total_latency_ms,
            "retrieval_latency_ms": 0,
            "reranking_latency_ms": 0,
            "generation_latency_ms": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "cost_usd": 0,
            "num_sources": 0,
            "has_citation": 0,
            "quality_score": 0,
            "sentiment_label": "neutral",
            "sentiment_score": 0,
            "status": "error",
            "error_message": str(e)
        }
        save_trace(error_trace)
        raise e


# ─── UI ───
col1, col2 = st.columns([2, 1])

with col1:
    question = st.text_input("Question Kelu:", placeholder="What is the leave policy?")

    if st.button("🔍 Ask", type="primary") and question:
        with st.spinner("Processing..."):
            try:
                result = monitored_query(question)

                st.success("✅ Answer Found!")
                st.markdown("### 💡 Answer")
                st.markdown(result["answer"])

            except Exception as e:
                st.error(f"Error: {e}")

with col2:
    # Live metrics sidebar-la kaattu
    if question and "result" in dir():
        metrics = result.get("metrics", {})
        st.markdown("### ⚡ Live Metrics")
        st.metric("Total Time", f"{metrics.get('total_latency_ms', 0):.0f}ms")
        st.metric("Cost", f"${metrics.get('cost_usd', 0):.5f}")
        st.metric("Quality", f"{metrics.get('quality_score', 0):.2f}/1.0")
        st.metric("Sentiment", metrics.get('sentiment_label', 'N/A'))

st.markdown("---")
st.markdown("📊 [View Full Dashboard](http://localhost:8502) | Run: `streamlit run dashboard.py --server.port 8502`")