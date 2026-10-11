// Optional, cookieless page-view counting via GoatCounter (https://www.goatcounter.com).
// Off unless the build sets VITE_GOATCOUNTER_CODE. GoatCounter's script already skips
// localhost, and visiting the site with `#toggle-goatcounter` stops counting that browser.
export function goatCounterEndpoint(code: string | undefined): string | null {
  const trimmed = code?.trim()
  return trimmed && /^[a-z0-9-]+$/i.test(trimmed) ? `https://${trimmed}.goatcounter.com/count` : null
}

export function loadAnalytics(code: string | undefined, search: string): void {
  const endpoint = goatCounterEndpoint(code)
  // `?demo` previews bundled sample data, so it isn't a real visit.
  if (!endpoint || new URLSearchParams(search).has('demo')) return
  const script = document.createElement('script')
  script.async = true
  script.src = 'https://gc.zgo.at/count.js'
  script.dataset.goatcounter = endpoint
  document.head.appendChild(script)
}
