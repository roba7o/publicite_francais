import csv
import os
from datetime import datetime

def write_to_csv(data, output_dir="output"):
    """Writes parsed article data to a timestamped CSV file in the output directory."""
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Generate filename with today's date
    today = datetime.today().strftime('%Y-%m-%d')
    filename = os.path.join(output_dir, f"{today}.csv")

    # Check if file exists to decide on writing headers
    file_exists = os.path.isfile(filename)

    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["word", "source", "date", "title", "frequency"])

        # Write header only if file is new
        if not file_exists:
            writer.writeheader()

        # Write the parsed data
        for word, frequency in data["word_frequencies"].items():
            writer.writerow({
                "word": word,
                "source": data["source"],
                "date": data["date"],
                "title": data["title"],
                "frequency": frequency
            })
    
    print(f"✅ Data written to {filename}")
