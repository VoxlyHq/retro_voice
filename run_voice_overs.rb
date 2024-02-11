
require 'json'
require 'open-uri'
require 'net/http'

HT_API_KEY=ENV["HT_API_KEY"]
HT_USERNAME=ENV["HT_USERNAME"]

lang = "en"
OUTPUT_FOLDER="output_#{lang}_htplay"

BASE_NAME = "ff4_v1_prologue_"
MAX_NUMBER_FILES = 1000 # Adjust based on the maximum number of files you expect


def convert(htvoice, content)
    url = URI("https://play.ht/api/v1/convert")
  
    payload = {
    #  "voice": "en-US-MichelleNeural",
      "voice": htvoice, #"th-TH-ThanwaNeural",
      "speed": "0.3",
      "content": [
        content #   "either pass content s an array of strings , or ssml , but not both"
      ],
      "title": "Testing thai language"
    }.to_json
  
    headers = {
        'Authorization': HT_API_KEY,
        'X-User-ID': HT_USERNAME,
        'Content-Type': 'application/json'
    }
  
    http = Net::HTTP.new(url.host, url.port)
    http.use_ssl = true
    http.verify_mode = OpenSSL::SSL::VERIFY_PEER
  
    request = Net::HTTP::Post.new(url, headers)
    request.body = payload
  
    puts "request--"
    puts request.inspect 
  
    response = http.request(request)
    puts response.body
    data = JSON.parse(response.body)
    puts data
    return data["transcriptionId"]
end
  
def download_ht(transcriptionID, tries=0)
    audioDuration = 0
    if tries == 5 
        return nil
    end
    url = URI("https://play.ht/api/v1/articleStatus?transcriptionId=#{transcriptionID}")
  
  
    headers = {
      'Authorization': HT_API_KEY,
      'X-User-ID': HT_USERNAME,
      'Content-Type': 'application/json'
    }
  
    http = Net::HTTP.new(url.host, url.port)
    http.use_ssl = true
    http.verify_mode = OpenSSL::SSL::VERIFY_PEER
  
    request = Net::HTTP::Get.new(url, headers)
    #request.body = payload
  
    response = http.request(request)
    puts response.body
  
    #parse and get the url
    data = JSON.parse(response.body)
    puts "-#{transcriptionID}---#{data}"
  
    converted = data["converted"]
    if converted == false
      puts "not converted yet"
      sleep 5 
      tries = tries +1
      return download_ht(transcriptionID, tries)
    end
  
    transcriped = data["transcriped"]
    if transcriped == false
      puts "not transcriped yet"
      sleep 5 
      tries = tries +1
      return download_ht(transcriptionID, tries)
    end



    turl = data["audioUrl"]
    audio_duration = 0
    if data["audioDuration"] != nil 
        audio_duration = data["audioDuration"] * 1000
    end
    puts "audio_duration- #{audio_duration}"

    if turl == nil || turl == "" 
        puts "no url - #{transcriptionID}, should we try again?"
        puts "not transcribed yet"
        sleep 5 
        tries = tries +1
        return download_ht(transcriptionID, tries)
    end

    #download file
    puts "about to download --#{turl}--"
    url = URI(turl)
    downloaded_file = url.open()
    tempfile = Tempfile.new(['prefix', '.mp3'])
    tempfile.write(downloaded_file.read)
  
    downloaded_file.close
    tempfile.close
    tempfile.open
  
    tempfile_path = tempfile.path
    puts tempfile_path
    tempfile.close
    #tempfile.unlink # in theory this deletes the file, we should do when program is done
  
    return tempfile_path, audio_duration
  end

def voice_over_parse()
    # Read dialogues from the JSON file
#    dialogues = JSON.parse(File.read("dialogues.json"))
    dialogues = JSON.parse(File.read("dialogues.json"))

    # Output the dialogues
    dialogues.each do |dialogue|
    puts "#{dialogue['name']} says: \"#{dialogue['dialogue']}\""
    end

    dialogues
end

def voice_to_name()
    # Read dialogues from the JSON file
    voices = JSON.parse(File.read("characters_voiceover.json"))

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
    res_id = convert(ht_voice, text)
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
    res_id = transcribe_voice(task["name"], task["dialogue"])

    sleep 5
    download_voice(res_id, task[:index])
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