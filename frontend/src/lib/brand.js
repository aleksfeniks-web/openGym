// Reset Gym — la versión de openGym con la marca de Reset Supply.
//
// Todo lo que el usuario lee con el nombre de la app pasa por aquí. Las claves de traducción
// siguen diciendo "openGym" (son el texto fuente en inglés y las comparten los 19 idiomas), así
// que t() cambia el nombre al mostrarlo en lugar de reescribir cada paquete de idioma.
//
// Basado en openGym de Duarte Santos (https://github.com/DuarteSantos8/openGym), AGPL-3.0.

// Marca blanca: el servidor de cada gimnasio escribe window.__GYM__ en index.html al arrancar
// (render/brand.mjs) con el nombre, el logo y el color que Reset Supply le configuró. Sin eso
// (la app de Android, el servidor propio de Reset Gym, las pruebas) todo queda como Reset Gym.
const readGym = () => {
  try {
    const g = typeof window !== 'undefined' ? window.__GYM__ : null
    if (!g || typeof g !== 'object') return null
    const name = typeof g.name === 'string' && g.name.trim() ? g.name.trim().slice(0, 45) : null
    const logo = typeof g.logo === 'string' && /^gym-logo-[a-f0-9]{10}\.png$/.test(g.logo) ? g.logo : null
    return name || logo ? { name, logo } : null
  } catch { return null }
}

export const PLATFORM_NAME = 'Reset Gym'
export const BRAND = 'Reset Supply'
export const BRAND_SITE = 'resetsupplymx.com'
/** La marca del gimnasio de este servidor, o null si es Reset Gym tal cual. */
export const GYM = import.meta.env?.MODE === 'test' ? null : readGym()
export const APP_NAME = GYM?.name || PLATFORM_NAME
/** Logo que se muestra en el inicio de sesión y en el aviso de instalar. */
export const APP_LOGO = GYM?.logo || 'icon-180.png'
/** Bajo el logo: el lema de Reset Supply, o "con tecnología de Reset Gym" en un gimnasio con marca propia. */
export const BRAND_TAGLINE = GYM ? `con tecnología de ${PLATFORM_NAME}` : 'Professional ★ Gym Care'

// El repositorio de GitHub de este fork, "usuario/repo". Lo pone el workflow de GitHub Actions
// al compilar (VITE_APP_REPO = github.repository). Sin él no se buscan actualizaciones, así que
// la app nunca ofrece instalar un APK de openGym encima de Reset Gym.
// Las pruebas de openGym (vitest) siguen describiendo openGym: ahí el nombre y el repositorio se
// quedan como en el original, para que esas pruebas sigan avisando de fallos reales.
const TEST = import.meta.env?.MODE === 'test'

export const UPSTREAM_REPO = 'DuarteSantos8/openGym'
export const APP_REPO = TEST ? UPSTREAM_REPO : (import.meta.env?.VITE_APP_REPO || '').trim()
// Reset Gym arranca en español, con los nombres de los ejercicios en inglés (el resto de cada
// ejercicio, instrucciones y descripción, en español). Se puede cambiar en Ajustes.
export const BRAND_LANG = TEST ? null : 'es'

// El servidor de Reset Gym (Render). Con él, la app de Android abre en una pantalla de inicio de
// sesión con usuario y contraseña en lugar de preguntar si usarla solo en el teléfono. Lo pone el
// workflow desde la variable del repositorio RESET_SERVER_URL; sin ella la app funciona como openGym.
const cleanOrigin = raw => { try { return raw ? new URL(/^https?:\/\//i.test(raw) ? raw : 'https://' + raw).origin : '' } catch { return '' } }
export const RESET_SERVER = TEST ? '' : cleanOrigin((import.meta.env?.VITE_RESET_SERVER || '').trim())

export const SOURCE_URL = 'https://github.com/' + (APP_REPO || UPSTREAM_REPO)

// "Documents/openGym" es una carpeta real del teléfono (la copia de seguridad automática la
// crea con ese nombre), así que se queda tal cual; el resto de menciones cambian de nombre.
const UPSTREAM_NAME = /(?<!Documents\/)openGym/g

/** El texto con el nombre de la app cambiado a Reset Gym. */
export const brandText = s => (!TEST && typeof s === 'string' && s.includes('openGym') ? s.replace(UPSTREAM_NAME, APP_NAME) : s)
