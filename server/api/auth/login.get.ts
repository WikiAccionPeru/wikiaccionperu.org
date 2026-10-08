import { createHash, randomBytes } from 'node:crypto'

const b64 = (b: Buffer) => b.toString('base64url')

// Starts the OAuth 2.0 authorization-code flow with PKCE (S256) and a random `state`.
export default defineEventHandler(async (event) => {
  const cfg = useRuntimeConfig(event)
  if (!cfg.oauthClientId) throw createError({ statusCode: 503, statusMessage: 'OAuth is not configured (NUXT_OAUTH_CLIENT_ID)' })
  const verifier = b64(randomBytes(32))
  const state = b64(randomBytes(16))
  const session = await useAuthSession(event)
  await session.update({ oauth: { state, verifier, returnTo: safeReturnTo(getQuery(event).returnTo) } })
  const ep = oauthEndpoints(event)
  const url = new URL(ep.authorize)
  url.search = new URLSearchParams({
    response_type: 'code',
    client_id: String(cfg.oauthClientId),
    redirect_uri: ep.redirectUri,
    state,
    code_challenge: b64(createHash('sha256').update(verifier).digest()),
    code_challenge_method: 'S256',
  }).toString()
  return sendRedirect(event, url.toString())
})
