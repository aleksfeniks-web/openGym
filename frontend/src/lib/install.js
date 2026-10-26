// Invitación a instalar la app web en la pantalla de inicio (Reset Gym y cada gimnasio con marca
// propia, render/brand.mjs). La decisión de cuándo mostrarla es una función pura con su prueba
// (install.test.js); el resto solo guarda el evento del navegador y lo ofrece a quien lo pida.
//
//   Chrome, Edge y Samsung Internet (Android y computadora) avisan con `beforeinstallprompt`:
//     se guarda y el botón "Instalar" lo dispara. Sin ese evento no hay forma de instalar desde
//     la página, así que no se muestra nada.
//   iPhone y iPad no tienen ese evento ni aviso propio: se explica Compartir → Agregar a inicio.
//   Instalada (pantalla completa) o dentro de la app de Android: nunca se muestra.

const DISMISS_KEY = 'install_dismissed_until'
export const DISMISS_DAYS = 30

/** iPhone, iPad, o un iPad que se presenta como Mac (iPadOS de escritorio). */
export function isIOSDevice(ua = '', maxTouchPoints = 0) {
  return /iPhone|iPad|iPod/.test(ua) || (/Macintosh/.test(ua) && maxTouchPoints > 1)
}

/**
 * Qué ofrecer: 'prompt' (botón de instalar), 'ios' (instrucciones) o null (nada).
 * `dismissedUntil` es la fecha (ms) hasta la que la persona pidió no verlo.
 */
export function installOffer({ mobile = false, standalone = false, ios = false, hasPrompt = false, dismissedUntil = 0, now = Date.now() } = {}) {
  if (mobile || standalone) return null
  if (dismissedUntil && now < dismissedUntil) return null
  if (hasPrompt) return 'prompt'
  if (ios) return 'ios'
  return null
}

export function isStandalone(win = typeof window !== 'undefined' ? window : null) {
  try {
    return !!(win?.matchMedia?.('(display-mode: standalone)').matches || win?.navigator?.standalone === true)
  } catch {
    return false
  }
}

export function readDismissed(storage = globalThis.localStorage) {
  try { return Number(storage?.getItem(DISMISS_KEY)) || 0 } catch { return 0 }
}

export function dismissInstall(storage = globalThis.localStorage, now = Date.now()) {
  try { storage?.setItem(DISMISS_KEY, String(now + DISMISS_DAYS * 864e5)) } catch { /* modo privado */ }
}

// ---- El evento del navegador ----
let deferred = null
const listeners = new Set()
const emit = () => listeners.forEach(fn => fn())

/** Se llama una vez al arrancar: el evento llega temprano, antes de que se pinte cualquier vista. */
export function startInstallCapture(win = window) {
  win.addEventListener('beforeinstallprompt', e => {
    e.preventDefault() // sin esto Chrome muestra su propia barra y el evento ya no sirve después
    deferred = e
    emit()
  })
  win.addEventListener('appinstalled', () => {
    deferred = null
    emit()
  })
}

export const hasInstallPrompt = () => !!deferred
export function onInstallChange(fn) {
  listeners.add(fn)
  return () => listeners.delete(fn)
}

/** Abre el diálogo de instalación del navegador. Devuelve true si la persona aceptó. */
export async function promptInstall() {
  const e = deferred
  if (!e) return false
  deferred = null // un evento solo se puede usar una vez
  emit()
  e.prompt()
  try {
    const choice = await e.userChoice
    return choice?.outcome === 'accepted'
  } catch {
    return false
  }
}
