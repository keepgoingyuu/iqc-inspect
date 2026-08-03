import { defineConfig } from '@hey-api/openapi-ts'

// 後端 Pydantic model → TypeScript client:後端 API 有變動時執行 pnpm generate-client
export default defineConfig({
  input: 'http://localhost:8000/openapi.json',
  output: 'src/client',
})
