import assemblyai as aai
import elevenlabs
import os
from queue import Queue
from dotenv import load_dotenv


# Charger les variables d'environnement à partir du fichier .env
load_dotenv()

# Set API keys
aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")


# Récupérer la clé API depuis .env
elevenlabs_api_key = os.getenv('ELEVENLABS_API_KEY')

# Définir la clé API
elevenlabs.set_api_key(elevenlabs_api_key)


transcript_queue = Queue()

def on_data(transcript: aai.RealtimeTranscript):
    if not transcript.text:
        return
    if isinstance(transcript, aai.RealtimeFinalTranscript):
        transcript_queue.put(transcript.text + '')
        print("User:", transcript.text, end="\r\n")
    else:
        print(transcript.text, end="\r")

def on_error(error: aai.RealtimeError):
    print("An error occured:", error)

def handle_conversation(): 
    while True:
        transcriber = aai.RealtimeTranscriber(
            on_data=on_data,
            on_error=on_error,
            sample_rate=44_100,
        )

        # Start the connection
        transcriber.connect()

        # Open  the microphone stream
        microphone_stream = aai.extras.MicrophoneStream()

        # Stream audio from the microphone
        transcriber.stream(microphone_stream)

        # Close current transcription session with Crtl + C
        transcriber.close()

        # Retrieve data from queue
        transcript_result = transcript_queue.get()
        
    return transcript_result

def tell_the_response(text):
    # Convert the response to audio and play it
        audio = elevenlabs.generate(
            text=text,
            voice="Bella" # or any voice of your choice
        )

        #print("\nAI:", text, end="\r\n")

        elevenlabs.play(audio)
    
    
if __name__ == '__main__':
    handle_conversation()
            