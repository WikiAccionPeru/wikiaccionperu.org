import type { H3Event } from 'h3'

/** OAuth endpoints live on the same wiki as the authorize URL (token + profile follow it). */
export function oauthEndpoints(event: H3Event) {
  const cfg = useRuntimeConfig(event)
  const authorize = String(cfg.oauthAuthorizeUrl)
  const base = authorize.replace(/\/authorize$/, '')
  return {
    authorize,
    token: `${base}/access_token`,
    profile: `${base}/resource/profile`,
    // Same wiki's action API (fallback identity lookup, as in the working Lingua Libre backend)
    api: new URL(authorize).origin + '/w/api.php',
    redirectUri: String(cfg.oauthRedirectUri || `${cfg.public.siteUrl}/api/auth/callback`),
  }
}

const UA = 'wikiaccionperu.org (editor login)'

export async function handleOAuthCallback(event: H3Event) {
  const cfg = useRuntimeConfig(event)
  const ep = oauthEndpoints(event)
  const q = getQuery(event)
  const session = await useAuthSession(event)
  const pending = session.data.oauth
  await session.update({ oauth: undefined }) // one-shot, whatever happens next
  if (q.error) throw createError({ statusCode: 400, statusMessage: 'Login cancelled or refused' })
  if (!pending || typeof q.state !== 'string' || q.state !== pending.state || typeof q.code !== 'string') {
    throw createError({ statusCode: 400, statusMessage: 'Invalid login state' })
  }
  const body = new URLSearchParams({
    grant_type: 'authorization_code',
    code: q.code,
    redirect_uri: ep.redirectUri,
    client_id: String(cfg.oauthClientId),
    code_verifier: pending.verifier,
  })
  if (cfg.oauthClientSecret) body.set('client_secret', String(cfg.oauthClientSecret))
  let accessToken: string | undefined
  try {
    accessToken = (await $fetch<{ access_token?: string }>(ep.token, { method: 'POST', body, headers: { 'User-Agent': UA } })).access_token
  } catch (e: any) {
    const err = e?.data?.error || e?.data?.message || e?.statusCode
    console.error('[oauth] token exchange failed:', err, e?.data?.error_description ?? '')
    const hint = err === 'invalid_client' && !cfg.oauthClientSecret ? ' (this consumer is confidential: set NUXT_OAUTH_CLIENT_SECRET)' : ''
    throw createError({ statusCode: 502, statusMessage: `Token exchange failed: ${err}${hint}` })
  }
  if (!accessToken) throw createError({ statusCode: 502, statusMessage: 'Token exchange returned no token' })
  // Identify the visitor with the wiki's userinfo (same call as the working Lingua Libre backend). Its `id` is the
  // wiki-local user id: the same kind of id `list=users` returns, which the editor list relies on.
  // Falls back to the OAuth profile (`sub` is a central id: it will not match a local-id lookup, so it fails closed).
  let who: { id?: string; username?: string } | null = null
  const headers = { Authorization: `Bearer ${accessToken}`, 'User-Agent': UA }
  const info = await $fetch<{ query?: { userinfo?: { id?: number; name?: string } } }>(ep.api, {
    headers, query: { action: 'query', meta: 'userinfo', format: 'json', formatversion: 2 },
  }).catch((e) => { console.error('[oauth] userinfo failed:', e?.statusCode); return null })
  const u = info?.query?.userinfo
  if (u?.name && u.id) who = { id: String(u.id), username: u.name }
  else {
    const profile = await $fetch<{ sub?: string | number; username?: string }>(ep.profile, { headers }).catch((e) => {
      console.error('[oauth] profile failed:', e?.statusCode, e?.data?.error ?? ''); return null
    })
    if (profile?.sub && profile.username) who = { id: String(profile.sub), username: profile.username }
  }
  if (!who?.username) throw createError({ statusCode: 502, statusMessage: 'Could not identify the Wikimedia user' })
  // The access token is not stored: we only need to know who the visitor is.
  await session.update({ user: { id: who.id ?? '', username: who.username } })
  return sendRedirect(event, pending.returnTo)
}
