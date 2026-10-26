#!/usr/bin/env node
// Marca del gimnasio por servidor (marca blanca).
//
// Cada gimnasio que contrata Reset Gym tiene su propio servicio en Render. Reset Supply le pone su
// nombre, su logo y su color con variables de entorno, y este script los aplica a la app web al
// arrancar, antes de que nginx empiece a servirla:
//
//   GYM_NAME        Nombre del gimnasio ("Gym Titán"). Sin él, la app se queda como Reset Gym.
//   GYM_SHORT_NAME  Nombre corto bajo el ícono del teléfono (12 caracteres o menos). Opcional.
//   GYM_LOGO_URL    URL https de un PNG cuadrado, mínimo 192 px (ideal 512 px o más). Opcional.
//   GYM_COLOR       Color de acento en hex ("#ff6a00"). Opcional.
//
// Lo que cambia: el manifiesto (nombre e ícono al instalar la app en el teléfono), el título y el
// ícono de la página, y window.__GYM__, que la app lee para mostrar nombre y logo por dentro.
// Un logo que no se puede descargar o no sirve no detiene el servidor: se avisa en el log y se usa
// la última copia buena guardada en el disco (DATA_DIR/brand), o el ícono de Reset Gym.
//
// Sin dependencias: Node 22 trae fetch, y del PNG solo se lee la cabecera para saber su tamaño.

import { createHash } from 'node:crypto'
import { copyFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { pathToFileURL } from 'node:url'

const MAX_BYTES = 3 * 1024 * 1024
const MIN_SIDE = 192
const PNG_SIG = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a])

/** Ancho y alto de un PNG, o null si no es un PNG válido. */
export function pngSize(buf) {
  if (!Buffer.isBuffer(buf) || buf.length < 24 || !buf.subarray(0, 8).equals(PNG_SIG)) return null
  if (buf.toString('latin1', 12, 16) !== 'IHDR') return null
  return { width: buf.readUInt32BE(16), height: buf.readUInt32BE(20) }
}

/** Por qué un logo no sirve, o null si sirve. */
export function logoProblem(size) {
  if (!size) return 'no es un PNG'
  const { width, height } = size
  if (Math.abs(width - height) > Math.max(width, height) * 0.02) return `no es cuadrado (${width}×${height})`
  if (Math.min(width, height) < MIN_SIDE) return `es muy chico (${width}×${height}; mínimo ${MIN_SIDE}×${MIN_SIDE})`
  return null
}

/** Lee y limpia las variables. Devuelve null si no hay marca de gimnasio. */
export function readBrand(env) {
  const clean = v => (typeof v === 'string' ? v.trim().replace(/^(['"])(.*)\1$/, '$2').trim() : '')
  const name = clean(env.GYM_NAME).slice(0, 45)
  const color = /^#[0-9a-f]{6}$/i.test(clean(env.GYM_COLOR)) ? clean(env.GYM_COLOR).toLowerCase() : ''
  const logoUrl = clean(env.GYM_LOGO_URL)
  if (!name && !color && !logoUrl) return null
  const shortName = (clean(env.GYM_SHORT_NAME) || name).slice(0, 12).trim()
  return { name, shortName, color, logoUrl }
}

/** El manifiesto con la marca del gimnasio. */
export function brandManifest(manifest, brand, logo) {
  const m = { ...manifest }
  if (brand.name) {
    m.name = brand.name
    m.short_name = brand.shortName || brand.name
    m.description = `${brand.name} · tus entrenamientos y tu progreso`
  }
  if (logo) {
    // Un solo PNG grande: los navegadores lo escalan al tamaño que necesitan. "any" y no
    // "maskable": un logo normal no deja el margen de seguridad que Android recorta.
    m.icons = [{ src: logo.file, sizes: `${logo.width}x${logo.height}`, type: 'image/png', purpose: 'any' }]
  }
  return m
}

const escapeHtml = s => s.replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c])

/** El index.html con título, ícono, color y window.__GYM__ del gimnasio. */
export function brandHtml(html, brand, logo) {
  let out = html
  const gym = { name: brand.name || null, logo: logo ? logo.file : null, color: brand.color || null }
  // JSON dentro de <script>: "<" escapado para que un nombre nunca pueda cerrar la etiqueta.
  const json = JSON.stringify(gym).replace(/</g, '\\u003c')
  let head = `<script>window.__GYM__=${json}</script>`
  // :root:root:root gana a los :root (y al tema claro) de la hoja de estilos, aunque esta cargue después.
  if (brand.color) head += `<style>:root:root:root{--brand-lime:${brand.color};--brand-cyan:${brand.color}}</style>`
  if (brand.name) {
    out = out.replace(/<title>[^<]*<\/title>/, `<title>${escapeHtml(brand.name)}</title>`)
    out = out.replace(/(<meta name="apple-mobile-web-app-title" content=")[^"]*(")/, `$1${escapeHtml(brand.shortName || brand.name)}$2`)
  }
  if (brand.name) out = out.replace(/(<meta name="description" content=")[^"]*(")/, `$1${escapeHtml(brand.name)} · tus entrenamientos y tu progreso$2`)
  if (logo) {
    out = out.replace(/(<link rel="apple-touch-icon" href=")[^"]*(")/, `$1${logo.file}$2`)
    out = out.replace(/(<link rel="icon" type="image\/png" href=")[^"]*(")/, `$1${logo.file}$2`)
  }
  // Antes de cualquier otro <script>: la app lee window.__GYM__ al cargar sus módulos.
  return out.includes('</title>') ? out.replace('</title>', `</title>\n${head}`) : out.replace('<head>', `<head>\n${head}`)
}

async function download(url) {
  if (!/^https:\/\//i.test(url)) throw new Error('la URL del logo debe empezar con https://')
  const ctl = new AbortController()
  const timer = setTimeout(() => ctl.abort(), 15_000)
  try {
    const res = await fetch(url, { signal: ctl.signal, redirect: 'follow' })
    if (!res.ok) throw new Error(`respuesta ${res.status}`)
    const len = Number(res.headers.get('content-length') || 0)
    if (len > MAX_BYTES) throw new Error('pesa más de 3 MB')
    const buf = Buffer.from(await res.arrayBuffer())
    if (buf.length > MAX_BYTES) throw new Error('pesa más de 3 MB')
    return buf
  } finally {
    clearTimeout(timer)
  }
}

export async function applyBrand({ env = process.env, htmlDir, dataDir, log = console.log }) {
  const brand = readBrand(env)
  const indexPath = join(htmlDir, 'index.html')
  const manifestPath = join(htmlDir, 'manifest.json')
  // Siempre se parte del original de la imagen, así un reinicio no aplica la marca dos veces.
  for (const p of [indexPath, manifestPath]) if (!existsSync(p + '.orig')) copyFileSync(p, p + '.orig')
  const html = readFileSync(indexPath + '.orig', 'utf8')
  const manifest = JSON.parse(readFileSync(manifestPath + '.orig', 'utf8'))
  if (!brand) {
    writeFileSync(indexPath, html)
    writeFileSync(manifestPath, JSON.stringify(manifest, null, 2))
    log('Marca: Reset Gym (sin GYM_NAME / GYM_LOGO_URL / GYM_COLOR)')
    return null
  }

  let logo = null
  if (brand.logoUrl) {
    const cacheDir = join(dataDir, 'brand')
    const cached = join(cacheDir, 'logo.png')
    let buf = null
    try {
      buf = await download(brand.logoUrl)
      const problem = logoProblem(pngSize(buf))
      if (problem) throw new Error(`el logo ${problem}`)
      mkdirSync(cacheDir, { recursive: true })
      writeFileSync(cached, buf)
    } catch (e) {
      log(`Marca: no se pudo usar GYM_LOGO_URL (${e.message}).${existsSync(cached) ? ' Uso la última copia guardada.' : ' Uso el ícono de Reset Gym.'}`)
      buf = existsSync(cached) ? readFileSync(cached) : null
    }
    const size = buf && pngSize(buf)
    if (buf && size && !logoProblem(size)) {
      // El nombre lleva el hash: un logo nuevo es un archivo nuevo y ningún caché sirve el viejo.
      const file = `gym-logo-${createHash('sha256').update(buf).digest('hex').slice(0, 10)}.png`
      writeFileSync(join(htmlDir, file), buf)
      logo = { file, ...size }
    }
  }

  writeFileSync(manifestPath, JSON.stringify(brandManifest(manifest, brand, logo), null, 2))
  writeFileSync(indexPath, brandHtml(html, brand, logo))
  log(`Marca: ${brand.name || 'Reset Gym'}${logo ? ` · logo ${logo.width}×${logo.height}` : ''}${brand.color ? ` · color ${brand.color}` : ''}`)
  return { brand, logo }
}

if (import.meta.url === pathToFileURL(process.argv[1] || '').href) {
  applyBrand({ htmlDir: process.env.HTML_DIR || '/usr/share/nginx/html', dataDir: process.env.DATA_DIR || '/data' }).catch(e => {
    // La marca nunca tumba el servidor: en el peor caso se ve como Reset Gym.
    console.error('Marca: error inesperado, se queda Reset Gym:', e.message)
  })
}
