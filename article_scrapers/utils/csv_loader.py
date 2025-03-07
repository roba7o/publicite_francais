def load_slate_csv_to_db(csv_file, conn):
    """Loads data from a CSV file into PostgreSQL."""
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            cur = conn.cursor()
            
            # Copy CSV into the specified schema and table
            cur.copy_expert(
                "COPY francais_word_frequency.word_data (word, source, date, title, frequency) FROM STDIN WITH CSV HEADER DELIMITER ','",
                f
            )
            
            # Commit the transaction
            conn.commit()
            print(f"✅ Data successfully inserted from {csv_file} into PostgreSQL")

    except Exception as e:
        print(f"❌ Error loading CSV into PostgreSQL: {e}")
        conn.rollback()

    finally:
        cur.close()
