import json

# Load the JSON data from the file
with open('dialogues_en_v2.json', 'r') as file:
    dialogues = json.load(file)

# Add an 'id' field to each entry, incrementing for each
for i, dialogue in enumerate(dialogues, start=1):
    dialogue['id'] = i

# Save the modified data back to a file (or you can print it)
with open('dialogues_web.json', 'w') as file:
    json.dump(dialogues, file, indent=2)

print("The file has been updated with IDs.")
