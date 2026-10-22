# Reset Gym — video vertical 1080x1920 (Reels / TikTok / historias), 30 fps.
import subprocess, math, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
F = os.path.join(HERE, 'fonts') + '/'
SH = os.path.join(HERE, 'shots') + '/'
LIME, CYAN, BG = (142, 224, 0), (30, 184, 240), (10, 10, 10)
GRAY, LIGHT = (160, 160, 165), (191, 191, 191)

STAR_FONT = next((p for p in ['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'] if os.path.exists(p)), None)
def font(name, size): return ImageFont.truetype(F + name + '.ttf', size)
TITLE = font('BarlowCondensed-Black', 132)
TITLE_S = font('BarlowCondensed-Black', 104)
KICK = font('Barlow-Bold', 30)
SUB = font('Barlow-Regular', 42)
BEN = font('Barlow-SemiBold', 44)
SMALL = font('Barlow-SemiBold', 34)

def ease(x): x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3
def clamp(x): return max(0.0, min(1.0, x))

# --- fondo: negro con brillos de neón cian (izq) y lima (der), como el kit de Reset Supply
def make_bg():
    bg = Image.new('RGB', (W, H), BG)
    glow = Image.new('RGB', (W, H), (0, 0, 0))
    d = ImageDraw.Draw(glow)
    d.ellipse([-420, 300, 260, 1500], fill=(10, 70, 95))
    d.ellipse([820, 600, 1500, 1800], fill=(50, 85, 0))
    glow = glow.filter(ImageFilter.GaussianBlur(170))
    bg = Image.blend(bg, glow, 0.55)
    # piso reflejante: banda tenue abajo
    floor = Image.new('L', (W, H), 0)
    ImageDraw.Draw(floor).rectangle([0, 1700, W, H], fill=40)
    floor = floor.filter(ImageFilter.GaussianBlur(60))
    bg.paste((24, 24, 26), (0, 0), floor)
    return bg
BGIMG = make_bg()

def gradient(w, h, stops, vertical=True):
    g = Image.new('RGB', (w, h))
    px = g.load()
    n = h if vertical else w
    for i in range(n):
        t = i / max(1, n - 1)
        for k in range(len(stops) - 1):
            a, b = stops[k], stops[k + 1]
            if a[0] <= t <= b[0]:
                u = (t - a[0]) / max(1e-6, b[0] - a[0])
                c = tuple(int(a[1][j] + (b[1][j] - a[1][j]) * u) for j in range(3))
                break
        if vertical:
            for x in range(w): px[x, i] = c
        else:
            for y in range(h): px[i, y] = c
    return g

CHROME = [(0, (242, 242, 242)), (0.55, (154, 154, 154)), (1, (230, 230, 230))]
NEON = [(0, CYAN), (1, LIME)]

def text_img(txt, fnt, fill=None, grad=None, tracking=0):
    # renderiza texto (con tracking opcional) a una imagen RGBA recortada
    chars = list(txt)
    widths = [fnt.getlength(c) for c in chars]
    tw = int(sum(widths) + tracking * (len(chars) - 1)) + 8
    asc, desc = fnt.getmetrics()
    th = asc + desc + 8
    mask = Image.new('L', (tw, th), 0)
    d = ImageDraw.Draw(mask)
    x = 4
    for c, w in zip(chars, widths):
        d.text((x, 4), c, font=fnt, fill=255); x += w + tracking
    if grad:
        col = gradient(tw, th, grad, vertical=(grad is CHROME))
    else:
        col = Image.new('RGB', (tw, th), fill)
    out = Image.new('RGBA', (tw, th), (0, 0, 0, 0)); out.paste(col, (0, 0), mask)
    return out.crop(mask.getbbox() or (0, 0, 1, 1))

def wrap(txt, fnt, maxw):
    words, lines, cur = txt.split(), [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if fnt.getlength(t) <= maxw: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def paste_alpha(base, im, xy, alpha):
    if alpha <= 0: return
    if alpha < 1:
        im = im.copy(); a = im.getchannel('A').point(lambda v: int(v * alpha)); im.putalpha(a)
    base.alpha_composite(im, (int(xy[0]), int(xy[1])))

# --- teléfono con una pantalla real de la app
PH_H = 1120
def phone(shot):
    s = Image.open(SH + shot + '.png').convert('RGB')
    sw = int(PH_H * s.width / s.height)
    s = s.resize((sw, PH_H), Image.LANCZOS)
    pad, r = 16, 58
    fw, fh = sw + pad * 2, PH_H + pad * 2
    fr = Image.new('RGBA', (fw + 8, fh + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(fr)
    edge = gradient(fw + 8, fh + 8, NEON)
    m = Image.new('L', fr.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, fw + 7, fh + 7], r + 4, fill=255)
    fr.paste(edge, (0, 0), m)
    d.rounded_rectangle([4, 4, fw + 3, fh + 3], r, fill=(22, 22, 24))
    sm = Image.new('L', s.size, 0); ImageDraw.Draw(sm).rounded_rectangle([0, 0, sw - 1, PH_H - 1], r - 14, fill=255)
    fr.paste(s, (4 + pad, 4 + pad), sm)
    # sombra
    out = Image.new('RGBA', (fr.width + 120, fr.height + 120), (0, 0, 0, 0))
    sh = Image.new('L', out.size, 0); ImageDraw.Draw(sh).rounded_rectangle([60, 80, 60 + fr.width, 80 + fr.height], r, fill=170)
    sh = sh.filter(ImageFilter.GaussianBlur(30))
    out.paste((0, 0, 0), (0, 0), sh); out.alpha_composite(fr, (60, 60))
    return out

MARK = Image.open(os.path.join(HERE, 'mark.png')).convert('RGBA')
LOGO_SM = MARK.resize((150, 150), Image.LANCZOS)

def header(frame, t):
    # logo chico + "RESET GYM" arriba, fijo en las escenas de uso
    paste_alpha(frame, LOGO_SM, (60, 70), 1)
    paste_alpha(frame, WORDMARK_SM, (220, 112), 1)

WORDMARK = text_img('RESET GYM', font('BarlowCondensed-ExtraBoldItalic', 190), grad=NEON)
WORDMARK_SM = text_img('RESET GYM', font('BarlowCondensed-ExtraBoldItalic', 74), grad=NEON)
def tag_img():
    a = text_img('PROFESSIONAL', KICK, fill=LIGHT, tracking=9); b = text_img('GYM CARE', KICK, fill=LIGHT, tracking=9)
    st = text_img('★', ImageFont.truetype(STAR_FONT, 28), fill=LIME)
    gap = 26; w = a.width + st.width + b.width + gap * 2; h = max(a.height, b.height)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    im.alpha_composite(a, (0, 0)); im.alpha_composite(st, (a.width + gap, (h - st.height) // 2)); im.alpha_composite(b, (a.width + st.width + gap * 2, 0))
    return im
TAG = tag_img()

# ---------------- escenas
def scene_intro(frame, t, dur):
    a = ease(t / 0.8); out = 1 - clamp((t - (dur - 0.35)) / 0.35)
    sc = 0.75 + 0.25 * ease(t / 0.9)
    m = MARK.resize((int(420 * sc), int(420 * sc)), Image.LANCZOS)
    paste_alpha(frame, m, ((W - m.width) / 2, 560 - m.height / 2 + 60), a * out)
    paste_alpha(frame, WORDMARK, ((W - WORDMARK.width) / 2, 900 + 40 * (1 - ease((t - 0.3) / 0.7))), ease((t - 0.3) / 0.7) * out)
    paste_alpha(frame, TAG, ((W - TAG.width) / 2, 1130), ease((t - 0.7) / 0.6) * out)
    l1 = text_img('LA APP DE TU GIMNASIO,', TITLE_S, grad=CHROME)
    l2 = text_img('CON TU MARCA', TITLE_S, fill=LIME)
    k = ease((t - 1.1) / 0.6) * out
    paste_alpha(frame, l1, ((W - l1.width) / 2, 1330), k)
    paste_alpha(frame, l2, ((W - l2.width) / 2, 1450), k)

PHONES = {}
TITLES = {}
def title_lines(title):
    if title in TITLES: return TITLES[title]
    for f in (TITLE, TITLE_S):
        one = text_img(title, f, grad=CHROME)
        if one.width <= W - 128: TITLES[title] = [one]; return TITLES[title]
    lines = wrap(title, TITLE_S, W - 128)
    TITLES[title] = [text_img(l, TITLE_S, grad=CHROME) for l in lines]
    return TITLES[title]
def scene_use(shot, kicker, title, sub):
    def draw(frame, t, dur):
        out = 1 - clamp((t - (dur - 0.3)) / 0.3)
        header(frame, t)
        k = text_img(kicker, KICK, fill=LIME, tracking=8)
        paste_alpha(frame, k, (64, 268), ease(t / 0.4) * out)
        y = 318
        for ln in title_lines(title):
            paste_alpha(frame, ln, (60 - 40 * (1 - ease(t / 0.5)), y), ease(t / 0.5) * out); y += ln.height + 12
        y += 12
        for ln in wrap(sub, SUB, W - 128):
            paste_alpha(frame, text_img(ln, SUB, fill=LIGHT), (64, y), ease((t - 0.2) / 0.5) * out); y += 56
        if shot not in PHONES: PHONES[shot] = phone(shot)
        p = PHONES[shot]
        py = max(600, y + 30) + 260 * (1 - ease((t - 0.1) / 0.7))
        paste_alpha(frame, p, ((W - p.width) / 2, py), ease((t - 0.1) / 0.5) * out)
    return draw

BENEFITS = [
    'Tu logo y tu nombre en el celular de cada socio',
    'Panel de admin: altas, bajas y actividad',
    'Datos en tu servidor, sin anuncios',
    'En español, con soporte local',
    'Entrenador IA en el plan Pro',
    'App + productos ONIX GYM de Reset Supply',
]
def check_icon(size=58):
    im = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([2, 2, size - 3, size - 3], outline=LIME, width=4)
    d.line([(size * .28, size * .52), (size * .44, size * .67), (size * .73, size * .35)], fill=(255, 255, 255), width=5, joint='curve')
    return im
CHECK = check_icon()

def scene_benefits(frame, t, dur):
    out = 1 - clamp((t - (dur - 0.35)) / 0.35)
    header(frame, t)
    k = text_img('PARA EL DUEÑO DEL GIMNASIO', KICK, fill=LIME, tracking=8)
    paste_alpha(frame, k, (64, 300), ease(t / 0.4) * out)
    l1 = text_img('¿POR QUÉ', TITLE, grad=CHROME); l2 = text_img('RESET GYM?', TITLE, grad=NEON)
    paste_alpha(frame, l1, (60, 350), ease(t / 0.5) * out)
    paste_alpha(frame, l2, (60, 350 + l1.height + 14), ease((t - 0.15) / 0.5) * out)
    y = 720
    for i, b in enumerate(BENEFITS):
        step = max(0.55, (dur - 2.2) / len(BENEFITS))
        a = ease((t - 0.9 - i * step) / 0.45) * out
        dx = 50 * (1 - ease((t - 0.9 - i * step) / 0.45))
        paste_alpha(frame, CHECK, (64 + dx, y), a)
        ly = y + 2
        for ln in wrap(b, BEN, W - 230):
            paste_alpha(frame, text_img(ln, BEN, fill=(255, 255, 255)), (150 + dx, ly), a); ly += 56
        # línea divisoria fina
        if a > 0:
            ImageDraw.Draw(frame).line([(150, max(ly, y + 60) + 26), (W - 64, max(ly, y + 60) + 26)], fill=(40, 40, 44), width=2)
        y = max(ly, y + 60) + 58

def scene_cta(frame, t, dur):
    a = ease(t / 0.6)
    m = MARK.resize((300, 300), Image.LANCZOS)
    paste_alpha(frame, m, ((W - 300) / 2, 400), a)
    paste_alpha(frame, WORDMARK, ((W - WORDMARK.width) / 2, 730), a)
    l1 = text_img('DALE UN RESET', TITLE, grad=CHROME); l2 = text_img('A TU GIMNASIO', TITLE, fill=LIME)
    k = ease((t - 0.4) / 0.5)
    paste_alpha(frame, l1, ((W - l1.width) / 2, 1000), k)
    paste_alpha(frame, l2, ((W - l2.width) / 2, 1000 + l1.height + 16), k)
    # botón
    k2 = ease((t - 0.9) / 0.5)
    btn = Image.new('RGBA', (640, 120), (0, 0, 0, 0))
    bm = Image.new('L', btn.size, 0); ImageDraw.Draw(bm).rounded_rectangle([0, 0, 639, 119], 60, fill=255)
    btn.paste(gradient(640, 120, NEON, vertical=False), (0, 0), bm)
    bt = text_img('PIDE TU DEMO', font('BarlowCondensed-Black', 72), fill=(5, 5, 5))
    btn.alpha_composite(bt, ((640 - bt.width) // 2, (120 - bt.height) // 2))
    paste_alpha(frame, btn, ((W - 640) / 2, 1370), k2)
    s1 = text_img('Escríbenos por DM', SMALL, fill=LIGHT)
    s2 = text_img('resetsupplymx.com  ·  @ResetsupplyMx', SMALL, fill=(255, 255, 255))
    paste_alpha(frame, s1, ((W - s1.width) / 2, 1540), k2)
    paste_alpha(frame, s2, ((W - s2.width) / 2, 1600), k2)
    paste_alpha(frame, TAG, ((W - TAG.width) / 2, 1770), k2)

SCENES = [
    (scene_intro, 3.2),
    (scene_use('login', 'CÓMO SE USA', 'ENTRA CON TU CUENTA', 'Cada socio inicia sesión con el usuario que le da su gimnasio.'), 3.8),
    (scene_use('home', 'CÓMO SE USA', 'TU ENTRENAMIENTO DE HOY', 'Abre la app y ve qué te toca hoy, tu semana y tu peso.'), 3.8),
    (scene_use('workout', 'CÓMO SE USA', 'ENTRENA GUIADO', 'Pesos de la última vez, series y progresión automática.'), 3.8),
    (scene_use('plan', 'CÓMO SE USA', 'TU RUTINA SEMANAL', 'Una rutina por día o por rotación, lista para editar.'), 3.8),
    (scene_use('stats', 'CÓMO SE USA', 'MIRA TU PROGRESO', 'Racha, entrenos, mapa muscular y peso corporal.'), 3.8),
    (scene_use('library', 'CÓMO SE USA', '+5,600 EJERCICIOS', 'Busca por músculo, tipo de entrenamiento o equipo.'), 3.8),
    (scene_benefits, 8.0),
    (scene_cta, 4.5),
]

def apply_durations(path):
    global SCENES
    if path and os.path.exists(path):
        d = json.load(open(path))
        SCENES = [(fn, max(dur, d[i])) for i, (fn, dur) in enumerate(SCENES)]

def main(out):
    total = sum(d for _, d in SCENES)
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-preset', 'medium', '-crf', '19', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    n = 0
    for fn, dur in SCENES:
        for i in range(int(dur * FPS)):
            frame = BGIMG.convert('RGBA')
            fn(frame, i / FPS, dur)
            ff.stdin.write(frame.convert('RGB').tobytes()); n += 1
    ff.stdin.close(); ff.wait()
    print('frames', n, 'seconds', round(total, 1))

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 2 and sys.argv[1] == 'still':
        # vista previa: un cuadro en el segundo indicado
        t0 = float(sys.argv[2]); acc = 0
        for fn, dur in SCENES:
            if t0 < acc + dur:
                fr = BGIMG.convert('RGBA'); fn(fr, t0 - acc, dur); fr.convert('RGB').save(sys.argv[3]); break
            acc += dur
    else:
        apply_durations(sys.argv[2] if len(sys.argv) > 2 else None)
        main(sys.argv[1] if len(sys.argv) > 1 else 'reset-gym.mp4')
        json.dump([d for _, d in SCENES], open(os.path.splitext(sys.argv[1] if len(sys.argv) > 1 else 'reset-gym.mp4')[0] + '.timing.json', 'w'))
