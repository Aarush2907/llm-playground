
import sqlite3
from datetime import datetime, timezone


def create_table():
    conn = sqlite3.connect("playground.db")

    try:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS request_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL,
                system_instruction TEXT,
                user_question TEXT NOT NULL,
                response_text TEXT NOT NULL,
                latency REAL NOT NULL,
                input_tokens INTEGER,
                output_tokens INTEGER,
                total_tokens INTEGER,
                input_cost REAL,
                output_cost REAL,
                total_cost REAL,
                created_at TEXT NOT NULL
            )
        """)

        conn.commit()
    finally:
        conn.close()


def save_request(
    model_name,
    system_instruction,
    user_question,
    response_text,
    latency,
    input_tokens,
    output_tokens,
    total_tokens,
    input_cost,
    output_cost,
    total_cost
):
    conn = sqlite3.connect("playground.db")

    try:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO request_logs (
                model_name,
                system_instruction,
                user_question,
                response_text,
                latency,
                input_tokens,
                output_tokens,
                total_tokens,
                input_cost,
                output_cost,
                total_cost,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            model_name,
            system_instruction,
            user_question,
            response_text,
            latency,
            input_tokens,
            output_tokens,
            total_tokens,
            input_cost,
            output_cost,
            total_cost,
            datetime.now(timezone.utc).isoformat()
        ))

        conn.commit()
    finally:
        conn.close()



def get_recent_requests(limit=10):
    conn = sqlite3.connect("playground.db")

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM request_logs
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        return rows

    finally:
        conn.close()





if __name__ == "__main__":
    create_table()
    print("Database table is ready.")
    rows = get_recent_requests(3)
    print(rows)
    print(type(rows))

