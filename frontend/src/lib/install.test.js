import { describe, expect, it, vi } from 'vitest'
import { DISMISS_DAYS, dismissInstall, installOffer, isIOSDevice, readDismissed, startInstallCapture, hasInstallPrompt, promptInstall } from './install.js'

describe('installOffer', () => {
  const now = Date.UTC(2026, 9, 25)
  it('ofrece el botón cuando el navegador dio el evento', () => {
    expect(installOffer({ hasPrompt: true, now })).toBe('prompt')
  })
  it('en iPhone/iPad explica Compartir → Agregar a inicio', () => {
    expect(installOffer({ ios: true, now })).toBe('ios')
  })
  it('sin evento y sin iOS no hay nada que ofrecer', () => {
    expect(installOffer({ now })).toBe(null)
  })
  it('nunca dentro de la app de Android ni ya instalada', () => {
    expect(installOffer({ mobile: true, hasPrompt: true, now })).toBe(null)
    expect(installOffer({ standalone: true, ios: true, now })).toBe(null)
  })
  it('respeta el "Más tarde" hasta que vence', () => {
    expect(installOffer({ hasPrompt: true, dismissedUntil: now + 1000, now })).toBe(null)
    expect(installOffer({ hasPrompt: true, dismissedUntil: now - 1000, now })).toBe('prompt')
  })
})

describe('isIOSDevice', () => {
  it('reconoce iPhone y el iPad que se presenta como Mac', () => {
    expect(isIOSDevice('Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X)')).toBe(true)
    expect(isIOSDevice('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)', 5)).toBe(true)
    expect(isIOSDevice('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)', 0)).toBe(false)
    expect(isIOSDevice('Mozilla/5.0 (Linux; Android 14)')).toBe(false)
  })
})

describe('"Más tarde"', () => {
  it('guarda la fecha y la lee de vuelta; sin almacenamiento no truena', () => {
    const mem = new Map()
    const storage = { getItem: k => mem.get(k) ?? null, setItem: (k, v) => mem.set(k, v) }
    dismissInstall(storage, 1000)
    expect(readDismissed(storage)).toBe(1000 + DISMISS_DAYS * 864e5)
    const broken = { getItem: () => { throw new Error('privado') }, setItem: () => { throw new Error('privado') } }
    expect(() => dismissInstall(broken)).not.toThrow()
    expect(readDismissed(broken)).toBe(0)
  })
})

describe('evento beforeinstallprompt', () => {
  it('se guarda, evita la barra propia del navegador y se usa una sola vez', async () => {
    const handlers = {}
    const win = { addEventListener: (type, fn) => { handlers[type] = fn } }
    startInstallCapture(win)
    const ev = { preventDefault: vi.fn(), prompt: vi.fn(), userChoice: Promise.resolve({ outcome: 'accepted' }) }
    handlers.beforeinstallprompt(ev)
    expect(ev.preventDefault).toHaveBeenCalled()
    expect(hasInstallPrompt()).toBe(true)
    expect(await promptInstall()).toBe(true)
    expect(ev.prompt).toHaveBeenCalledOnce()
    expect(hasInstallPrompt()).toBe(false)
    expect(await promptInstall()).toBe(false)
  })
})
