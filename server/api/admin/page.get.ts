import { readFile } from 'node:fs/promises'

export default defineEventHandler(async (event) => {
  await requireAdmin(event)
  setHeader(event, 'Cache-Control', 'no-store')
  const { file, exists, route } = contentFileFor(getQuery(event).path)
  if (!exists) throw createError({ statusCode: 404, statusMessage: 'No such page' })
  return { path: route, text: await readFile(file, 'utf8') }
})
