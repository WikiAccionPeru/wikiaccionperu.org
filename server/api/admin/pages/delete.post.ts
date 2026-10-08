// Delete (to trash). Body: { path }
export default defineEventHandler(async (event) => {
  const user = await requireAdmin(event)
  assertSameOrigin(event)
  const b = await readBody<{ path?: string }>(event)
  const r = deletePage(String(b?.path ?? ''))
  removeRoutes([r.path])
  console.info(`[admin] ${user.username} deleted ${r.path} (-> ${r.trashed})`)
  return { ok: true, ...r }
})
