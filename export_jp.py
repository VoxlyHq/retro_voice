from bs4 import BeautifulSoup

# Load the HTML content
with open("script_jp.html", "r", encoding="utf-8") as file:
    html_content_jp = file.read()

# Parse the HTML
soup_jp = BeautifulSoup(html_content_jp, 'html.parser')

# Find all tables in the document, since the structure repeats, we assume similar structure throughout the document
tables_jp = soup_jp.find_all('table')

# Initialize a list to collect data
data_rows = []

# Iterate over each table and extract relevant information
for table in tables_jp:
    rows = table.find_all('tr')
    for row in rows:
        # Check if row has three columns for character name, Japanese text, and English text
        cols = row.find_all('td')
        if len(cols) == 3:
            # Extract character name, which might be in a 'name' class or directly in the td
            char_name = cols[0].text.strip().replace('\n', ' ').replace('(Cecil)', '').replace('(Rosa)', '').replace('(Kain)', '').replace('(Cid)', '').replace('(Baigan)', '').replace('(King)', '').replace('(Maid)', '').replace('(Crew)', '').replace('(Black Wizard)', '').replace('(White Wizard)', '').replace('(Elder)', '')
            # Extract Japanese and English text
            jp_text = cols[1].text.strip().replace('\n', ' ')
            en_text = cols[2].text.strip().replace('\n', ' ')
            # Append extracted data to the list
            data_rows.append([char_name, jp_text, en_text])

# Convert the list to a DataFrame
import pandas as pd

df_jp = pd.DataFrame(data_rows, columns=["Character Name", "Japanese Text", "English Text"])

# Save the DataFrame to a CSV file
csv_file_path_jp = "final_fantasy_iv_jp_en_translations.csv"
df_jp.to_csv(csv_file_path_jp, index=False)

csv_file_path_jp