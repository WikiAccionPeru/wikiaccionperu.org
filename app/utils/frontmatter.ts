import { parse, stringify } from 'yaml'

export type Doc = { data: Record<string, any>; body: string }

/** Splits a Markdown file into its properties (YAML frontmatter) and body. */
export function splitDoc(text: string): Doc {
  const m = text.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?([\s\S]*)$/)
  if (!m) return { data: {}, body: text }
  const data = parse(m[1])
  return { data: data && typeof data === 'object' && !Array.isArray(data) ? data : {}, body: m[2] }
}

/** Joins them back (lineWidth 0: never re-wrap long texts). */
export function joinDoc(doc: Doc): string {
  return `---\n${stringify(doc.data, { lineWidth: 0 })}---\n\n${doc.body.replace(/^\n+/, '')}`
}
