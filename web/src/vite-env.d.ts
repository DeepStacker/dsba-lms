/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly VITE_AI_SERVICE_URL: string
  readonly VITE_DEBUG: string
  readonly VITE_APP_NAME: string
  readonly VITE_GA_ID?: string
  readonly VITE_HOTJAR_ID?: string
  // more env variables...
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
