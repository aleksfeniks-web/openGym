// Invitación a instalar la app (con el nombre y logo del gimnasio de este servidor, lib/brand.js).
// Cuándo aparece lo decide lib/install.js; aquí solo se dibuja.
import { useEffect, useState } from 'react'
import { APP_LOGO, APP_NAME } from '../lib/brand.js'
import { t } from '../lib/i18n.js'
import { dismissInstall, hasInstallPrompt, installOffer, isIOSDevice, isStandalone, onInstallChange, promptInstall, readDismissed } from '../lib/install.js'
import { MOBILE } from '../lib/mobile.js'

const IOS = typeof navigator !== 'undefined' && isIOSDevice(navigator.userAgent, navigator.maxTouchPoints || 0)

export default function InstallBanner() {
  const [, rerender] = useState(0)
  const [dismissedUntil, setDismissedUntil] = useState(() => readDismissed())
  useEffect(() => onInstallChange(() => rerender(n => n + 1)), [])

  const offer = installOffer({ mobile: MOBILE, standalone: isStandalone(), ios: IOS, hasPrompt: hasInstallPrompt(), dismissedUntil })
  if (!offer) return null

  const later = () => {
    dismissInstall()
    setDismissedUntil(readDismissed())
  }

  return (
    <div className="install-banner" role="dialog" aria-label={t('Install {0}', APP_NAME)}>
      <img src={APP_LOGO} alt="" width="44" height="44" />
      <div className="install-txt">
        <b>{t('Install {0}', APP_NAME)}</b>
        <span>{offer === 'ios' ? t('In Safari: Share → Add to Home Screen') : t('Open it from your home screen, full screen like an app.')}</span>
      </div>
      <div className="install-acts">
        {offer === 'prompt' && (
          <button type="button" className="btn primary sm" onClick={async () => { if (!(await promptInstall())) later() }}>
            {t('Install')}
          </button>
        )}
        <button type="button" className="btn plain sm" onClick={later}>{t('Later')}</button>
      </div>
    </div>
  )
}
