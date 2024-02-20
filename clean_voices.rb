require 'json'

# Read the entire content of 'prologue_text.txt' into the text variable
text = File.read("ff2_prologue.txt")

# Initialize an array to hold dialogues and the last speaker variable
dialogues = []
last_speaker = nil

# Split the text into sections, excluding those between '---'
sections = text.split("---").each_slice(2).map(&:last)

# Process each section
sections.each do |section|
  # Split the section into lines and process each line
  section.lines.each do |line|
    line.strip!
    next if line.empty? # Skip empty lines

    if line.include?(":")
      # Extract the name and dialogue
      name, dialogue = line.split(":", 2).map(&:strip)
      dialogues << {name: name, dialogue: dialogue}
      last_speaker = name
    elsif last_speaker
      # If the line does not contain a colon and there is a last speaker, append the line to the last speaker's dialogue
      dialogues.last[:dialogue] += " #{line}"
    else
      # If there is no last speaker (narration), attribute line to the narrator
#      dialogues << {name: "Narrator", dialogue: line}
#disable narrator for now, its going to be annoying till i have it more clear
    end
  end
end

# Output the parsed dialogues and narrations
dialogues.each do |dialogue|
  puts "#{dialogue[:name]} says: \"#{dialogue[:dialogue]}\""
end

# Save dialogues to a JSON file
File.open("dialogues_v2.json", "w") do |file|
    file.write(JSON.pretty_generate(dialogues))
end

# Prepare the voiceover names data structure
names = dialogues.map { |dialogue| dialogue[:name] }
voiceover_names = names.uniq.map do |name|
    {
      name: name,
      voiceover_name: "#{name}Voice"
    }
  end
  
  # Save the voiceover names to a JSON file
  File.open("characters_voiceover_v2.json", "w") do |file|
    file.write(JSON.pretty_generate(voiceover_names))
  end