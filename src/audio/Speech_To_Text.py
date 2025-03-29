import os
import wave
import pyaudio
import threading
from faster_whisper import WhisperModel

class AudioRecorder:
    def __init__(self, sample_rate=44100, channels=1, chunk_size=1024):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.pyaudio = None
        self.stream = None
        self.frames = []
        self.is_recording = False
        self.recording_thread = None

    def _record_thread(self):
        """
        Internal method to continuously record audio frames
        """
        while self.is_recording:
            data = self.stream.read(self.chunk_size)
            self.frames.append(data)

    def start_recording(self):
        """
        Start audio recording in a separate thread
        """
        self.pyaudio = pyaudio.PyAudio()
        self.stream = self.pyaudio.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size
        )
        
        self.is_recording = True
        self.frames = []
        
        # Start recording in a separate thread
        self.recording_thread = threading.Thread(target=self._record_thread)
        self.recording_thread.start()
        print("Recording started...")

    def stop_recording(self, output_filename="output.wav"):
        """
        Stop recording and save audio file
        """
        self.is_recording = True
        if not self.is_recording:
            print("Recording is not active.")
            return None

        # Arrêter l'enregistrement
        self.is_recording = False

        # Attendre que le thread d'enregistrement se termine
        if self.recording_thread:
            self.recording_thread.join()

        # Arrêter et fermer le flux audio
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()

        # Sauvegarder l'audio enregistré
        with wave.open(output_filename, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.pyaudio.get_sample_size(pyaudio.paInt16))  # Récupérer la largeur des échantillons avant terminate()
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(self.frames))

        print("Recording stopped...")
        print(f"Audio saved to: {output_filename}")

        # Terminer PyAudio après avoir écrit le fichier audio
        if self.pyaudio:
            self.pyaudio.terminate()

        return output_filename

    def transcribe_audio(self, audio_file, model_size="medium.en", device="cuda"):
        """
        Transcribe the recorded audio file
        """
        try:
            model = WhisperModel(model_size, device=device, compute_type="float16")
            segments, info = model.transcribe(audio_file)
            transcription = " ".join(segment.text for segment in segments)
            
            os.remove(audio_file)
            
            return transcription
        except Exception as e:
            print(f"Transcription error: {e}")
            return None

def main():
    recorder = AudioRecorder(sample_rate=16000, channels=1)
    
    # Example usage
    recorder.start_recording()
    import time
    time.sleep(10)  # Record for 5 seconds
    audio_file = recorder.stop_recording()
    
    if audio_file:
        transcription = recorder.transcribe_audio(audio_file)
        if transcription:
            print("Transcription:", transcription)

def record():
    pass

if __name__ == "__main__":
    main()