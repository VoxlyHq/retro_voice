import pandas as pd
import json

# Replace 'your_csv_file.csv' with the path to your actual CSV file
csv_file_path = 'final_fantasy_iv_jp_en_translations.csv'

# Load the CSV file
df = pd.read_csv(csv_file_path)

# Assuming the first column is for names and the second column is for dialogues
# Rename columns for clarity
df.columns = ['name', 'dialogue', 'english']

# Print all unique names
unique_names = df['name'].unique()
print("Unique names:", unique_names)

# Convert DataFrame to JSON format
json_format = df.to_dict('records')

# Optionally, save this JSON data to a file
with open('dialogues_jp_v2.json', 'w', encoding='utf-8') as f:
    json.dump(json_format, f, ensure_ascii=False, indent=2)

print("Conversion to JSON completed successfully!")
