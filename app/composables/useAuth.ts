type Me = { user: { id: string; username: string } | null; admin: boolean }

/** Login state, loaded client-side only: pages are static, so it can never be baked into the HTML. */
export const useAuth = () => {
  // Styleguide only: <SgAuthScope> provides a fixed identity to its descendants so editor-only components can be shown.
  const demo = getCurrentInstance() ? inject<Me | null>('authDemo', null) : null
  if (demo) return { me: ref(demo), loaded: ref(true), refresh: async () => {}, logout: async () => {}, loginUrl: (r = '/') => `/api/auth/login?returnTo=${encodeURIComponent(r)}` }
  const me = useState<Me>('auth-me', () => ({ user: null, admin: false }))
  const loaded = useState('auth-loaded', () => false)
  const refresh = async () => {
    me.value = await $fetch<Me>('/api/auth/me').catch(() => ({ user: null, admin: false }))
    loaded.value = true
  }
  const logout = async () => {
    await $fetch('/api/auth/logout', { method: 'POST' }).catch(() => {})
    me.value = { user: null, admin: false }
    await navigateTo('/')
  }
  const loginUrl = (returnTo = '/') => `/api/auth/login?returnTo=${encodeURIComponent(returnTo)}`
  return { me, loaded, refresh, logout, loginUrl }
}
