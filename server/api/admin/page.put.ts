import { rename, writeFile } from 'node:fs/promises'

export default defineEventHandler(async (event) => {
  const user = await requireAdmin(event)
  assertSameOrigin(event)
  const body = await readBody<{ path?: string; text?: string }>(event)
  const { file, exists, route } = contentFileFor(body?.path)
  if (!exists) throw createError({ statusCode: 404, statusMessage: 'No such page' })
  const text = validatePageText(body?.text)
  const tmp = `${file}.${process.pid}.tmp`
  await writeFile(tmp, text, 'utf8')
  await rename(tmp, file) // atomic replace
  console.info(`[admin] ${user.username} (${user.id}) saved ${route}`)
  return { ok: true, path: route, bytes: text.length }
})
