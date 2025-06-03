# import os
# import psycopg2
# from psycopg2 import sql
# import csv


# def connect_to_db():
#     """Connect to the PostgreSQL database and return the connection"""
#     try:
#         conn = psycopg2.connect(
#             dbname="scraped_data",
#             user="postgres",  
#             password="francais", 
#             host="localhost", 
#             port="5432" 
#         )
#         print("✅ Connected to PostgreSQL database")
#         return conn
#     except Exception as e:
#         print(f"❌ Database connection error: {e}")
#         return None

# def load_slate_csv_to_db(csv_file, conn):
#     """Improved version with bulk inserts and article tracking"""
#     if not conn:
#         print("❌ No database connection available")
#         return
    
#     cursor = conn.cursor()
#     rows_inserted = 0
#     rows_skipped = 0
    
#     try:
#         with open(csv_file, 'r', encoding='utf-8') as file:
#             reader = csv.DictReader(file)
            
#             # Group rows by article first
#             articles = {}
#             for row in reader:
#                 article_key = (row['title'], row['source'])
#                 if article_key not in articles:
#                     articles[article_key] = {
#                         'article_date': row['article_date'],
#                         'scraped_date': row['scraped_date'],
#                         'words': []
#                     }
#                 articles[article_key]['words'].append((row['word'], int(row['frequency'])))
            
#             # Process each article
#             for (title, source), data in articles.items():
#                 # Check if article exists
#                 cursor.execute("""
#                     INSERT INTO francais_word_frequency.scraped_articles 
#                     (title, source, article_date, scraped_date)
#                     VALUES (%s, %s, %s, %s)
#                     ON CONFLICT (title, source) DO NOTHING
#                     RETURNING article_id
#                 """, (title, source, data['article_date'], data['scraped_date']))
                
#                 result = cursor.fetchone()
#                 if result:  # New article inserted
#                     article_id = result[0]
#                     # Insert all words for this article
#                     word_data = [(article_id, word, freq) for word, freq in data['words']]
#                     cursor.executemany("""
#                         INSERT INTO francais_word_frequency.word_data 
#                         (article_id, word, frequency)
#                         VALUES (%s, %s, %s)
#                     """, word_data)
#                     rows_inserted += len(word_data)
#                 else:
#                     rows_skipped += len(data['words'])
        
#         conn.commit()
#         print(f"✅ Data loaded: {rows_inserted} words inserted, {rows_skipped} skipped (existing articles)")
        
#     except Exception as e:
#         conn.rollback()
#         print(f"❌ Error loading data: {e}")
#         raise  # Re-raise if you want calling code to handle it
#     finally:
#         cursor.close()