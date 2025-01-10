import speech_recognition as sr
from gtts import gTTS
import os
import pyaudio
import wave
from pydub import AudioSegment

class AudioProcessor:
    def __init__(self):
        self.recognizer = sr.Recognizer()

    def audio_to_text(self, audio_file):
        """
        Converts an audio file to text using Google's Speech Recognition API.
        """
        try:
            # Use pydub to handle various audio formats
            audio = AudioSegment.from_file(audio_file)  # Load audio file
            temp_wav = 'temp_audio.wav'
            audio.export(temp_wav, format='wav')  # Convert to WAV for speech recognition

            with sr.AudioFile(temp_wav) as source:
                audio_data = self.recognizer.record(source)
                return self.recognizer.recognize_google(audio_data)
        except Exception as e:
            return f"Error processing audio file: {e}"

    def text_to_audio(self, text, output_path):
        """
        Converts text to an audio file using Google Text-to-Speech.
        """
        try:
            tts = gTTS(text=text, lang='en')
            tts.save(output_path)
        except Exception as e:
            print(f"Error converting text to audio: {e}")

    def record_audio(self, filename, duration=5):
        """
        Records audio from the microphone and saves it as a WAV file.
        """
        chunk = 1024  # Record in chunks of 1024 samples
        sample_format = pyaudio.paInt16  # 16-bit resolution
        channels = 2  # Stereo
        fs = 44100  # 44.1kHz sampling rate
        p = pyaudio.PyAudio()

        print("Recording...")
        try:
            stream = p.open(format=sample_format, channels=channels, rate=fs, frames_per_buffer=chunk, input=True)
            frames = []

            for _ in range(0, int(fs / chunk * duration)):
                data = stream.read(chunk)
                frames.append(data)

            stream.stop_stream()
            stream.close()
            p.terminate()

            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(p.get_sample_size(sample_format))
                wf.setframerate(fs)
                wf.writeframes(b''.join(frames))
            print("Recording saved as:", filename)
        except Exception as e:
            print(f"Error recording audio: {e}")

    def process_audio_for_user(self, user_id, filename, db_manager):
        """
        Handles recording, transcription, and database storage for a user.
        """
        try:
            # Transcribe the recorded audio
            transcription = self.audio_to_text(filename)

            # Save transcription to a file
            transcription_filename = os.path.splitext(filename)[0] + '.txt'
            transcription_path = os.path.join('temp_audio_files', transcription_filename)

            os.makedirs('temp_audio_files', exist_ok=True)
            with open(transcription_path, 'w') as f:
                f.write(transcription)

            # Save the audio and transcription details in the database
            subject = "Recorded Audio"
            category = "General"
            audio_path = filename

            audio_id = db_manager.save_audio(user_id, subject, category, audio_path, transcription_path)
            db_manager.save_transaction(user_id, audio_id, 'record')

            return transcription
        except Exception as e:
            return f"Error processing audio for user: {e}"
