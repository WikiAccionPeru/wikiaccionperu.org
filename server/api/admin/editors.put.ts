import { rename, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'

// Replace the editor list. Refuses a list that would lock the current editor out.
export default defineEventHandler(async (event) => {
  const user = await requireAdmin(event)
  assertSameOrigin(event)
  const b = await readBody<{ relyOnUsername?: boolean; admins?: { username?: string; id?: string | null }[] }>(event)
  if (typeof b?.relyOnUsername !== 'boolean' || !Array.isArray(b.admins) || b.admins.length > 100) throw createError({ statusCode: 400, statusMessage: 'Bad request' })
  const seen = new Set<string>()
  const admins = b.admins.map((a) => {
    if (!isValidUsername(a?.username)) throw createError({ statusCode: 422, statusMessage: `Nombre de usuario no válido: «${a?.username ?? ''}»` })
    const username = a.username.trim().replace(/_/g, ' ').replace(/^./, (c) => c.toUpperCase())
    if (seen.has(username.toLowerCase())) throw createError({ statusCode: 422, statusMessage: `Nombre repetido: ${username}` })
    seen.add(username.toLowerCase())
    const id = a.id && /^\d+$/.test(String(a.id)) ? String(a.id) : undefined
    if (!b.relyOnUsername && !id) throw createError({ statusCode: 422, statusMessage: `En modo estricto, «${username}» necesita un id` })
    return { username, id }
  })
  const cfg = { relyOnUsername: b.relyOnUsername, admins }
  if (!(await isAdminWith(cfg, user, oauthEndpoints(event).api))) {
    throw createError({ statusCode: 422, statusMessage: 'Con esta lista tu propia cuenta dejaría de ser editora; no se guarda' })
  }
  const file = resolve(process.cwd(), 'admins.md')
  await writeFile(file + '.tmp', formatAdminsFile(cfg), 'utf8')
  await rename(file + '.tmp', file)
  console.info(`[admin] ${user.username} updated the editor list (${admins.length})`)
  return { ok: true, count: admins.length }
})
