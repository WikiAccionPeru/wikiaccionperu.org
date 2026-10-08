import menu from '~~/data/menu.json'
import taxonomies from '~~/data/taxonomies.json'
import taxonomyIndex from '~~/data/taxonomy-index.json'
import mediaIndex from '~~/data/media-index.json'

type TaxDef = { prefix: string; terms: { slug: string; name: string; count: number }[] }
const tax = taxonomies as Record<string, TaxDef>

export const useSite = () => ({
  menu,
  perPage: 9,
  thumb: (id?: number) => (id ? (mediaIndex as Record<string, string>)[String(id)] : undefined),
  term: (taxonomy: string, slug: string) => {
    const def = tax[taxonomy]
    const t = def?.terms.find((x) => x.slug === slug)
    return t ? { name: t.name.replace(/&amp;/g, '&'), to: `/${def.prefix}/${slug}/` } : undefined
  },
  /** Resolve /<prefix>/<slug> to a taxonomy archive, or undefined. */
  archive: (parts: string[]) => {
    const paged = parts.length === 4 && parts[2] === 'page' && /^\d+$/.test(parts[3])
    if (parts.length !== 2 && !paged) return undefined
    const [taxonomy, def] = Object.entries(tax).find(([, d]) => d.prefix === parts[0]) ?? []
    const t = def?.terms.find((x) => x.slug === parts[1])
    return taxonomy && t ? { taxonomy, page: paged ? Number(parts[3]) : 1, name: t.name.replace(/&amp;/g, '&'), paths: (taxonomyIndex as Record<string, string[]>)[`${taxonomy}/${parts[1]}`] ?? [] } : undefined
  },
  // Same style as the WordPress site: "octubre 5, 2026"
  formatDate: (iso: string) => {
    const d = new Date(iso)
    return `${new Intl.DateTimeFormat('es', { month: 'long' }).format(d).toLowerCase()} ${d.getDate()}, ${d.getFullYear()}`
  },
})
