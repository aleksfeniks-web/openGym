# Reset Gym

Versión para Android de [openGym](https://github.com/DuarteSantos8/openGym) con la marca de
**Reset Supply** (Rosarito, Baja California). Mismo código y mismas funciones; cambian el nombre,
el ID de la app, los colores, el ícono y el idioma por defecto.

## Qué cambia respecto a openGym

| | openGym | Reset Gym |
|---|---|---|
| Nombre | openGym | Reset Gym |
| ID de Android | `ch.duartesantos.opengym` | `mx.resetsupply.resetgym` |
| Fondo | `#0c0e12` | negro de marca `#0a0a0a` |
| Acento | verde iOS `#30d158` | verde lima `#8ee000` (y cian `#1eb8f0` como opción "Azul") |
| Ícono | mancuerna | gota con rayo en degradado cian → lima (**provisional**) |
| Idioma | el del teléfono | español, con nombres de ejercicios en inglés |
| Actualizaciones | Releases de openGym | Releases de este repositorio |

Como el ID es distinto, Reset Gym y openGym pueden convivir en el mismo teléfono.

Archivos principales: `frontend/src/lib/brand.js` (nombre, repositorio, idioma),
`frontend/src/index.css` (colores), `frontend/capacitor.config.json` y
`frontend/android/app/src/main/res/` (nombre, ícono y pantalla de inicio de Android).

## Compilar el APK

Lo hace GitHub Actions (`.github/workflows/reset-gym-apk.yml`):

1. En el repositorio: **Actions** → habilita los workflows si GitHub lo pide.
2. **Reset Gym APK** → **Run workflow**. En ~15 minutos el APK aparece en el run, en *Artifacts*.
3. Sin clave de firma sale un APK de prueba llamado "Reset Gym Test". Para versiones reales,
   crea una clave una sola vez y guárdala en *Settings → Secrets and variables → Actions*
   (`RESET_KEYSTORE_B64`, `RESET_KEYSTORE_PASSWORD`, `RESET_KEY_ALIAS`):

   ```bash
   keytool -genkeypair -v -keystore reset-gym.jks -alias resetgym -keyalg RSA -keysize 4096 -validity 10000
   base64 -w0 reset-gym.jks   # esto va en RESET_KEYSTORE_B64
   ```

   Guarda `reset-gym.jks` en un lugar seguro: sin ella ningún teléfono podrá actualizar la app.
4. Para publicar una versión: sube `version` en `frontend/package.json`, sube `versionCode` y
   `versionName` en `frontend/android/app/build.gradle`, y crea la etiqueta `vX.Y.Z` con el mismo
   número. El workflow publica el Release con el APK y su `.sha256`, y la app lo ofrece en
   Ajustes → Buscar actualizaciones.

## Licencias (importante)

- **Código:** AGPL-3.0, igual que openGym. Si distribuyes el APK, el código fuente de esa versión
  tiene que estar disponible (este repositorio público lo cumple) y se conserva el crédito a
  openGym y a Duarte Santos (Ajustes, al pie).
- **Animaciones de ejercicios:** son de Gym visual y **no** están bajo la AGPL (ver `NOTICE.md`).
  Un fork **no comercial** puede usar las de 180 px del repositorio con su aviso. Si Reset Gym se
  usa con fines comerciales (por ejemplo, para promocionar Reset Supply), hace falta una licencia
  propia de [gymvisual.com](https://gymvisual.com/).
- **Marca:** "openGym" es el nombre del proyecto original; Reset Gym no lo usa como nombre propio.
