// Pruebas de la marca por gimnasio: node --test render/brand.test.mjs
import assert from 'node:assert/strict'
import { mkdtempSync, readFileSync, writeFileSync, readdirSync, existsSync } from 'node:fs'
import { createServer } from 'node:http'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { deflateSync } from 'node:zlib'
import { test } from 'node:test'
import { applyBrand, brandHtml, logoProblem, pngSize, readBrand } from './brand.mjs'

// PNG mínimo válido (cabecera + IHDR + IDAT vacío + IEND) del tamaño pedido; para el tamaño basta la cabecera.
function png(w, h) {
  const crcTable = Array.from({ length: 256 }, (_, n) => { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; return c >>> 0 })
  const crc = b => { let c = 0xffffffff; for (const x of b) c = crcTable[(c ^ x) & 0xff] ^ (c >>> 8); return (c ^ 0xffffffff) >>> 0 }
  const chunk = (type, data) => { const len = Buffer.alloc(4); len.writeUInt32BE(data.length); const td = Buffer.concat([Buffer.from(type), data]); const c = Buffer.alloc(4); c.writeUInt32BE(crc(td)); return Buffer.concat([len, td, c]) }
  const ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(w, 0); ihdr.writeUInt32BE(h, 4); ihdr[8] = 8; ihdr[9] = 6
  return Buffer.concat([Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]), chunk('IHDR', ihdr), chunk('IDAT', deflateSync(Buffer.alloc(0))), chunk('IEND', Buffer.alloc(0))])
}

const HTML = `<!DOCTYPE html><html><head><title>Reset Gym</title>
<meta name="description" content="Reset Gym by Reset Supply">
<meta name="apple-mobile-web-app-title" content="Reset Gym">
<link rel="manifest" href="manifest.json" crossorigin="use-credentials">
<link rel="apple-touch-icon" href="icon-180.png">
<link rel="icon" type="image/png" href="icon-180.png">
<script type="module" src="/assets/index.js"></script></head><body></body></html>`
const MANIFEST = { name: 'Reset Gym', short_name: 'Reset Gym', icons: [{ src: 'icon-512.png', sizes: '512x512' }] }

function site() {
  const dir = mkdtempSync(join(tmpdir(), 'brand-'))
  writeFileSync(join(dir, 'index.html'), HTML)
  writeFileSync(join(dir, 'manifest.json'), JSON.stringify(MANIFEST))
  return { htmlDir: dir, dataDir: mkdtempSync(join(tmpdir(), 'data-')) }
}

test('tamaño del PNG y validación del logo', () => {
  assert.deepEqual(pngSize(png(512, 512)), { width: 512, height: 512 })
  assert.equal(pngSize(Buffer.from('GIF89a......................')), null)
  assert.equal(logoProblem({ width: 512, height: 512 }), null)
  assert.match(logoProblem({ width: 600, height: 300 }), /cuadrado/)
  assert.match(logoProblem({ width: 100, height: 100 }), /chico/)
  assert.match(logoProblem(null), /PNG/)
})

test('variables: limpia comillas, valida el color y acorta el nombre corto', () => {
  assert.equal(readBrand({}), null)
  const b = readBrand({ GYM_NAME: ' "Gym Titán Rosarito" ', GYM_COLOR: '#FF6A00', GYM_LOGO_URL: 'https://x/l.png' })
  assert.deepEqual(b, { name: 'Gym Titán Rosarito', shortName: 'Gym Titán Ro', color: '#ff6a00', logoUrl: 'https://x/l.png' })
  assert.equal(readBrand({ GYM_NAME: 'X', GYM_COLOR: 'rojo' }).color, '')
})

test('el nombre no puede inyectar HTML ni cerrar el <script>', () => {
  const out = brandHtml(HTML, { name: '</script><img onerror=x>', shortName: 'x', color: '' }, null)
  assert.ok(!out.includes('</script><img'))
  assert.ok(out.includes('<title>&lt;/script&gt;&lt;img onerror=x&gt;</title>'))
  assert.ok(out.includes('\\u003c/script>'))
})

test('sin variables se queda Reset Gym', async () => {
  const s = site()
  assert.equal(await applyBrand({ env: {}, ...s, log: () => {} }), null)
  assert.match(readFileSync(join(s.htmlDir, 'index.html'), 'utf8'), /<title>Reset Gym<\/title>/)
})

test('aplica nombre, logo y color; un reinicio parte del original; un logo caído usa la copia guardada', async () => {
  const good = png(1024, 1024)
  let serve = good
  const srv = createServer((req, res) => {
    if (!serve) { res.writeHead(500); return res.end() }
    res.writeHead(200, { 'content-type': 'image/png' }); res.end(serve)
  })
  await new Promise(r => srv.listen(0, '127.0.0.1', r))
  // fetch exige https en producción; para la prueba se usa un servidor local con un proxy mínimo.
  const url = `http://127.0.0.1:${srv.address().port}/logo.png`
  const s = site()
  const env = { GYM_NAME: 'Gym Titán', GYM_COLOR: '#ff6a00', GYM_LOGO_URL: url }
  const realFetch = globalThis.fetch
  const httpsOk = (u, o) => realFetch(u.replace(/^https:/, 'http:'), o)
  globalThis.fetch = httpsOk
  try {
    env.GYM_LOGO_URL = url.replace(/^http:/, 'https:')
    const r = await applyBrand({ env, ...s, log: () => {} })
    assert.equal(r.logo.width, 1024)
    const html = readFileSync(join(s.htmlDir, 'index.html'), 'utf8')
    const manifest = JSON.parse(readFileSync(join(s.htmlDir, 'manifest.json'), 'utf8'))
    assert.match(html, /<title>Gym Titán<\/title>/)
    assert.match(html, /window\.__GYM__=\{"name":"Gym Titán","logo":"gym-logo-[a-f0-9]{10}\.png","color":"#ff6a00"\}/)
    assert.match(html, /:root:root:root\{--brand-lime:#ff6a00;--brand-cyan:#ff6a00\}/)
    assert.match(html, /apple-touch-icon" href="gym-logo-/)
    assert.ok(html.indexOf('window.__GYM__') < html.indexOf('/assets/index.js'), 'la marca va antes del bundle')
    assert.equal(manifest.name, 'Gym Titán')
    assert.equal(manifest.short_name, 'Gym Titán')
    assert.deepEqual(manifest.icons, [{ src: r.logo.file, sizes: '1024x1024', type: 'image/png', purpose: 'any' }])
    assert.ok(readdirSync(s.htmlDir).includes(r.logo.file))

    // Reinicio con el logo caído: se aplica una sola vez y se usa la copia del disco.
    serve = null
    const r2 = await applyBrand({ env, ...s, log: () => {} })
    assert.equal(r2.logo.file, r.logo.file)
    const html2 = readFileSync(join(s.htmlDir, 'index.html'), 'utf8')
    assert.equal(html2.split('window.__GYM__').length, 2)

    // Un logo que no sirve (no cuadrado) en un servidor nuevo: sin logo, pero con nombre.
    serve = png(800, 400)
    const s3 = site()
    const r3 = await applyBrand({ env, ...s3, log: () => {} })
    assert.equal(r3.logo, null)
    assert.match(readFileSync(join(s3.htmlDir, 'index.html'), 'utf8'), /<title>Gym Titán<\/title>/)
    assert.ok(!existsSync(join(s3.dataDir, 'brand', 'logo.png')))
  } finally {
    globalThis.fetch = realFetch
    srv.close()
  }
})

test('rechaza URLs que no son https', async () => {
  const s = site()
  const r = await applyBrand({ env: { GYM_NAME: 'X', GYM_LOGO_URL: 'http://inseguro/logo.png' }, ...s, log: () => {} })
  assert.equal(r.logo, null)
})
