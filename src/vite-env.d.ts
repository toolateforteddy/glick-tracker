/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_GIST_RAW_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
