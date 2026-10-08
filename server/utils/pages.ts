import { existsSync, mkdirSync, readdirSync, readFileSync, renameSync, writeFileSync } from 'node:fs'
import { dirname, join, relative, resolve } from 'node:path'
import { parse as parseYaml } from 'yaml'
import { contentFileFor, defaultContentDir } from './content-files'

const mkErr = (statusCode: number, statusMessage: string) => (globalThis as any).createError?.({ statusCode, statusMessage }) ?? Object.assign(new Error(statusMessage), { statusCode, statusMessage })

// URL space owned by the app itself (never usable as a page address) and the taxonomy archives.
const RESERVED = new Set(['admin', 'api', '_nuxt', '_ipx', 'media', 'buscar', 'oauth', 'styleguide', 'categoria', 'etiqueta', 'tipo-recurso', 'enfoque-tematico', 'tipo_alianza', 'search-index.json', 'page', '__nuxt_content'])
const SLUG = /^[a-z0-9]+(?:-[a-z0-9]+)*$/

/** New or moved addresses are strict: lowercase ascii words joined by "-", at most 4 levels, not reserved. */
export function validateNewRoute(route: unknown): string {
  if (typeof route !== 'string' || !route.startsWith('/')) throw mkErr(400, 'Bad path')
  const parts = route.split('/').filter(Boolean)
  if (!parts.length || parts.length > 4) throw mkErr(422, 'La dirección debe tener entre 1 y 4 niveles')
  if (!parts.every((p) => SLUG.test(p) && p.length <= 100)) throw mkErr(422, 'Usa solo minúsculas, números y guiones (a-z, 0-9, -) en cada nivel')
  if (RESERVED.has(parts[0])) throw mkErr(422, `«${parts[0]}» está reservado por el sistema`)
  return '/' + parts.join('/')
}

/** Frontmatter block → object (null when absent/invalid). */
export function readFrontmatter(text: string): Record<string, unknown> | null {
  const m = text.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/)
  if (!m) return null
  try { const v = parseYaml(m[1]); return v && typeof v === 'object' && !Array.isArray(v) ? (v as Record<string, unknown>) : null } catch { return null }
}

/** Every page must keep a valid frontmatter: title, type and date are required by the content schema. */
export function validatePageText(text: unknown): string {
  if (typeof text !== 'string' || text.length > 1_000_000) throw mkErr(400, 'Bad content')
  const fm = readFrontmatter(text)
  if (!fm) throw mkErr(422, 'La página debe empezar con un bloque de propiedades (--- … ---) válido')
  for (const k of ['title', 'type', 'date'] as const) {
    if (typeof fm[k] !== 'string' || !(fm[k] as string).trim()) throw mkErr(422, `Falta la propiedad «${k}»`)
  }
  if (fm.status !== 'publish' && fm.status !== 'draft') throw mkErr(422, 'La propiedad «status» debe ser publish o draft')
  return text.endsWith('\n') ? text : text + '\n'
}

export type PageInfo = { path: string; title: string; type: string; date: string }

export function listPages(base = defaultContentDir()): PageInfo[] {
  const out: PageInfo[] = []
  const walk = (dir: string) => {
    for (const e of readdirSync(dir, { withFileTypes: true })) {
      if (e.name.startsWith('.')) continue // .trash etc.
      const full = join(dir, e.name)
      if (e.isDirectory()) { walk(full); continue }
      if (!e.name.endsWith('.md')) continue
      const rel = relative(base, full).replace(/\\/g, '/').replace(/\.md$/, '')
      const route = rel === 'index' ? '/' : '/' + rel.replace(/\/index$/, '')
      const fm = readFrontmatter(readFileSync(full, 'utf8').slice(0, 6000)) ?? {}
      out.push({ path: route, title: String(fm.title ?? route), type: String(fm.type ?? ''), date: String(fm.date ?? '') })
    }
  }
  if (existsSync(base)) walk(base)
  return out.sort((a, b) => a.path.localeCompare(b.path))
}

const q = (s: string) => JSON.stringify(s)
export function createPage(route: string, opts: { title: string; type: 'page' | 'post' }, base = defaultContentDir()) {
  const target = validateNewRoute(route)
  if (typeof opts.title !== 'string' || !opts.title.trim() || opts.title.length > 300) throw mkErr(422, 'Falta el título')
  if (!['page', 'post'].includes(opts.type)) throw mkErr(422, 'Tipo no válido')
  const { file, exists } = contentFileFor(target, base)
  if (exists) throw mkErr(409, 'Ya existe una página en esa dirección')
  const slug = target.split('/').pop()!
  const now = new Date(Date.now() - new Date().getTimezoneOffset() * 60000).toISOString().slice(0, 19)
  mkdirSync(dirname(file), { recursive: true })
  writeFileSync(file, `---\ntitle: ${q(opts.title.trim())}\nslug: ${q(slug)}\ntype: ${q(opts.type)}\ndate: ${q(now)}\nstatus: "publish"\n---\n\nEscribe aquí el contenido.\n`, { flag: 'wx' })
  return target
}

export function movePage(from: string, to: string, base = defaultContentDir()) {
  if (from === '/' || from === '') throw mkErr(422, 'La página de inicio no se puede mover')
  const src = contentFileFor(from, base)
  if (!src.exists) throw mkErr(404, 'No such page')
  const target = validateNewRoute(to)
  const dst = contentFileFor(target, base)
  if (dst.exists) throw mkErr(409, 'Ya existe una página en la dirección de destino')
  if (src.route === target) throw mkErr(422, 'Origen y destino son iguales')
  mkdirSync(dirname(dst.file), { recursive: true })
  renameSync(src.file, dst.file)
  // keep the frontmatter slug in step with the new address
  const text = readFileSync(dst.file, 'utf8')
  writeFileSync(dst.file, text.replace(/^slug:.*$/m, `slug: ${q(target.split('/').pop()!)}`))
  return { from: src.route, to: target }
}

/** Soft delete: the file goes to content/.trash (ignored by the site, recoverable by hand or from git). */
export function deletePage(route: string, base = defaultContentDir()) {
  if (route === '/' || route === '') throw mkErr(422, 'La página de inicio no se puede eliminar')
  const src = contentFileFor(route, base)
  if (!src.exists) throw mkErr(404, 'No such page')
  const trash = resolve(base, '.trash')
  mkdirSync(trash, { recursive: true })
  const stamp = new Date().toISOString().replace(/[:.]/g, '-')
  const dest = join(trash, `${stamp}__${src.route.slice(1).replace(/\//g, '__')}.md`)
  renameSync(src.file, dest)
  return { path: src.route, trashed: relative(base, dest) }
}
