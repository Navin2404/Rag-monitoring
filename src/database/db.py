# src/database/db.py
# SQLite use panrom - simple, no setup needed
# Ovvoru RAG call-um inga store aagum

import sqlite3
import json
from datetime import datetime
from pathlib import Path

# Database file path
DB_PATH = "monitoring.db"


def get_connection():
    """
    # SQLite connection undakkurom
    # Excel file mathiri - oru .db file-la ellam store aagum
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Results dict-ah varum
    return conn


def initialize_database():
    """
    # Tables undakkurom - ore oru time
    # Table = Excel sheet mathiri
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Main traces table - ovvoru query-um oru row
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS traces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,

            -- Query details
            query TEXT NOT NULL,
            answer TEXT NOT NULL,

            -- Latency metrics (milliseconds-la)
            total_latency_ms REAL,        -- Motha time
            retrieval_latency_ms REAL,    -- Search time mattum
            reranking_latency_ms REAL,    -- Rerank time mattum
            generation_latency_ms REAL,   -- LLM time mattum

            -- Token & Cost
            prompt_tokens INTEGER,        -- Input tokens count
            completion_tokens INTEGER,    -- Output tokens count
            total_tokens INTEGER,         -- Motha tokens
            cost_usd REAL,               -- Dollar-la cost

            -- Quality metrics
            num_sources INTEGER,          -- Ethana sources use aachu
            has_citation INTEGER,         -- Citation irukka? (1/0)
            quality_score REAL,          -- 0-1 scale quality

            -- Sentiment
            sentiment_label TEXT,         -- positive/negative/neutral
            sentiment_score REAL,         -- -1 to 1

            -- Status
            status TEXT DEFAULT 'success', -- success/error
            error_message TEXT            -- error vantha message
        )
    """)

    # Daily summary table - dashboard-la fast load-ku
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_summary (
            date TEXT PRIMARY KEY,
            total_queries INTEGER DEFAULT 0,
            avg_latency_ms REAL DEFAULT 0,
            p50_latency_ms REAL DEFAULT 0,
            p95_latency_ms REAL DEFAULT 0,
            total_cost_usd REAL DEFAULT 0,
            avg_quality_score REAL DEFAULT 0,
            error_rate REAL DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Database initialized!")


def save_trace(trace_data: dict):
    """
    # Oru query-oda ella metrics-um save panrom
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO traces (
            timestamp, query, answer,
            total_latency_ms, retrieval_latency_ms, 
            reranking_latency_ms, generation_latency_ms,
            prompt_tokens, completion_tokens, total_tokens, cost_usd,
            num_sources, has_citation, quality_score,
            sentiment_label, sentiment_score,
            status, error_message
        ) VALUES (
            :timestamp, :query, :answer,
            :total_latency_ms, :retrieval_latency_ms,
            :reranking_latency_ms, :generation_latency_ms,
            :prompt_tokens, :completion_tokens, :total_tokens, :cost_usd,
            :num_sources, :has_citation, :quality_score,
            :sentiment_label, :sentiment_score,
            :status, :error_message
        )
    """, trace_data)

    conn.commit()
    conn.close()


def get_all_traces(limit: int = 1000) -> list:
    """
    # Recent traces ellam edu - dashboard-ku
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM traces 
        ORDER BY timestamp DESC 
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()

    # Dict list-ah convert pannu
    return [dict(row) for row in rows]


def get_summary_stats() -> dict:
    """
    # Overall statistics - dashboard header-ku
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            COUNT(*) as total_queries,
            AVG(total_latency_ms) as avg_latency,
            SUM(cost_usd) as total_cost,
            AVG(quality_score) as avg_quality,
            SUM(CASE WHEN status='error' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as error_rate
        FROM traces
    """)

    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else {}