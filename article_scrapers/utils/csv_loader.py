import psycopg2
import os
import shutil

def load_csv_to_db(csv_file, conn):
    """Loads data from a CSV file into PostgreSQL and deletes the file after."""
    temp_file = csv_file.replace(".csv", "_backup.csv")  # Rename for debugging
    
    try:
        cur = conn.cursor()
        
        with open(csv_file, "r", encoding="utf-8") as f:
            next(f)  # Skip header if CSV has one
            cur.copy_expert(
                "COPY words (word, source, date, title, frequency) FROM STDIN WITH CSV",
                f
            )

        conn.commit()
        print("✅ Data successfully inserted into PostgreSQL")

        # Rename for debugging, then delete after checking logs
        shutil.move(csv_file, temp_file)
        os.remove(temp_file)
        print(f"🗑️ Deleted: {temp_file}")

    except Exception as e:
        print(f"❌ Error loading CSV into PostgreSQL: {e}")
        conn.rollback()
    finally:
        cur.close()
