import routes from './data/routes.json'
import redirects from './data/redirects.json'
import { execSync } from 'node:child_process'

const commit = (() => {
  try { return execSync('git rev-parse --short HEAD', { stdio: ['ignore', 'pipe', 'ignore'] }).toString().trim() }
  catch { return 'dev' }
})()

export default defineNuxtConfig({
  compatibilityDate: '2026-01-01',
  modules: ['@nuxt/content', '@nuxt/image', '@nuxt/fonts'],
  components: [{ path: '~/components', pathPrefix: false }],
  css: ['~/assets/tokens.css', '~/assets/base.css'],
  app: {
    head: {
      htmlAttrs: { lang: 'es' },
      link: [{ rel: 'icon', href: '/media/2021/10/cropped-isotipo_wikiaccion-2.png' }],
      meta: [{ name: 'viewport', content: 'width=device-width, initial-scale=1' }],
    },
  },
  content: { experimental: { nativeSqlite: true } },
  runtimeConfig: {
    // Wikimedia OAuth 2.0 consumer. Falls back to the VITE_* names already used by sibling projects (e.g. Lingua Libre).
    oauthClientId: process.env.NUXT_OAUTH_CLIENT_ID || process.env.CLIENT_ID || process.env.VITE_OAUTH_ACCESS_TOKEN || '',
    oauthClientSecret: process.env.NUXT_OAUTH_CLIENT_SECRET || process.env.CLIENT_SECRET || '', // required for "confidential" consumers
    // Wiki whose OAuth endpoints are used; project-restricted consumers (e.g. commons only) must use that wiki.
    oauthAuthorizeUrl: process.env.NUXT_OAUTH_AUTHORIZE_URL || process.env.VITE_AUTHORIZATION_ENDPOINT || 'https://meta.wikimedia.org/w/rest.php/oauth2/authorize',
    // Must equal the callback registered on the consumer; default <siteUrl>/api/auth/callback.
    oauthRedirectUri: '', // NUXT_OAUTH_REDIRECT_URI
    sessionSecret: '', // NUXT_SESSION_SECRET
    public: { commit, siteUrl: 'http://localhost:3000' }, // NUXT_PUBLIC_SITE_URL
  },
  fonts: { families: [{ name: 'Ubuntu', weights: [400, 500, 600, 700], provider: 'google' }, { name: 'Source Code Pro', weights: [400, 600], provider: 'google' }] },
  image: { format: ['webp'], quality: 80, screens: { sm: 480, md: 768, lg: 1024 } },
  routeRules: Object.fromEntries((redirects as { from: string; to: string }[]).map((r) => [r.from, { redirect: { to: r.to, statusCode: 301 } }])),
  nitro: { prerender: { routes: [...routes, '/search-index.json', ...(redirects as { from: string }[]).map((r) => r.from)], crawlLinks: false, failOnError: false } },
})
