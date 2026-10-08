type MNode = string | [string, Record<string, unknown>, ...MNode[]]
const textOf = (n: MNode): string => (typeof n === 'string' ? n : n.slice(2).map((c) => textOf(c as MNode)).join(' '))
/** First paragraph(s) of the body, as plain text (used when WordPress had no excerpt). */
const lead = (body: { value?: MNode[] } | undefined, max = 220) => {
  let out = ''
  for (const n of body?.value ?? []) {
    if (Array.isArray(n) && n[0] === 'p') out += ' ' + textOf(n)
    if (out.trim().length >= max) break
  }
  return out.replace(/\s+/g, ' ').trim().slice(0, max)
}

// Prerendered at build time (see nitro.prerender.routes): compact index searched in the browser.
export default defineEventHandler(async (event) => {
  const docs = await queryCollection(event, 'content').select('path', 'title', 'date', 'type', 'status', 'excerpt', 'taxonomies', 'body').all()
  setHeader(event, 'Content-Type', 'application/json; charset=utf-8')
  return docs
    .filter((d) => d.path !== '/' && d.status === 'publish')
    .map((d) => ({
      p: d.path,
      t: d.title,
      d: d.date?.slice(0, 10),
      k: d.type,
      x: (d.excerpt || lead(d.body as never)).slice(0, 220),
      g: Object.values(d.taxonomies ?? {}).flat().map((s) => s.replace(/-/g, ' ')).join(' '),
    }))
})
