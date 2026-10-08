type Item = { title: string; url: string; children: Item[] }
const URL_OK = /^(\/[^\s<>"]*|https:\/\/[^\s<>"]+)$/

function clean(items: unknown, depth: number): Item[] {
  if (!Array.isArray(items) || items.length > (depth === 0 ? 20 : 15)) throw createError({ statusCode: 422, statusMessage: 'Menú demasiado largo' })
  return items.map((it: any) => {
    const title = typeof it?.title === 'string' ? it.title.trim() : ''
    const url = typeof it?.url === 'string' ? it.url.trim() : ''
    if (!title || title.length > 80) throw createError({ statusCode: 422, statusMessage: 'Cada elemento necesita un título (máx. 80 caracteres)' })
    if (!URL_OK.test(url) || url.length > 300) throw createError({ statusCode: 422, statusMessage: `Dirección no válida en «${title}» (usa /ruta o https://…)` })
    if (depth >= 1 && it.children?.length) throw createError({ statusCode: 422, statusMessage: 'El menú admite solo dos niveles' })
    return { title, url, children: depth === 0 ? clean(it.children ?? [], 1) : [] }
  })
}

export default defineEventHandler(async (event) => {
  const user = await requireAdmin(event)
  assertSameOrigin(event)
  const menu = clean(await readBody(event), 0)
  if (!menu.length) throw createError({ statusCode: 422, statusMessage: 'El menú no puede quedar vacío' })
  writeJson('menu.json', menu)
  console.info(`[admin] ${user.username} saved the menu (${menu.length} items)`)
  return { ok: true, items: menu.length }
})
