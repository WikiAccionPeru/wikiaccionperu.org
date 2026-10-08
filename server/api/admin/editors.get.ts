export default defineEventHandler(async (event) => {
  const me = await requireAdmin(event)
  setHeader(event, 'Cache-Control', 'no-store')
  const cfg = readAdmins()
  const ids = await resolveUserIds(oauthEndpoints(event).api, cfg.admins.map((a) => a.username))
  return { relyOnUsername: cfg.relyOnUsername, admins: cfg.admins.map((a) => ({ username: a.username, id: a.id ?? null, resolvedId: ids[a.username] ?? null })), me }
})
