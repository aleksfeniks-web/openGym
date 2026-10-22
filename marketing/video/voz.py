# Narra cada escena con Piper y arma la pista de audio alineada con el video.
#   python voz.py modelo.onnx salida_dir        -> escribe duraciones.json y escena_N.wav
#   python voz.py --mezcla salida_dir video.timing.json pista.wav
import json, os, sys, wave

HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 30
LEAD = 0.35   # la voz entra un poco después del corte de escena
TAIL = 0.6    # y deja aire antes del siguiente

def narrar(modelo, out):
    from piper import PiperVoice
    try:
        from piper import SynthesisConfig
        cfg = SynthesisConfig(length_scale=0.92)
    except Exception:
        cfg = None
    voz = PiperVoice.load(modelo)
    lineas = json.load(open(os.path.join(HERE, 'narracion.json'), encoding='utf-8'))
    dur = []
    os.makedirs(out, exist_ok=True)
    for i, txt in enumerate(lineas):
        p = os.path.join(out, f'escena_{i}.wav')
        with wave.open(p, 'wb') as w:
            if cfg is not None: voz.synthesize_wav(txt, w, syn_config=cfg)
            else: voz.synthesize_wav(txt, w)
        with wave.open(p) as w: s = w.getnframes() / w.getframerate()
        dur.append(round(s + LEAD + TAIL, 2))
        print(f'escena {i}: {s:.2f}s')
    json.dump(dur, open(os.path.join(out, 'duraciones.json'), 'w'))

def mezclar(out, timing, pista):
    escenas = json.load(open(timing))
    starts, acc = [], 0
    for d in escenas:
        starts.append(acc / FPS); acc += int(d * FPS)
    total = acc / FPS
    with wave.open(os.path.join(out, 'escena_0.wav')) as w:
        rate, ch, sw = w.getframerate(), w.getnchannels(), w.getsampwidth()
    buf = bytearray(int(total * rate) * ch * sw)
    for i, st in enumerate(starts):
        with wave.open(os.path.join(out, f'escena_{i}.wav')) as w: data = w.readframes(w.getnframes())
        o = int((st + LEAD) * rate) * ch * sw
        buf[o:o + len(data)] = data[:max(0, len(buf) - o)]
    with wave.open(pista, 'wb') as w:
        w.setnchannels(ch); w.setsampwidth(sw); w.setframerate(rate); w.writeframes(bytes(buf))

if __name__ == '__main__':
    if sys.argv[1] == '--mezcla': mezclar(sys.argv[2], sys.argv[3], sys.argv[4])
    else: narrar(sys.argv[1], sys.argv[2])
