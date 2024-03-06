import json

lang = "jp"  # Replace with 'en' or 'jp'

# Load the JSON data from the file
print(f'dialogues_{lang}_v2.json')
with open(f'dialogues_{lang}_v2.json', 'r') as file:
    dialogues = json.load(file)

print(dialogues)
# Add an 'id' field to each entry, incrementing for each
for i, dialogue in enumerate(dialogues, start=1):
    dialogue['id'] = i

# Save the modified data back to a file (or you can print it)
with open(f'dialogues_{lang}_web.json', 'w') as file:
    json.dump(dialogues, file, indent=2, ensure_ascii=False)

print("The file has been updated with IDs.")
