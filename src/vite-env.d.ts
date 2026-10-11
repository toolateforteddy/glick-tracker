/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_GIST_RAW_URL?: string
  readonly VITE_GOATCOUNTER_CODE?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
