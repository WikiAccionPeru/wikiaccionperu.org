<script setup lang="ts">
import { parseMarkdown } from '@nuxtjs/mdc/runtime'

definePageMeta({ layout: 'default' })
useSeoMeta({ title: 'Editar — WikiAcción Perú', robots: 'noindex' })
const route = useRoute()
const path = computed(() => String(route.query.path ?? '/'))
const section = computed(() => (route.query.section ? String(route.query.section) : ''))
const { me, refresh } = useAuth()

const TECHNICAL = ['id', 'parent', 'menu_order', 'author', 'source_url', 'modified', 'featured_media', 'slug', 'wide']
const data = ref<Record<string, any>>({})
const body = ref('')
const original = ref('')
const composed = computed(() => { try { return joinDoc({ data: data.value, body: body.value }) } catch { return '' } })
const dirty = computed(() => !!original.value && composed.value !== original.value)
const status = ref<{ kind: 'info' | 'ok' | 'error'; msg: string }>({ kind: 'info', msg: '' })
const loading = ref(true)
const loadFailed = ref(false)
const isStructured = computed(() => !!data.value.home)
const techData = computed(() => Object.fromEntries(Object.entries(data.value).filter(([k]) => TECHNICAL.includes(k))))
const patch = (part: Record<string, any>, keys: string[]) => {
  const next = { ...data.value }
  keys.forEach((k) => delete next[k])
  data.value = { ...next, ...part }
}
const pageProps = computed({ get: () => data.value, set: (v) => (data.value = v) })

async function load() {
  loading.value = true
  try {
    const r = await adminFetch<{ text: string }>('/api/admin/page', { query: { path: path.value } })
    const d = splitDoc(r.text)
    data.value = d.data; body.value = d.body
    original.value = joinDoc(d)
    loadFailed.value = false; status.value = { kind: 'info', msg: '' }
  } catch (e: any) { loadFailed.value = true; status.value = { kind: 'error', msg: `No se pudo cargar la página: ${e.message}` } } finally { loading.value = false }
}
onMounted(async () => { await refresh(); if (me.value.admin) await load(); else loading.value = false })

async function save() {
  if (!dirty.value) return
  status.value = { kind: 'info', msg: 'Guardando…' }
  try {
    await adminFetch('/api/admin/page', { method: 'PUT', body: { path: path.value, text: composed.value } })
    original.value = composed.value
    status.value = { kind: 'ok', msg: 'Guardado. (En producción hay que publicar para que los visitantes lo vean.)' }
  } catch (e: any) { status.value = { kind: 'error', msg: e.message } }
}

// Preview of the Markdown body, rendered with the same MDC pipeline as the site.
const preview = shallowRef<{ body: any; data: any } | null>(null)
const previewError = ref('')
const previewBusy = ref(false)
let t: ReturnType<typeof setTimeout> | undefined
watch(body, (v) => {
  if (!v.trim()) { preview.value = null; return }
  clearTimeout(t)
  previewBusy.value = true
  t = setTimeout(async () => {
    try { const r = await parseMarkdown(v); preview.value = { body: r.body, data: r.data }; previewError.value = '' }
    catch (e: any) { previewError.value = e?.message ?? 'No se pudo generar la vista previa' }
    finally { previewBusy.value = false }
  }, 400)
})

const guard = (e: BeforeUnloadEvent) => { if (dirty.value) { e.preventDefault(); e.returnValue = '' } }
onMounted(() => window.addEventListener('beforeunload', guard))
onBeforeUnmount(() => window.removeEventListener('beforeunload', guard))
onBeforeRouteLeave(() => (dirty.value ? window.confirm('Hay cambios sin guardar. ¿Salir de todos modos?') : true))
watch([loading, section], async () => {
  if (loading.value || !section.value) return
  await nextTick()
  document.querySelector(`[data-section="${CSS.escape(section.value)}"]`)?.scrollIntoView({ block: 'start' })
})
</script>

<template>
  <div class="container pad">
    <AdminNav />
    <h1>Editar <code>{{ path }}</code><small v-if="section"> · sección «{{ section }}»</small></h1>
    <AdminGate>
      <div class="bar">
        <button type="button" class="save" :disabled="!dirty" @click="save">💾 Guardar</button>
        <NuxtLink :to="path">Ver página</NuxtLink>
        <span v-if="dirty" class="dirty">cambios sin guardar</span>
        <span v-if="status.msg" :class="['msg', status.kind]" role="status">{{ status.msg }}</span>
      </div>
      <p v-if="loading">Cargando…</p>
      <p v-else-if="loadFailed" class="msg error">No se abre el editor porque la página no se pudo cargar. <button type="button" @click="load">Reintentar</button></p>
      <template v-else>
        <section v-if="!section || !isStructured" class="panel">
          <h2>Propiedades</h2>
          <EditorPageProperties v-model="pageProps" :hide="TECHNICAL" />
          <details class="adv"><summary>Avanzado (datos técnicos)</summary>
            <EditorPageFieldTree :model-value="techData" @update:model-value="patch($event as any, Object.keys(techData))" />
          </details>
        </section>
        <section v-if="isStructured" class="panel">
          <h2>Secciones de la portada</h2>
          <EditorPageFieldTree :model-value="data.home" :open="section" @update:model-value="data = { ...data, home: $event as any }" />
        </section>
        <section v-if="!isStructured || body.trim()" class="panel">
          <h2>Contenido (Markdown)</h2>
          <ClientOnly>
            <EditorMarkdown v-model="body" @save="save">
              <template #tools="{ insertBlock }"><EditorCommonsFileInserter @insert="insertBlock" /></template>
            </EditorMarkdown>
          </ClientOnly>
          <h2>Vista previa</h2>
          <p v-if="previewError" class="msg error">{{ previewError }}</p>
          <div v-else class="prose preview"><MDCRenderer v-if="preview" :body="preview.body" :data="preview.data" /><p v-else><em>{{ previewBusy ? 'Generando vista previa… (la primera vez tarda unos segundos)' : 'Escribe para ver la vista previa.' }}</em></p></div>
        </section>
      </template>
    </AdminGate>
  </div>
</template>

<style scoped>
.pad { padding-block: var(--space-4) var(--space-6); }
h1 small { font-size: 1rem; color: var(--color-text-muted); }
.bar { display: flex; flex-wrap: wrap; gap: var(--space-3); align-items: center; margin-bottom: var(--space-3); position: sticky; top: var(--header-h); background: #fff; padding-block: var(--space-2); z-index: 5; }
.save { padding: var(--space-2) var(--space-4); border: 1px solid #000; background: #000; color: #fff; font: 600 0.9rem var(--font-body); cursor: pointer; }
.save:disabled { opacity: 0.4; cursor: default; }
.dirty { color: #a40; font-size: 0.85rem; }
.msg { font-size: 0.85rem; } .msg.ok { color: #060; } .msg.error { color: #b00; font-weight: 600; }
.panel { margin-bottom: var(--space-5); } .panel h2 { font-size: 1.15rem; }
.adv { margin-top: var(--space-3); } .adv summary { cursor: pointer; font-size: 0.85rem; color: var(--color-text-muted); }
.preview { border: var(--border); padding: var(--space-4); background: #fff; max-width: 52rem; }
</style>
