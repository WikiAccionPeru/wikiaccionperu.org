export default defineEventHandler(async (event) => {
  setHeader(event, 'Cache-Control', 'no-store')
  const { data } = await useAuthSession(event)
  return { user: data.user ?? null, admin: await isAdmin(data.user, oauthEndpoints(event).api) }
})
