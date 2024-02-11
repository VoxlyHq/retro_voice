
require 'json'
require 'open-uri'
require 'net/http'
load './play_ht.rb'
load './eleven_labs.rb'

lang = "en"

BASE_NAME = "ff4_v1_prologue_"
MAX_NUMBER_FILES = 1000 # Adjust based on the maximum number of files you expect

BACKEND_VOICE_PLATFORM = "elevenlabs" #htplay, elevenlabs
OUTPUT_FOLDER="output_#{lang}_#{BACKEND_VOICE_PLATFORM}"

def voice_over_parse()
    # Read dialogues from the JSON file
#    dialogues = JSON.parse(File.read("dialogues.json"))
    dialogues = JSON.parse(File.read("dialogues_short.json"))

    # Output the dialogues
    dialogues.each do |dialogue|
    puts "#{dialogue['name']} says: \"#{dialogue['dialogue']}\""
    end

    dialogues
end

def voice_to_name()
    # Read dialogues from the JSON file
    voices = JSON.parse(File.read("characters_voiceover_ht.json"))

    # Output the dialogues
    voices.each do |voice|
    puts "#{voice['name']}: \"#{voice['voiceover_name']}\""
    end

    voices
end

def voice_to_name_e11()
    # Read dialogues from the JSON file
    voices = JSON.parse(File.read("characters_voiceover_eleven.json"))

    # Output the dialogues
    voices.each do |voice|
    puts "#{voice['name']}: \"#{voice['voiceover_name']}\""
    end

    voices
end



def transcribe_voice(name, text) 
    puts "hello -#{text} - #{name}"
    ht_voice = @voices.find { |voice| voice['name'] == name }['voiceover_name']
    puts "transcribing -#{text} - #{ht_voice}"

#    ht_voice = "en-US-MichelleNeural"
    res_id = convert_ht(ht_voice, text)
    puts "result = #{res_id}"
    return res_id
end

def download_voice(res_id, task_id)
    puts "downloading -#{res_id}, task_id - #{task_id}"
    filename =  generate_filename(BASE_NAME, task_id, MAX_NUMBER_FILES)
    puts "generated - #{filename}"
    tempfile_path, duration = download_ht(res_id, 3)
    if tempfile_path == nil 
        puts "failed to download = #{res_id} - #{filename}"
        return 
    end
    File.rename(tempfile_path, filename)
    puts "weeee - #{tempfile_path} - #{duration}"

    return "success", "url"
end

def transcribe_and_down_e11_voice(name, text, task_id)
    puts "hello -#{text} - #{name}"
    e11_voice = @e11_voices.find { |voice| voice['name'] == name }['voiceover_name']
    puts "transcribing -#{text} - #{e11_voice}"
    filename =  generate_filename(BASE_NAME, task_id, MAX_NUMBER_FILES)
    puts "downloading -#{filename}, task_id - #{task_id}"

    convert_eleven(e11_voice, text, filename)
end



def generate_filename(base_name, number, max_number)
    # Determine the number of digits needed for the maximum number
    num_digits = max_number.to_s.length
  
    # Format the number with leading zeros
    formatted_number = number.to_s.rjust(num_digits, '0')
  
    # Combine the base name, formatted number, and file extension
    "#{OUTPUT_FOLDER}/#{base_name}#{formatted_number}.mp3"
  end


def thread_work(task)
    # Ask for Transcription of voice
    puts "thread_work #{task[:index]}: #{task["name"]} says: \"#{task["dialogue"]}\""

    if BACKEND_VOICE_PLATFORM == "elevenlabs"
        transcribe_and_down_e11_voice(task["name"], task["dialogue"], task[:index])
    elsif BACKEND_VOICE_PLATFORM == "htplay"
        res_id = transcribe_voice(task["name"], task["dialogue"])

        sleep 5
        download_voice(res_id, task[:index])
    else
        raise "unknown backend voice platform"
    end
end

# load and parse the voice over files into lines
# lineid, charecter, speech
voice_over_lines = voice_over_parse()



# Array to hold the threads
threads = []
max_threads = 10

# Create a Queue and add tasks to it
task_queue = Queue.new
voice_over_lines.each_with_index do |item, index|
    item_with_index = item.merge({"index": index})
    task_queue.push(item_with_index)
end
@voices = voice_to_name()
@e11_voices = voice_to_name_e11()

# Array to hold worker threads
workers = Array.new(max_threads) do
  Thread.new do
    begin
      while (task = task_queue.pop(true)) # Non-blocking pop; raises ThreadError when the queue is empty
        puts "Processing task #{task}"
        thread_work(task)
        puts "Task #{task} completed"
      end
    rescue ThreadError
      # Queue is empty, thread can exit
    end
  end
end

# Wait for all worker threads to finish
workers.each(&:join)

puts "All tasks have been processed."