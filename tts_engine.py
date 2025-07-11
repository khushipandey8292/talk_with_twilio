import os
import wave
import audioop
import tempfile
from bark.bark import SAMPLE_RATE, generate_audio
from scipy.io.wavfile import write as write_wav
import torch
print("🖥️ CUDA Available:", torch.cuda.is_available())

def generate_tts_and_encode(text: str) -> bytes:
    # 1. Generate audio using Bark
    print("🧠 Generating speech with Bark...")
    audio_array = generate_audio(text)

    # 2. Save audio to temporary .wav file (sample rate: 24000 Hz stereo)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as bark_wav_file:
        bark_wav_path = bark_wav_file.name
        write_wav(bark_wav_path, SAMPLE_RATE, audio_array)
        print(f"💾 Bark WAV saved: {bark_wav_path}")

    # 3. Convert to 8kHz mono WAV using ffmpeg
    final_wav_path = bark_wav_path.replace(".wav", "_8k.wav")
    cmd = f"ffmpeg -y -i {bark_wav_path} -ar 8000 -ac 1 -f wav {final_wav_path}"
    os.system(cmd)
    print(f"🎧 Resampled WAV saved: {final_wav_path}")

    # 4. Convert 16-bit PCM WAV to μ-law
    with wave.open(final_wav_path, 'rb') as wf:
        pcm_data = wf.readframes(wf.getnframes())
        ulaw_data = audioop.lin2ulaw(pcm_data, 2)  # 2 bytes = 16-bit

    # 5. Cleanup temp files
    # os.remove(bark_wav_path)
    # os.remove(final_wav_path)

    print("✅ μ-law audio ready.")
    return ulaw_data