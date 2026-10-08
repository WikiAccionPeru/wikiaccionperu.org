// Move/rename a page. Body: { from, to }. The old address is recorded as a redirect.
export default defineEventHandler(async (event) => {
  const user = await requireAdmin(event)
  assertSameOrigin(event)
  const b = await readBody<{ from?: string; to?: string }>(event)
  const r = movePage(String(b?.from ?? ''), String(b?.to ?? ''))
  removeRoutes([r.from]); addRoutes([r.to]); addRedirect(r.from, r.to)
  console.info(`[admin] ${user.username} moved ${r.from} -> ${r.to}`)
  return { ok: true, ...r }
})
