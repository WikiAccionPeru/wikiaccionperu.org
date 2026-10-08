import { existsSync } from 'node:fs'
import { resolve, sep } from 'node:path'
import type { H3Event } from 'h3'

export const defaultContentDir = () => resolve(process.cwd(), 'content')
// A path segment may not start with a dot, nor contain separators, control chars or shell/URL metacharacters.
const SEGMENT = /^(?!\.)[^/\\<>:"|?*\u0000-\u001f]{1,240}$/
const err = (statusCode: number, statusMessage: string) => Object.assign(new Error(statusMessage), { statusCode, statusMessage })
const fail = (code: number, msg: string): never => { throw (globalThis as any).createError ? (globalThis as any).createError({ statusCode: code, statusMessage: msg }) : err(code, msg) }

/** Maps a site path (/foo/bar, or /) to its Markdown file under content/. Throws 400 on anything unsafe. */
export function contentFileFor(routePath: unknown, base = defaultContentDir()): { file: string; exists: boolean; route: string } {
  if (typeof routePath !== 'string' || !routePath.startsWith('/') || routePath.length > 1000) fail(400, 'Bad path')
  const parts = (routePath as string).split('/').filter(Boolean)
  if (!parts.every((p) => SEGMENT.test(p) && !/%(2e|2f|5c|00)/i.test(p))) fail(400, 'Bad path')
  const candidates = parts.length ? [resolve(base, ...parts) + '.md', resolve(base, ...parts, 'index.md')] : [resolve(base, 'index.md')]
  for (const c of candidates) if (!c.startsWith(base + sep)) fail(400, 'Bad path')
  const file = candidates.find((c) => existsSync(c)) ?? candidates[0]
  return { file, exists: existsSync(file), route: '/' + parts.join('/') }
}

/** Mutating requests must come from this site (the session cookie is SameSite=Lax, this is the second layer). */
export function assertSameOrigin(event: H3Event) {
  const origin = getRequestHeader(event, 'origin')
  const host = getRequestHeader(event, 'host')
  let ok = false
  try { ok = !!origin && !!host && new URL(origin).host === host } catch { ok = false }
  if (!ok) throw createError({ statusCode: 403, statusMessage: 'Cross-site request refused' })
}
