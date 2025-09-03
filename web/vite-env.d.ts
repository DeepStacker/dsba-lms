/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly VITE_AI_URL: string
  readonly VITE_ENVIRONMENT: string
  // more env variables...
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}