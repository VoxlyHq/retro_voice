require 'open-uri'
require 'json'

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