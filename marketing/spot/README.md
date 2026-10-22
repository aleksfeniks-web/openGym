# Spot de Reset Gym (9:16)

Spot vertical de 33 s para Reels, TikTok e historias, al estilo "motion" de las marcas de apps:
teléfono en 3D sobre un resplandor lima, texto que entra palabra por palabra, tarjetas
flotantes, notificación con sonido y cierre con el logo.

- `visual.mp4`: la animación (1080×1920, 30 fps), hecha con HTML/CSS y capturada cuadro por cuadro.
- `fondo.flac`: música y efectos, sintetizados para este spot (sin samples de terceros).
- `voz.json`: lo que dice la voz y en qué segundo. Cambia los textos aquí.
- `narrar.py`: genera la voz con Piper (gratis) o con ElevenLabs.

El workflow **Reset Gym spot** arma el MP4 final con voz, música y efectos y lo publica en el
Release `spot`.

## Voz con ElevenLabs

En GitHub → Settings → Secrets and variables → Actions:
- Secreto `ELEVENLABS_API_KEY`: tu clave de ElevenLabs.
- Variable `ELEVENLABS_VOICE_ID`: el id de la voz (en ElevenLabs → Voices → la voz → "ID").

Con las dos, el workflow también publica la versión con ElevenLabs.
