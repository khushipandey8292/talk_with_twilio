import tempfile
import wave
import whisper
import audioop
import os

class DummyAlternative:
    def __init__(self, transcript):
        self.transcript = transcript

class DummyResult:
    def __init__(self, transcript):
        self.alternatives = [DummyAlternative(transcript)]

class DummyResponse:
    def __init__(self, transcript):
        self.results = [DummyResult(transcript)]

class SpeechClientBridge:
    def __init__(self, streaming_config, on_response):
        self._on_response = on_response
        self.pcm_audio_chunks = []
        try:
            print("📦 Loading Whisper model...")
            self.model = whisper.load_model("base")
            print("✅ Whisper model loaded.")
        except Exception as e:
            print(f"❌ Whisper model loading failed: {e}")
            self.model = None

    def add_request(self, buffer):
        if buffer:
            try:
                decoded_8k = audioop.ulaw2lin(buffer, 2)  # output 16-bit PCM
                resampled_16k, _ = audioop.ratecv(decoded_8k, 2, 1, 8000, 16000, None)
                self.pcm_audio_chunks.append(resampled_16k)
            except Exception as e:
                print(f"❌ Audio decode error: {e}")

    def terminate(self):
        print("🛑 Call ended. Transcribing...")
        self.transcribe()

    def transcribe(self):
        if not self.model or not self.pcm_audio_chunks:
            print("⚠️ No model or no audio data. Skipping transcription.")
            return

        audio_data = b''.join(self.pcm_audio_chunks)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_path = temp_file.name
            with wave.open(temp_path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(audio_data)

        try:
            print(f"🧠 Transcribing from: {temp_path}")
            result = self.model.transcribe(temp_path, language="en", fp16=False)
            text = result.get("text", "").strip()
            if text:
                print(f"✅ Transcription: {text}")
                self._on_response(DummyResponse(text))
            else:
                print("⚠️ No transcription result.")
        except Exception as e:
            print(f"❌ Transcription error: {e}")
        # finally:
        #     os.remove(temp_path)






