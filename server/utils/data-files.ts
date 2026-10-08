import { existsSync, readFileSync, renameSync, writeFileSync } from 'node:fs'
import { resolve } from 'node:path'

const dataFile = (name: string) => resolve(process.cwd(), 'data', name)
export function readJson<T>(name: string, fallback: T): T {
  try { return JSON.parse(readFileSync(dataFile(name), 'utf8')) as T } catch { return fallback }
}
export function writeJson(name: string, value: unknown) {
  const f = dataFile(name)
  writeFileSync(f + '.tmp', JSON.stringify(value, null, 2) + '\n')
  renameSync(f + '.tmp', f) // atomic
}

/** Routes to prerender at build time. */
export function addRoutes(routes: string[]) {
  const set = new Set(readJson<string[]>('routes.json', []))
  routes.forEach((r) => set.add(r)); writeJson('routes.json', [...set].sort())
}
export function removeRoutes(routes: string[]) {
  const set = new Set(readJson<string[]>('routes.json', []))
  routes.forEach((r) => set.delete(r)); writeJson('routes.json', [...set].sort())
}
/** Old address → new address, applied as 301 redirects by the build (see nuxt.config.ts). */
export function addRedirect(from: string, to: string) {
  const list = readJson<{ from: string; to: string }[]>('redirects.json', []).filter((r) => r.from !== from && r.from !== to)
  // flatten chains: anything that pointed to `from` now points to `to`
  list.forEach((r) => { if (r.to === from) r.to = to })
  list.push({ from, to })
  writeJson('redirects.json', list)
}
export { existsSync }
