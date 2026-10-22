# Video de Reset Gym (9:16)

Video vertical de 1080×1920 para Reels, TikTok e historias: cómo se usa la app y qué gana el
gimnasio. Las pantallas son capturas reales de la app con datos de ejemplo; las animaciones de
ejercicios están ocultas porque su licencia (Gym visual) no permite usarlas en publicidad.

- `render.py` dibuja el video (Pillow + ffmpeg). `narracion.json` es el texto de cada escena.
- `voz.py` narra cada escena con [Piper](https://github.com/rhasspy/piper) (voces en español de México).
- El workflow **Reset Gym video** lo arma todo y publica los MP4 en el Release `video`.

Para cambiar un texto de la narración, edita `narracion.json` y vuelve a correr el workflow.
Tipografía: Barlow y Barlow Condensed (SIL Open Font License, `fonts/OFL.txt`).
