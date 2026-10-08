// "Username → id" helper. ?names=Yug|Jesedmateo (also accepts commas or new lines), max 50.
export default defineEventHandler(async (event) => {
  await requireAdmin(event)
  const raw = String(getQuery(event).names ?? '')
  const names = [...new Set(raw.split(/[|,\n]/).map((s) => s.trim()).filter(Boolean))]
  if (!names.length || names.length > 50) throw createError({ statusCode: 400, statusMessage: 'Indica entre 1 y 50 nombres' })
  const invalid = names.filter((n) => !isValidUsername(n))
  const ok = names.filter((n) => isValidUsername(n))
  const ids = await resolveUserIds(oauthEndpoints(event).api, ok)
  return { ids, invalid }
})
