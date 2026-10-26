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
| Ícono | mancuerna | pesas con rayo en degradado cian → lima |
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

## Servidor en Render (cuentas e inicio de sesión)

Las cuentas viven en un servidor, no en la app: el repositorio es público y el APK se puede
abrir, así que ninguna contraseña va en el código. El servidor es el mismo de openGym con
inicio de sesión por usuario y contraseña, sin registro abierto y sin modo invitado.

1. En [render.com](https://render.com): **New → Blueprint** → conecta GitHub y elige este
   repositorio. Render lee `render.yaml` y crea el servicio **reset-gym** (plan Starter con un
   disco de 1 GB en `/data`; el plan gratis no tiene disco y borraría todo en cada reinicio).
2. Render pide el valor de **RESET_ACCOUNTS**. Es una lista JSON con las cuentas iniciales:

   ```json
   [{"name":"Jorge","password":"…"},{"name":"admin","password":"…","admin":true}]
   ```

   Se guarda como secreto en Render y no aparece en ningún otro lado. Cada cuenta se crea la
   primera vez que arranca el servidor; si ya existe, no se toca (un cambio de contraseña hecho
   después se respeta). Para agregar usuarios, súmalos a la lista y reinicia el servicio, o
   genera un código de invitación en el panel de admin para que la persona cree su cuenta.
3. La app usa `https://reset-gym.onrender.com`. Si el servidor cambia de dirección, guarda la
   nueva en GitHub: *Settings → Secrets and variables → Actions → Variables* →
   `RESET_SERVER_URL`, y vuelve a compilar el APK.

El workflow **Reset Gym servidor** compila y arranca la imagen de Render en cada cambio y prueba
el inicio de sesión con cuentas de prueba.

## Licencias (importante)

- **Código:** AGPL-3.0, igual que openGym. Si distribuyes el APK, el código fuente de esa versión
  tiene que estar disponible (este repositorio público lo cumple) y se conserva el crédito a
  openGym y a Duarte Santos (Ajustes, al pie).
- **Animaciones de ejercicios:** son de Gym visual y **no** están bajo la AGPL (ver `NOTICE.md`).
  Un fork **no comercial** puede usar las de 180 px del repositorio con su aviso. Si Reset Gym se
  usa con fines comerciales (por ejemplo, para promocionar Reset Supply), hace falta una licencia
  propia de [gymvisual.com](https://gymvisual.com/).
- **Marca:** "openGym" es el nombre del proyecto original; Reset Gym no lo usa como nombre propio.

## Marca de cada gimnasio (marca blanca)

Cada gimnasio que contrata Reset Gym tiene **su propio servidor en Render**, con sus cuentas y sus
datos separados de los demás. Reset Supply le pone el nombre, el logo y el color del gimnasio con
cuatro variables; al arrancar, el servidor los aplica a la app web (`render/brand.mjs`):

| Variable | Qué es | Ejemplo |
|---|---|---|
| `GYM_NAME` | Nombre del gimnasio: título, pantalla de inicio de sesión, nombre al instalar la app | `Gym Titán` |
| `GYM_SHORT_NAME` | Nombre bajo el ícono del teléfono (12 caracteres o menos). Opcional | `Titán` |
| `GYM_LOGO_URL` | Enlace **https** a un **PNG cuadrado**, mínimo 192 px (ideal 512 px o más, fondo sólido) | `https://…/logo.png` |
| `GYM_COLOR` | Color de botones y acentos, en hex. Opcional | `#ff6a00` |

Con la marca puesta, la persona que abre la página del gimnasio ve su logo y su nombre, y al
instalar la app en el teléfono queda con el ícono y el nombre del gimnasio. La app muestra
"con tecnología de Reset Gym" bajo el nombre. Sin estas variables todo se queda como Reset Gym.

**Alta de un gimnasio nuevo:**

1. Render → **New → Blueprint** → este repositorio. Ponle al servicio un nombre del gimnasio
   (por ejemplo `gym-titan`).
2. Llena `RESET_ACCOUNTS` (cuentas iniciales del gimnasio) y las cuatro variables de marca.
3. Opcional: en el servicio, **Settings → Custom Domains**, agrega el dominio del gimnasio
   (`app.gymtitan.mx`). Hazlo antes de que los socios creen sus passkeys: van atadas al dominio.
4. En **Logs** debe aparecer `Marca: Gym Titán · logo 512×512 · color #ff6a00`. Si el logo no
   sirve (no es PNG, no es cuadrado, es muy chico o el enlace no responde), el log dice por qué y la
   app usa el ícono de Reset Gym; el servidor nunca se detiene por eso.

Para **cambiar el logo**: cambia `GYM_LOGO_URL` y redespliega. Los teléfonos que ya instalaron la
app actualizan el ícono por su cuenta (Android puede tardar unos días; en iPhone hay que reinstalar).

**Invitación a instalar:** al abrir la página aparece una tarjeta "Instalar {gimnasio}". En Android y
en la computadora (Chrome, Edge, Samsung Internet) abre el instalador del navegador; en iPhone
explica *Compartir → Agregar a inicio*. "Más tarde" la oculta 30 días. No aparece si la app ya está
instalada ni dentro del APK.

**APK de Android:** su ícono y su nombre se fijan al compilar, así que el APK sigue siendo Reset Gym.
Para un APK con la marca de un gimnasio hay que compilar una versión aparte con su propio ID.
