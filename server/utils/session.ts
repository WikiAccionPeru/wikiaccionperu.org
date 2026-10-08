import type { H3Event } from 'h3'

export type AuthUser = { id: string; username: string }
export type SessionData = {
  user?: AuthUser
  oauth?: { state: string; verifier: string; returnTo: string }
}

let devSecret: string | undefined

/** Sealed, httpOnly session cookie (h3 useSession). */
export function useAuthSession(event: H3Event) {
  const cfg = useRuntimeConfig(event)
  let password = cfg.sessionSecret as string
  if (!password || password.length < 32) {
    if (!import.meta.dev) throw createError({ statusCode: 500, statusMessage: 'NUXT_SESSION_SECRET (32+ chars) is required' })
    devSecret ??= crypto.randomUUID() + crypto.randomUUID() // ephemeral: dev sessions end on restart
    password = devSecret
  }
  return useSession<SessionData>(event, {
    password,
    name: 'wap_session',
    maxAge: 60 * 60 * 8,
    cookie: { httpOnly: true, sameSite: 'lax', secure: !import.meta.dev, path: '/' },
  })
}

/** Only same-site relative paths may be used as post-login destination (no open redirects). */
export function safeReturnTo(value: unknown): string {
  const v = typeof value === 'string' ? value : '/'
  return v.startsWith('/') && !v.startsWith('//') && !v.includes('\\') ? v : '/'
}
