require 'eleven_labs'


ElevenLabs.configure do |config|
    config.api_key = "your_api_token"
end


ELEVEN_API_KEY=ENV["ELEVEN_API_KEY"]

client = ElevenLabs::Client.new(api_key: ELEVEN_API_KEY)
#voices = client.get('voices')
#voice_id = voices['voices'].first['voice_id']


def convert_eleven(voicename, content)
    speech = client.post("text-to-speech/#{voicename}", { text: 'your text' }) # returns a binary string
    puts speech
end