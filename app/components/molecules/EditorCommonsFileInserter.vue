<script setup lang="ts">
/** Toolbar tool: search Wikimedia Commons, pick an image, insert it as Markdown (with optional credit line). */
const emit = defineEmits<{ insert: [markdown: string] }>()
const API = 'https://commons.wikimedia.org/w/api.php'
const WIKIMEDIA_IMG = /^https:\/\/(upload|thumb)\.wikimedia\.org\//

type Hit = { title: string; thumb: string; width: number; height: number; license: string }
type Detail = { title: string; src: string; page: string; width: number; description: string; artist: string; license: string; licenseUrl: string }

const dlg = ref<HTMLDialogElement>()
const q = ref('')
const hits = ref<Hit[]>([])
const more = ref<number | null>(null)
const busy = ref(false)
const error = ref('')
const searched = ref(false)
const chosen = ref<Detail | null>(null)
const alt = ref('')
const caption = ref('')
const credit = ref(true)

const strip = (html?: string) => (html ?? '').replace(/<[^>]*>/g, ' ').replace(/&amp;/g, '&').replace(/&quot;/g, '"').replace(/&#0?39;/g, "'").replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/\s+/g, ' ').replace(/\(\s+/g, '(').replace(/\s+([),.;:])/g, '$1').trim()
const niceTitle = (t: string) => t.replace(/^File:/, '').replace(/\.[a-z0-9]+$/i, '').replace(/_/g, ' ')
const shorten = (s: string, n: number) => (s.length > n ? s.slice(0, n - 1).trimEnd() + '…' : s)
const safeUrl = (u: string) => u.replace(/\(/g, '%28').replace(/\)/g, '%29').replace(/\s/g, '%20')

function open() { dlg.value?.showModal(); nextTick(() => (document.getElementById('cfi-q') as HTMLInputElement | null)?.focus()) }
function close() { dlg.value?.close() }

async function search(offset = 0) {
  const term = q.value.trim()
  if (!term) return
  busy.value = true; error.value = ''
  if (!offset) { hits.value = []; chosen.value = null; more.value = null }
  try {
    const r: any = await $fetch(API, { query: {
      action: 'query', generator: 'search', gsrsearch: `${term} filetype:bitmap|drawing`, gsrnamespace: 6, gsrlimit: 24, gsroffset: offset,
      prop: 'imageinfo', iiprop: 'url|size|mime|extmetadata', iiurlwidth: 320, iiextmetadatafilter: 'LicenseShortName',
      format: 'json', formatversion: 2, origin: '*', uselang: 'es',
    } })
    const pages = [...(r.query?.pages ?? [])].sort((a: any, b: any) => a.index - b.index)
    hits.value.push(...pages.filter((p: any) => WIKIMEDIA_IMG.test(p.imageinfo?.[0]?.thumburl ?? '')).map((p: any) => ({
      title: p.title, thumb: p.imageinfo[0].thumburl, width: p.imageinfo[0].width, height: p.imageinfo[0].height,
      license: strip(p.imageinfo[0].extmetadata?.LicenseShortName?.value),
    })))
    more.value = r.continue?.gsroffset ?? null
    searched.value = true
  } catch { error.value = 'No se pudo consultar Wikimedia Commons. Inténtalo de nuevo.' } finally { busy.value = false }
}

async function choose(h: Hit) {
  busy.value = true; error.value = ''
  try {
    const r: any = await $fetch(API, { query: {
      action: 'query', titles: h.title, prop: 'imageinfo', iiprop: 'url|size|extmetadata', iiurlwidth: 1024,
      iiextmetadatafilter: 'ImageDescription|Artist|LicenseShortName|LicenseUrl', format: 'json', formatversion: 2, origin: '*', uselang: 'es',
    } })
    const ii = r.query?.pages?.[0]?.imageinfo?.[0]
    if (!ii) throw new Error('sin datos')
    const m = ii.extmetadata ?? {}
    const src: string = String(ii.thumburl || ii.url).split('?')[0] // drop utm_* tracking parameters
    if (!WIKIMEDIA_IMG.test(src)) throw new Error('origen no permitido') // only Wikimedia's own image hosts
    chosen.value = {
      title: h.title, src, page: ii.descriptionurl, width: ii.width,
      description: strip(m.ImageDescription?.value), artist: strip(m.Artist?.value), license: strip(m.LicenseShortName?.value), licenseUrl: m.LicenseUrl?.value ?? '',
    }
    alt.value = shorten(chosen.value.description || niceTitle(h.title), 125)
    caption.value = shorten(chosen.value.description || niceTitle(h.title), 160)
  } catch { error.value = 'No se pudieron leer los datos de la imagen.' } finally { busy.value = false }
}

const clean = (s: string) => s.replace(/[\r\n]+/g, ' ').replace(/[[\]]/g, '').replace(/"/g, "'").trim()
const markdown = computed(() => {
  const c = chosen.value
  if (!c) return ''
  const img = `![${clean(alt.value)}](${safeUrl(c.src)}${caption.value.trim() ? ` "${clean(caption.value)}"` : ''})`
  if (!credit.value) return img
  const lic = c.license ? (/^https?:\/\//.test(c.licenseUrl) ? `[${clean(c.license)}](${safeUrl(c.licenseUrl)})` : clean(c.license)) : 'licencia libre'
  const who = c.artist ? `${clean(shorten(c.artist, 80))}, ` : ''
  return `${img}\n\n*${clean(caption.value) || clean(niceTitle(c.title))} — ${who}${lic}, [vía Wikimedia Commons](${safeUrl(c.page)})*`
})
const canInsert = computed(() => !!chosen.value && alt.value.trim().length > 0)
function insert() { if (!canInsert.value) return; emit('insert', markdown.value); close() }
</script>

<template>
  <button type="button" title="Insertar imagen de Wikimedia Commons" @click="open">🖼 Commons</button>
  <dialog ref="dlg" class="cfi" aria-labelledby="cfi-h" @click.self="close" @keydown.esc.prevent="close">
    <form method="dialog" class="head"><h2 id="cfi-h">Imagen de Wikimedia Commons</h2><button type="submit" aria-label="Cerrar">✕</button></form>
    <form class="search" role="search" @submit.prevent="search(0)">
      <input id="cfi-q" v-model="q" type="search" placeholder="Buscar en Commons (p. ej. Machu Picchu)" aria-label="Buscar en Commons">
      <button type="submit" :disabled="busy || !q.trim()">Buscar</button>
    </form>
    <p v-if="error" class="err" role="alert">{{ error }}</p>
    <div class="body">
      <div class="results">
        <p v-if="searched && !hits.length && !busy">Sin resultados.</p>
        <ul v-if="hits.length" class="grid">
          <li v-for="h in hits" :key="h.title">
            <button type="button" :class="{ sel: chosen?.title === h.title }" :title="niceTitle(h.title)" @click="choose(h)">
              <img :src="h.thumb" :alt="niceTitle(h.title)" loading="lazy">
              <span>{{ shorten(niceTitle(h.title), 38) }}</span><small v-if="h.license">{{ h.license }}</small>
            </button>
          </li>
        </ul>
        <p v-if="busy">Cargando…</p>
        <button v-if="more !== null && !busy" type="button" class="more" @click="search(more!)">Cargar más</button>
      </div>
      <form v-if="chosen" class="detail" @submit.prevent="insert">
        <img :src="chosen.src" :alt="alt" class="prev">
        <p class="meta"><strong>{{ niceTitle(chosen.title) }}</strong><br>{{ chosen.artist || 'Autor no indicado' }} · {{ chosen.license || 'licencia no indicada' }} · <a :href="chosen.page" target="_blank" rel="noopener">ver en Commons</a></p>
        <label>Texto alternativo (obligatorio, describe la imagen)<input v-model="alt" required maxlength="200"></label>
        <label>Pie de foto<input v-model="caption" maxlength="250"></label>
        <label class="chk"><input v-model="credit" type="checkbox"> Incluir crédito (autor, licencia y enlace a Commons) — recomendado por las licencias libres</label>
        <pre class="md" aria-label="Vista del Markdown">{{ markdown }}</pre>
        <button type="submit" class="ins" :disabled="!canInsert">Insertar en la página</button>
      </form>
    </div>
  </dialog>
</template>

<style scoped>
button { border: 1px solid #000; background: #fff; font: 600 0.8rem var(--font-body); cursor: pointer; padding: 2px var(--space-2); } button:hover:not(:disabled) { background: #000; color: #fff; } button:disabled { opacity: 0.4; cursor: default; }
.cfi { width: min(60rem, 96vw); max-height: 92vh; padding: 0; border: var(--border); overflow: auto; }
.cfi::backdrop { background: rgba(0, 0, 0, 0.5); }
.head { display: flex; justify-content: space-between; align-items: center; padding: var(--space-2) var(--space-4); background: var(--color-lilac); border-bottom: var(--border); } .head h2 { margin: 0; font-size: 1.1rem; }
.search { display: flex; gap: var(--space-2); padding: var(--space-3) var(--space-4); } .search input { flex: 1; padding: var(--space-2); border: var(--border); font: 0.9rem var(--font-body); }
.err { color: #b00; padding: 0 var(--space-4); font-weight: 600; }
.body { display: grid; grid-template-columns: 1.4fr 1fr; gap: var(--space-4); padding: 0 var(--space-4) var(--space-4); align-items: start; }
@media (max-width: 800px) { .body { grid-template-columns: 1fr; } }
.grid { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(auto-fill, minmax(8.5rem, 1fr)); gap: var(--space-2); }
.grid button { width: 100%; display: grid; gap: 2px; padding: var(--space-1); text-align: left; font-weight: 400; font-size: 0.7rem; background: #fff; } .grid button.sel { outline: 3px solid var(--color-accent-lilac); background: var(--color-bg-soft); }
.grid img { width: 100%; aspect-ratio: 1; object-fit: cover; background: var(--color-bg-soft); } .grid small { color: var(--color-text-muted); }
.more { margin-top: var(--space-3); padding: var(--space-1) var(--space-4); }
.detail { display: grid; gap: var(--space-2); position: sticky; top: 0; font-size: 0.8rem; } .prev { max-width: 100%; max-height: 12rem; object-fit: contain; border: var(--border); background: var(--color-bg-soft); justify-self: start; }
.meta { margin: 0; } label { display: grid; gap: 2px; font-weight: 600; } label input:not([type='checkbox']) { padding: var(--space-2); border: var(--border); font: 0.85rem var(--font-body); font-weight: 400; } .chk { display: flex; gap: var(--space-2); align-items: start; font-weight: 400; }
.md { margin: 0; padding: var(--space-2); background: var(--color-bg-soft); white-space: pre-wrap; word-break: break-all; font: 0.7rem/1.4 var(--font-mono); max-height: 8rem; overflow: auto; }
.ins { background: #000; color: #fff; padding: var(--space-2) var(--space-4); justify-self: start; }
</style>
