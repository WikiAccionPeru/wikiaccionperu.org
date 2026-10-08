<script setup lang="ts">
type Entry = { p: string; t: string; d: string; k: string; x: string; g: string }
const route = useRoute()
const { formatDate } = useSite()
definePageMeta({ layout: 'band' })
useSeoMeta({ title: 'Buscar — WikiAcción Perú', robots: 'noindex' })

const norm = (s: string) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()
const query = computed(() => String(route.query.q ?? '').trim())
const index = ref<Entry[] | null>(null)
const failed = ref(false)
onMounted(async () => {
  try { index.value = await $fetch<Entry[]>('/search-index.json') } catch { failed.value = true }
})
const typeLabel: Record<string, string> = { post: 'Noticia', page: 'Página', recurso: 'Recurso', alianza: 'Alianza', nota: 'Nota' }
const results = computed(() => {
  const terms = norm(query.value).split(/\s+/).filter(Boolean)
  if (!index.value || !terms.length) return []
  return index.value
    .map((e) => {
      const title = norm(e.t), rest = norm(`${e.x} ${e.g}`)
      if (!terms.every((t) => title.includes(t) || rest.includes(t))) return null
      return { e, score: terms.reduce((s, t) => s + (title.includes(t) ? 3 : 0) + (rest.includes(t) ? 1 : 0), 0) }
    })
    .filter((r): r is { e: Entry; score: number } => !!r)
    .sort((a, b) => b.score - a.score || b.e.d.localeCompare(a.e.d))
    .slice(0, 60)
    .map((r) => r.e)
})
</script>
<template>
  <div class="with-aside">
    <div>
      <h1>Resultados de búsqueda<template v-if="query">: «{{ query }}»</template></h1>
      <p v-if="failed">No se pudo cargar el índice de búsqueda.</p>
      <p v-else-if="!query">Escribe algo para buscar.</p>
      <p v-else-if="!index">Buscando…</p>
      <p v-else-if="!results.length">Sin resultados para «{{ query }}».</p>
      <ol v-else class="results">
        <li v-for="r in results" :key="r.p">
          <NuxtLink :to="r.p + '/'"><span v-html="r.t" /></NuxtLink>
          <small>{{ typeLabel[r.k] ?? r.k }} · {{ formatDate(r.d) }}</small>
          <p v-if="r.x">{{ r.x }}…</p>
        </li>
      </ol>
    </div>
    <div class="side"><SearchBox :initial="query" /></div>
  </div>
</template>
<style scoped>
.with-aside { display: grid; grid-template-columns: 1fr 18rem; gap: var(--space-4); align-items: start; }
h1 { margin-top: 0; }
.results { list-style: none; margin: 0; padding: 0; display: grid; gap: var(--space-3); }
.results li { background: #fff; border: var(--border); padding: var(--space-3) var(--space-4); }
.results a { font: 600 1.15rem var(--font-heading); text-decoration: none; }
.results small { display: block; color: var(--color-text-muted); margin: var(--space-1) 0; }
.results p { margin: 0; font-size: 0.85rem; }
@media (max-width: 1000px) { .with-aside { grid-template-columns: 1fr; } .side { order: -1; } }
</style>
