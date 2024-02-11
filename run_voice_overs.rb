
require 'json'



def voice_over_parse()
    # Read dialogues from the JSON file
    dialogues = JSON.parse(File.read("dialogues.json"))

    # Output the dialogues
    dialogues.each do |dialogue|
    puts "#{dialogue['name']} says: \"#{dialogue['dialogue']}\""
    end

    dialogues
end

def voice_to_name()
    res = File.readlines('voice_names_playht.txt').map do |line|
        line.chomp.split(',')
    end

    res
end

def transcribe_voice(text) 


end

def download_voice(id)
end


def thread_work(task)
    # Ask for Transcription of voice
    id = transcribe_voice(voice_over_lines[i])

    # try up to 3 times
    3.times do |x|
        sleep 1
        res, url = download_voice(id)
        if res == 'success'
            break
        end
    end
end

# load and parse the voice over files into lines
# lineid, charecter, speech
voice_over_lines = voice_over_parse()



# Array to hold the threads
threads = []
max_threads = 3

# Create a Queue and add tasks to it
task_queue = Queue.new
voice_over_lines.each { |i| task_queue.push(i) }

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