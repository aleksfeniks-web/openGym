# Música y efectos de sonido del spot de Reset Gym, sintetizados (sin samples de terceros).
# 120 BPM, La menor (Am – F – C – G). Escribe musica.wav y sfx.wav (48 kHz, estéreo).
import numpy as np, wave, json, os
SR = 48000
TOTAL = 33.0
N = int(SR * TOTAL)
rng = np.random.default_rng(7)
HERE = os.path.dirname(os.path.abspath(__file__))

def t_(d): return np.arange(int(SR * d)) / SR
def env(n, a, r, curve=4):
    e = np.ones(n)
    na = max(1, int(a * SR)); e[:na] = np.linspace(0, 1, na)
    nr = n - na; e[na:] = np.exp(-curve * np.linspace(0, 1, nr)) if nr > 0 else e[na:]
    return e
def add(buf, x, at, gain=1.0, pan=0.0):
    i = int(at * SR)
    if i >= len(buf): return
    x = x[: len(buf) - i] * gain
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    buf[i:i + len(x), 0] += x * l * 1.414
    buf[i:i + len(x), 1] += x * r * 1.414
def lowpass(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR); y = np.zeros_like(x); acc = 0.0
    for i in range(len(x)): acc = (1 - a) * x[i] + a * acc; y[i] = acc
    return y
def lp_fast(x, cutoff):  # filtro de un polo vectorizado por bloques (suficiente para ruido/pad)
    from scipy.signal import lfilter
    a = np.exp(-2 * np.pi * cutoff / SR)
    return lfilter([1 - a], [1, -a], x)
def hp_fast(x, cutoff):
    return x - lp_fast(x, cutoff)
def note(n): return 440.0 * 2 ** ((n - 69) / 12)

# ---------------- instrumentos
def kick():
    tt = t_(0.42); f = 50 + 110 * np.exp(-tt * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * env(len(tt), .002, .42, 5) + 0.25 * rng.standard_normal(len(tt)) * np.exp(-tt * 140)
def clap():
    tt = t_(0.25); n = rng.standard_normal(len(tt))
    n = hp_fast(n, 1200) * (np.exp(-tt * 22) + 0.6 * np.exp(-((tt - .012) ** 2) / 1e-5))
    return n * .55
def hat(open_=False):
    d = .22 if open_ else .05; tt = t_(d)
    return hp_fast(rng.standard_normal(len(tt)), 7000) * np.exp(-tt * (14 if open_ else 70)) * .35
def saw(freq, d, detune=0.0):
    tt = t_(d); out = 0
    for k, dt in enumerate([-detune, 0, detune]):
        ph = (tt * freq * (1 + dt)) % 1.0
        out = out + (2 * ph - 1)
    return out / 3
def bass(n, d):
    x = saw(note(n), d, .003) * 0.7 + np.sin(2 * np.pi * note(n) * t_(d)) * 0.6
    x = lp_fast(x, 420)
    return x * env(len(x), .005, d, 2.5) * .55
def pad(chord, d):
    x = sum(saw(note(n), d, .006) for n in chord) / len(chord)
    x = lp_fast(x, 1500)
    e = np.minimum(1, t_(d) / .35) * np.minimum(1, (d - t_(d)) / .4)
    return x * e * .32
def pluck(n, d=.35):
    tt = t_(d); x = saw(note(n), d) * np.exp(-tt * 9)
    return lp_fast(x, 2600) * .3

# ---------------- música
CH = {'Am': [57, 60, 64], 'F': [53, 57, 60], 'C': [52, 55, 60], 'G': [55, 59, 62]}
BASS = {'Am': 33, 'F': 29, 'C': 36, 'G': 31}
PROG = ['Am', 'F', 'C', 'G']
BEAT = 0.5
mus = np.zeros((N, 2))
for bar in range(int(TOTAL / 2) + 1):
    t0 = bar * 2.0; c = PROG[bar % 4]
    if t0 >= TOTAL: break
    groove = 3.0 <= t0 < 27.5
    finale = t0 >= 28.0
    # pad siempre (más fuerte en el final)
    add(mus, pad(CH[c], 2.0), t0, 1.0 if not finale else 1.3)
    if t0 < 3.0 and bar == 0: pass
    for b in range(4):
        tb = t0 + b * BEAT
        if tb >= TOTAL: break
        drop = 27.5 <= tb < 28.0
        if groove and not drop:
            add(mus, kick(), tb, .95)
            if b in (1, 3): add(mus, clap(), tb, .55, .1)
            add(mus, hat(), tb + BEAT / 2, .55, .25)
            add(mus, hat(), tb + BEAT / 4, .18, -.25)
            # bajo: corcheas con octava
            for k, off in enumerate([0, .25]):
                add(mus, bass(BASS[c] + (12 if (b == 3 and k == 1) else 0), .23), tb + off, .9)
        elif finale and tb < 31.0:
            add(mus, kick(), tb, .8 if b == 0 else .5)
            add(mus, hat(True), tb + BEAT / 2, .3, .2)
            add(mus, bass(BASS[c], .45), tb, .8)
    # arpegio tipo "pluck" en la parte media
    if 7.0 <= t0 < 27.0:
        arp = CH[c] + [CH[c][0] + 12]
        for i in range(8):
            add(mus, pluck(arp[i % 4] + 12), t0 + i * .25, .35, .35 if i % 2 else -.35)
# fade final
fade = np.ones(N); fs = int(31.2 * SR); fade[fs:] = np.linspace(1, 0, N - fs)
mus *= fade[:, None]

# ---------------- efectos
sfx = np.zeros((N, 2))
def whoosh(d=.55, up=True):
    tt = t_(d); n = rng.standard_normal(len(tt))
    # barrido de filtro: banda que sube/baja
    cuts = np.linspace(400, 6000, len(tt)) if up else np.linspace(6000, 400, len(tt))
    out = np.zeros_like(n); a_prev = 0.0
    for i0 in range(0, len(n), 256):
        seg = n[i0:i0 + 256]; c = cuts[i0]
        out[i0:i0 + 256] = hp_fast(lp_fast(seg, c * 1.6), c * .5)
    e = np.sin(np.pi * np.clip(tt / d, 0, 1)) ** 2
    return out * e * .9
def tick():
    tt = t_(.035); return np.sin(2 * np.pi * 2400 * tt) * np.exp(-tt * 180) * .25
def pop():
    tt = t_(.14); f = 900 + 900 * np.exp(-tt * 40)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 30) * .5
def ding():
    out = np.zeros(int(SR * 1.6))
    for i, (f, at) in enumerate([(1318.5, 0), (1760, .14)]):
        tt = t_(1.4); x = (np.sin(2 * np.pi * f * tt) + .35 * np.sin(2 * np.pi * f * 2.01 * tt) + .15 * np.sin(2 * np.pi * f * 3.02 * tt)) * np.exp(-tt * 3.2)
        o = int(at * SR); out[o:o + len(x)] += x[: len(out) - o]
    return out * .55
def riser(d=1.2):
    tt = t_(d); n = rng.standard_normal(len(tt)); out = np.zeros_like(n)
    for i0 in range(0, len(n), 256):
        c = 300 + 9000 * (i0 / len(n)) ** 2; out[i0:i0 + 256] = hp_fast(n[i0:i0 + 256], c * .4)
    sweep = np.sin(2 * np.pi * np.cumsum(200 + 1600 * (tt / d) ** 2) / SR) * .25
    return (out * .6 + sweep) * (tt / d) ** 2
def impact():
    tt = t_(1.8); f = 38 + 70 * np.exp(-tt * 9)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 2.2)
    crash = hp_fast(rng.standard_normal(len(tt)), 3000) * np.exp(-tt * 3.5) * .35
    return (boom + crash) * .95
def shimmer():
    tt = t_(1.2); x = sum(np.sin(2 * np.pi * note(n) * tt) for n in [81, 84, 88, 93]) / 4
    return x * np.exp(-tt * 2.5) * np.minimum(1, tt / .02) * .3
def buzz():
    tt = t_(.5); x = np.sin(2 * np.pi * 170 * tt) * (np.sin(2 * np.pi * 24 * tt) > 0)
    return lp_fast(x, 600) * .18

# transiciones
for tr in [3.15, 7.3, 11.4, 15.8, 20.0, 24.2]:
    add(sfx, whoosh(.55, True), tr - .32, .55, -.3)
# palabras
WORDS = [0.35, 0.62, 0.95, 3.3, 3.48, 3.6, 3.8, 4.25, 4.45, 4.7, 7.5, 7.7, 8.0, 11.5, 11.85, 12.4, 12.55, 12.7,
         15.9, 16.05, 16.2, 16.45, 20.1, 20.25, 20.4, 20.65, 21.0, 24.3, 24.65, 24.9]
for w in WORDS: add(sfx, tick(), w + .05, .5, 0)
# tarjetas y colores
for p in [8.25, 8.4, 8.55, 8.7, 8.9, 12.2, 12.75, 13.3, 16.7, 17.15, 17.6, 21.4, 21.62, 21.84, 22.06]:
    add(sfx, pop(), p + .04, .55, rng.uniform(-.4, .4))
add(sfx, whoosh(.5, False), 20.25, .45, .2)
# contador del panel
for k in range(18): add(sfx, tick(), 20.9 + k * .075, .25, .15)
# notificación
add(sfx, buzz(), 24.8, .7); add(sfx, ding(), 24.85, .9)
# cierre
add(sfx, riser(1.25), 26.8, .65); add(sfx, impact(), 28.03, 1.0); add(sfx, shimmer(), 29.15, .8); add(sfx, pop(), 29.15, .4)

def write(path, x, peak=.89):
    m = np.max(np.abs(x)) or 1; x = x / m * peak
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x * 32767).astype('<i2').tobytes())
write(os.path.join(HERE, 'musica.wav'), mus, .7)
write(os.path.join(HERE, 'sfx.wav'), sfx, .85)
print('ok')
