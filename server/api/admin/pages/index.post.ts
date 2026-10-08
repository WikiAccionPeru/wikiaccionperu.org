// Create a page. Body: { path, title, type: 'page' | 'post' }
export default defineEventHandler(async (event) => {
  const user = await requireAdmin(event)
  assertSameOrigin(event)
  const b = await readBody<{ path?: string; title?: string; type?: 'page' | 'post' }>(event)
  const route = createPage(String(b?.path ?? ''), { title: String(b?.title ?? ''), type: b?.type as 'page' | 'post' })
  addRoutes([route])
  console.info(`[admin] ${user.username} created ${route}`)
  return { ok: true, path: route }
})
