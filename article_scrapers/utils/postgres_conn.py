import os
import psycopg2
from psycopg2 import sql
import csv


def connect_to_db():
    """Connect to the PostgreSQL database and return the connection"""
    try:
        conn = psycopg2.connect(
            dbname="scraped_data",
            user="postgres",  
            password="francais", 
            host="localhost", 
            port="5432" 
        )
        print("✅ Connected to PostgreSQL database")
        return conn
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return None

def load_slate_csv_to_db(csv_file, conn):
    """
    Load data from CSV file to PostgreSQL database
    Ensures no duplicate entries are created based on word, source, title combination
    """
    if not conn:
        print("❌ No database connection available")
        return
    
    cursor = conn.cursor()
    rows_inserted = 0
    rows_skipped = 0
    
    try:
        # Read the CSV file
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            # Process each row in the CSV
            for row in reader:
                # Check if this word from this article already exists in the database
                check_query = sql.SQL("""
                    SELECT COUNT(*) FROM francais_word_frequency.word_data 
                    WHERE word = %s AND source = %s AND title = %s
                """)
                
                cursor.execute(check_query, (row['word'], row['source'], row['title']))
                count = cursor.fetchone()[0]
                
                # If record doesn't exist, insert it
                if count == 0:
                    insert_query = sql.SQL("""
                        INSERT INTO francais_word_frequency.word_data 
                        (word, source, date, title, frequency) 
                        VALUES (%s, %s, %s, %s, %s)
                    """)
                    
                    cursor.execute(insert_query, (
                        row['word'], 
                        row['source'], 
                        row['date'], 
                        row['title'], 
                        int(row['frequency']) if row['frequency'].isdigit() else row['frequency']
                    ))
                    rows_inserted += 1
                else:
                    rows_skipped += 1
        
        # Commit the transaction
        conn.commit()
        print(f"✅ Data from {csv_file} loaded to database: {rows_inserted} rows inserted, {rows_skipped} rows skipped (duplicates)")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error loading data to database: {e}")
    finally:
        cursor.close()