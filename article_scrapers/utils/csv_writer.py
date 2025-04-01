import csv
import os
from datetime import datetime

def write_to_csv(data, output_dir="output"):
    """Writes parsed article data to a timestamped CSV file in the output directory.
    Skips writing if the article already exists in the file."""
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename with today's date
    today = datetime.today().strftime('%Y-%m-%d')
    filename = os.path.join(output_dir, f"{today}.csv")
    
    # Check if the file exists and if the article is already in it
    existing_articles = set()
    if os.path.isfile(filename):
        with open(filename, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Create a unique identifier for each article (title + source)
                article_key = f"{row['title']}:{row['source']}"
                existing_articles.add(article_key)
        
    # Create a unique identifier for the current article
    current_article_key = f"{data['title']}:{data['source']}"
    
    # Skip if this article is already in the file
    if current_article_key in existing_articles:
        print(f"❌ Article '{data['title']}' from {data['source']} already exists in today's CSV. Skipping.")
        return
    
    # Open file in append mode if it exists, or write mode if it doesn't
    file_exists = os.path.isfile(filename)
    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["word", "source", "article_date", "scraped_date", "title", "frequency"])
        
        # Write header only if file doesn't exist yet
        if not file_exists:
            writer.writeheader()
        
        # Write the parsed data
        for word, frequency in data["word_frequencies"].items():
            writer.writerow({
                "word": word,
                "source": data["source"],
                "article_date": data["article_date"],
                "scraped_date": data["date_scraped"],
                "title": data["title"],
                "frequency": frequency
            })
    
    print(f"✅ Data for article '{data['title']}' written to {filename}")