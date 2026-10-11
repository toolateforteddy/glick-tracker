import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { loadAnalytics } from './lib/analytics'

loadAnalytics(import.meta.env.VITE_GOATCOUNTER_CODE, window.location.search)

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
