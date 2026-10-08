import { readFileSync, statSync } from 'node:fs'
import { resolve } from 'node:path'
import type { H3Event } from 'h3'
import type { AuthUser } from './session'

type Admin = { username: string; id?: string }
type AdminFile = { relyOnUsername: boolean; admins: Admin[] }
let cache: { path: string; mtime: number; file: AdminFile } | undefined

// MediaWiki forbids  # < > [ ] | { } /  (and we also refuse : @ and control chars) in usernames; max 85 bytes
const VALID_NAME = /^[^#<>[\]|{}/:@\u0000-\u001f]{1,85}$/
const normName = (s: string) => {
  const n = s.trim().replace(/_/g, ' ')
  return n.charAt(0).toUpperCase() + n.slice(1) // MediaWiki usernames start with a capital
}

/**
 * Parses admins.md.
 *  - `rely_on_username: true|false`  (default false)
 *  - one account per line: `Username` or `Username | id` (`-` bullets, `#` and <!-- --> comments allowed)
 */
export function readAdmins(file = resolve(process.cwd(), 'admins.md')): AdminFile {
  let mtime = 0
  try { mtime = statSync(file).mtimeMs } catch { return { relyOnUsername: false, admins: [] } }
  if (cache?.path === file && cache.mtime === mtime) return cache.file
  const out: AdminFile = { relyOnUsername: false, admins: [] }
  const text = readFileSync(file, 'utf8').replace(/<!--[\s\S]*?-->/g, '') // comments may span lines
  for (const raw of text.split('\n')) {
    const line = raw.replace(/^\s*[-*]\s*/, '').trim()
    if (!line || line.startsWith('#')) continue
    const opt = line.match(/^rely[_-]on[_-]username\s*[:=]\s*(true|false)\s*$/i)
    if (opt) { out.relyOnUsername = opt[1].toLowerCase() === 'true'; continue }
    const [username, id] = line.split('|').map((s) => s.trim())
    if (username && VALID_NAME.test(username)) out.admins.push({ username: normName(username), id: id && /^\d+$/.test(id) ? id : undefined })
  }
  cache = { path: file, mtime, file: out }
  return out
}

// username -> user id (null = no such account), cached so a login doesn't hit the API every time
const idCache = new Map<string, { id: string | null; at: number }>()
const TTL = 10 * 60 * 1000

/** Resolves usernames to user ids with one batched `list=users` call per ≤50 names. `api` is the wiki's api.php. */
export async function resolveUserIds(api: string, names: string[]): Promise<Record<string, string | null>> {
  const now = Date.now()
  const out: Record<string, string | null> = {}
  const todo = [...new Set(names.map(normName))].filter((n) => {
    const c = idCache.get(n)
    if (c && now - c.at < TTL) { out[n] = c.id; return false }
    return true
  })
  for (let i = 0; i < todo.length; i += 50) {
    const batch = todo.slice(i, i + 50)
    const res = await $fetch<{ query?: { users?: { userid?: number; name: string; missing?: boolean; invalid?: boolean }[] } }>(api, {
      headers: { 'User-Agent': 'wikiaccionperu.org (editor list)' },
      query: { action: 'query', list: 'users', ususers: batch.join('|'), format: 'json', formatversion: 2 },
    }).catch(() => null)
    if (!res) { for (const n of batch) out[n] = idCache.get(n)?.id ?? null; continue } // API down: stale value or fail closed
    const found = new Map((res.query?.users ?? []).filter((u) => u.userid && !u.missing && !u.invalid).map((u) => [normName(u.name), String(u.userid)]))
    for (const n of batch) {
      const id = found.get(n) ?? null
      idCache.set(n, { id, at: now })
      out[n] = id
    }
  }
  return out
}

/**
 * - rely_on_username: false (default): only entries written `Username | id` count; ids are the rename-proof key.
 * - rely_on_username: true: usernames are enough; their ids are looked up through the API and compared with the
 *   id of the logged-in account (so the login and the lookup must use the same wiki — see oauthEndpoints).
 */
export async function isAdmin(user: AuthUser | undefined, api: string): Promise<boolean> {
  return isAdminWith(readAdmins(), user, api)
}

/** Same check against an arbitrary configuration (used to refuse an edit that would lock the editor out). */
export async function isAdminWith(cfg: AdminFile, user: AuthUser | undefined, api: string): Promise<boolean> {
  if (!user?.id) return false
  if (!cfg.relyOnUsername) return cfg.admins.some((a) => a.id === user.id)
  const ids = await resolveUserIds(api, cfg.admins.map((a) => a.username))
  return Object.values(ids).includes(user.id)
}

export const isValidUsername = (n: unknown): n is string => typeof n === 'string' && VALID_NAME.test(n.trim())

const FILE_HEAD = `# Editors (site administrators)

<!--
HOW THIS FILE WORKS
- One Wikimedia account per line, e.g. \`- Yug\`. This file can also be edited in the site settings (/admin/editors/).
- rely_on_username: true   -> usernames are enough. The site looks up each account's user id on Commons
                              (api.php?action=query&list=users&ususers=A|B) and compares it with the id of the
                              account that logged in. Renamed accounts must be updated here.
- rely_on_username: false  -> strict mode: write \`Username | id\`; lines without an id grant nothing.
- Lines starting with # are ignored.
-->
`

export function formatAdminsFile(cfg: AdminFile): string {
  const lines = cfg.admins.map((a) => (!cfg.relyOnUsername && a.id ? `- ${a.username} | ${a.id}` : `- ${a.username}`))
  return `${FILE_HEAD}\nrely_on_username: ${cfg.relyOnUsername}\n\n${lines.join('\n')}\n`
}
export type { AdminFile, Admin }

/** Guard for every write endpoint: 401 if not logged in, 403 if not an editor. */
export async function requireAdmin(event: H3Event): Promise<AuthUser> {
  const { data } = await useAuthSession(event)
  if (!data.user) throw createError({ statusCode: 401, statusMessage: 'Login required' })
  if (!(await isAdmin(data.user, oauthEndpoints(event).api))) throw createError({ statusCode: 403, statusMessage: 'Not an editor' })
  return data.user
}
