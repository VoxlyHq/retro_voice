require 'eleven_labs'


ElevenLabs.configure do |config|
    config.api_key = "your_api_token"
end


ELEVEN_API_KEY=ENV["ELEVEN_API_KEY"]

@e11_client = ElevenLabs::Client.new(api_key: ELEVEN_API_KEY)
#voices = client.get('voices')
#voice_id = voices['voices'].first['voice_id']


def convert_eleven(voicename, content)
    speech = @e11_client.post("text-to-speech/#{voicename}", { text: content  }) # returns a binary string

    # Open a file in binary write mode
    File.open('weee.mp3', 'wb') do |file|
     file.write(speech)
    end
end


convert_eleven("N2lVS1w4EtoT3dr4eOWO", "Ah, the young lord returns triumphant! You did secure Mysidia's Crystal, did you not?")
