import sqlite3
import os
from datetime import datetime
from typing import Dict, Any

DATABASE_NAME = "pipeline_metrics.db"
DB_PATH = os.path.join(os.path.dirname(__file__), DATABASE_NAME)

def initialize_database():
    """
    Initializes the SQLite database and creates the metrics table if it doesn't exist.
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                input_filename TEXT NOT NULL,
                output_filename TEXT NOT NULL,
                word_count INTEGER,
                flesch_kincaid_grade REAL,
                cosine_relevance REAL,
                relevance_keywords_found INTEGER,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()
        print(f"Database '{DATABASE_NAME}' initialized successfully.")
    except sqlite3.Error as e:
        print(f"Error initializing database: {e}")
    finally:
        if conn:
            conn.close()

def insert_metrics_record(
    input_filename: str,
    output_filename: str,
    metrics: Dict[str, Any]
):
    """
    Inserts a new record into the pipeline_runs table.
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        created_at = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO pipeline_runs (
                input_filename,
                output_filename,
                word_count,
                flesch_kincaid_grade,
                cosine_relevance,
                relevance_keywords_found,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            input_filename,
            output_filename,
            metrics.get('word_count'),
            metrics.get('flesch_kincaid_grade'),
            metrics.get('cosine_relevance'),
            metrics.get('relevance_keywords_found'),
            created_at
        ))
        conn.commit()
        print(f"Metrics for run '{input_filename}' stored successfully.")
    except sqlite3.Error as e:
        print(f"Error inserting metrics record: {e}")
    finally:
        if conn:
            conn.close()

