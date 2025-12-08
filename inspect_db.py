import sqlite3
import os
from price_reversal_core.database_manager import DB_PATH

def inspect_database():
    """
    Connects to the SQLite database and displays the ten newest records.
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        print(f"Connecting to database: {DB_PATH}\n")

        # Query to select the ten newest records
        cursor.execute("SELECT * FROM pipeline_runs ORDER BY created_at DESC LIMIT 10")
        records = cursor.fetchall()

        if records:
            column_names = [description[0] for description in cursor.description]
            
            # Calculate maximum width for each column
            max_widths = [len(name) for name in column_names]
            for record in records:
                for i, item in enumerate(record):
                    max_widths[i] = max(max_widths[i], len(str(item)))
            
            # Print header
            header_line = " | ".join(f"{name:<{max_widths[i]}}" for i, name in enumerate(column_names))
            print(header_line)
            print("-" * len(header_line))

            # Print records
            for record in records:
                print(" | ".join(f"{str(item):<{max_widths[i]}}" for i, item in enumerate(record)))
        else:
            print("No records found in the pipeline_runs table.")

    except sqlite3.Error as e:
        print(f"Error accessing database: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    inspect_database()
