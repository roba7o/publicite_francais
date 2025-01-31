import csv
import os

def write_to_csv(data, filename='output.csv'):
    """Writes the parsed article data to a CSV file"""
    file_exists = os.path.isfile(filename)
    
    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["word", "source", "date", "title", "frequency"])
        
        # Write header only if file doesn't exist
        if not file_exists:
            writer.writeheader()
        
        # Write the parsed data
        for word, frequency in data['word_frequencies'].items():
            writer.writerow({
                'word': word,
                'source': data['source'],
                'date': data['date'],
                'title': data['title'],
                'frequency': frequency
            })
    print(f"Data written to {filename}")
