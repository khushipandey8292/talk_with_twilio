import numpy as np
import wave

def create_beep_wav(filename="beep.wav", duration=0.5, freq=1000, rate=8000):
    t = np.linspace(0, duration, int(rate * duration), False)
    tone = (np.sin(2 * np.pi * freq * t) * 32767).astype(np.int16)

    with wave.open(filename, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(tone.tobytes())

    print(f"✅ beep.wav created at: {filename}")

# Run this directly if executed
if __name__ == "__main__":
    create_beep_wav()
