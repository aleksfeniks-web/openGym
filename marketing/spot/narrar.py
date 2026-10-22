# Narración del spot: genera una frase por cue (voz.json), la ajusta a su espacio y arma voz.wav.
#   python narrar.py piper voz.onnx       -> voz con Piper (gratis)
#   python narrar.py elevenlabs           -> voz con ElevenLabs (ELEVENLABS_API_KEY y ELEVENLABS_VOICE_ID)
import json, os, subprocess, sys, wave, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
SR, TOTAL = 48000, 33.0
cues = json.load(open(os.path.join(HERE, 'voz.json'), encoding='utf-8'))
os.makedirs('voz', exist_ok=True)

def dur(p):
    out = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p], capture_output=True, text=True).stdout
    return float(out.strip())

def piper(modelo):
    from piper import PiperVoice, SynthesisConfig
    v = PiperVoice.load(modelo); cfg = SynthesisConfig(length_scale=0.95)
    for i, c in enumerate(cues):
        with wave.open(f'voz/raw_{i}.wav', 'wb') as w: v.synthesize_wav(c['texto'], w, syn_config=cfg)

def elevenlabs():
    key, vid = os.environ['ELEVENLABS_API_KEY'], os.environ['ELEVENLABS_VOICE_ID']
    model = os.environ.get('ELEVENLABS_MODEL') or 'eleven_multilingual_v2'
    for i, c in enumerate(cues):
        body = json.dumps({'text': c['texto'], 'model_id': model,
                           'voice_settings': {'stability': 0.45, 'similarity_boost': 0.8, 'style': 0.35, 'use_speaker_boost': True}}).encode()
        req = urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{vid}?output_format=mp3_44100_128', data=body,
                                     headers={'xi-api-key': key, 'Content-Type': 'application/json', 'Accept': 'audio/mpeg'})
        open(f'voz/raw_{i}.mp3', 'wb').write(urllib.request.urlopen(req, timeout=120).read())
        subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', f'voz/raw_{i}.mp3', f'voz/raw_{i}.wav'], check=True)

motor = sys.argv[1]
piper(sys.argv[2]) if motor == 'piper' else elevenlabs()

# cada frase: recorta silencios, acelera un poco si no cabe (máx 1.3×), y la coloca en su tiempo
parts, labels = [], []
for i, c in enumerate(cues):
    src = f'voz/raw_{i}.wav'; clean = f'voz/c_{i}.wav'
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', src, '-af',
                    'silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,aresample=48000',
                    '-ac', '1', clean], check=True)
    d = dur(clean); speed = min(1.3, max(1.0, d / c['max']))
    if speed > 1.0:
        subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', clean, '-af', f'atempo={speed:.3f}', f'voz/s_{i}.wav'], check=True); clean = f'voz/s_{i}.wav'
    print(f"{i}: {d:.2f}s (espacio {c['max']}s) velocidad {speed:.2f} — {c['texto']}")
    parts.append(clean); labels.append(int(c['t'] * 1000))
inputs = sum([['-i', p] for p in parts], [])
delays = ';'.join(f'[{i}:a]adelay={ms}|{ms}[d{i}]' for i, ms in enumerate(labels))
mix = ''.join(f'[d{i}]' for i in range(len(parts))) + f'amix=inputs={len(parts)}:normalize=0,apad=whole_dur={TOTAL},atrim=0:{TOTAL}[v]'
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', *inputs, '-filter_complex', delays + ';' + mix, '-map', '[v]', '-ar', str(SR), '-ac', '2', 'voz.wav'], check=True)
print('voz.wav listo')
