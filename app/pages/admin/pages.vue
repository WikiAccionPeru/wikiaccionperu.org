<script setup lang="ts">
useSeoMeta({ title: 'Páginas — WikiAcción Perú', robots: 'noindex' })
type Page = { path: string; title: string; type: string; date: string }
const { me, refresh } = useAuth()
const router = useRouter() // grabbed at setup: navigateTo() loses its Nuxt context after an await
const pages = ref<Page[]>([])
const loading = ref(true)
const q = ref('')
const typeFilter = ref('')
const msg = ref<{ kind: 'ok' | 'error'; text: string }>()
const moving = ref('')
const moveTo = ref('')
const nw = reactive({ path: '', title: '', type: 'page' as 'page' | 'post' })

const norm = (s: string) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()
const shown = computed(() => pages.value.filter((p) => (!typeFilter.value || p.type === typeFilter.value) && (!q.value || norm(`${p.title} ${p.path}`).includes(norm(q.value)))).slice(0, 200))
const types = computed(() => [...new Set(pages.value.map((p) => p.type))].sort())

async function load() {
  loading.value = true
  try { pages.value = await adminFetch<Page[]>('/api/admin/pages') } catch (e: any) { msg.value = { kind: 'error', text: e.message } } finally { loading.value = false }
}
onMounted(async () => { await refresh(); if (me.value.admin) await load(); else loading.value = false })

const run = async (fn: () => Promise<unknown>, ok: string) => {
  try { await fn(); msg.value = { kind: 'ok', text: ok }; await load() } catch (e: any) { msg.value = { kind: 'error', text: e.message } }
}
const create = () => run(async () => {
  const r = await adminFetch<{ path: string }>('/api/admin/pages', { method: 'POST', body: { ...nw } })
  Object.assign(nw, { path: '', title: '', type: 'page' })
  await router.push({ path: '/admin/edit/', query: { path: r.path } })
}, 'Página creada.')
const move = (from: string) => run(async () => {
  await adminFetch('/api/admin/pages/move', { method: 'POST', body: { from, to: moveTo.value } })
  moving.value = ''
}, `Movida a ${moveTo.value}. Se creará una redirección desde la dirección antigua al publicar.`)
const del = (p: Page) => {
  if (!window.confirm(`¿Eliminar «${p.title}» (${p.path})?\n\nSe moverá a la papelera (content/.trash) y se podrá recuperar.`)) return
  return run(() => adminFetch('/api/admin/pages/delete', { method: 'POST', body: { path: p.path } }), 'Página eliminada (en la papelera).')
}
</script>

<template>
  <div class="container pad">
    <AdminNav />
    <h1>Páginas</h1>
    <AdminGate>
      <p v-if="msg" :class="['msg', msg.kind]" role="status">{{ msg.text }}</p>
      <form class="new" @submit.prevent="create">
        <h2>Nueva página</h2>
        <label>Título <input v-model="nw.title" required maxlength="300"></label>
        <label>Dirección <input v-model="nw.path" required placeholder="/mi-nueva-pagina" pattern="^/[a-z0-9]+(-[a-z0-9]+)*(/[a-z0-9]+(-[a-z0-9]+)*){0,3}$" title="Minúsculas, números y guiones; empieza con /; hasta 4 niveles"></label>
        <label>Tipo <select v-model="nw.type"><option value="page">Página</option><option value="post">Noticia</option></select></label>
        <button type="submit">Crear y editar</button>
      </form>
      <div class="filters">
        <input v-model="q" type="search" placeholder="Filtrar por título o dirección…" aria-label="Filtrar">
        <select v-model="typeFilter" aria-label="Tipo"><option value="">Todos los tipos</option><option v-for="t in types" :key="t" :value="t">{{ t }}</option></select>
        <span class="count">{{ shown.length }} de {{ pages.length }}</span>
      </div>
      <p v-if="loading">Cargando…</p>
      <table v-else>
        <thead><tr><th>Título</th><th>Dirección</th><th>Tipo</th><th>Acciones</th></tr></thead>
        <tbody>
          <template v-for="p in shown" :key="p.path">
            <tr>
              <td><span v-html="p.title" /></td>
              <td><NuxtLink :to="p.path">{{ p.path }}</NuxtLink></td>
              <td>{{ p.type }}</td>
              <td class="act">
                <NuxtLink :to="{ path: '/admin/edit/', query: { path: p.path } }">Editar</NuxtLink>
                <button v-if="p.path !== '/'" type="button" @click="moving = moving === p.path ? '' : p.path; moveTo = p.path">Mover</button>
                <button v-if="p.path !== '/'" type="button" class="danger" @click="del(p)">Eliminar</button>
              </td>
            </tr>
            <tr v-if="moving === p.path" class="moverow"><td colspan="4">
              <form @submit.prevent="move(p.path)">Nueva dirección: <input v-model="moveTo" required pattern="^/[a-z0-9]+(-[a-z0-9]+)*(/[a-z0-9]+(-[a-z0-9]+)*){0,3}$" title="Minúsculas, números y guiones; empieza con /"> <button type="submit">Mover</button> <button type="button" @click="moving = ''">Cancelar</button></form>
            </td></tr>
          </template>
        </tbody>
      </table>
    </AdminGate>
  </div>
</template>

<style scoped>
.pad { padding-block: var(--space-4) var(--space-6); }
.msg { padding: var(--space-2) var(--space-3); border: var(--border); } .msg.ok { background: var(--color-green); } .msg.error { background: #fcc; font-weight: 600; }
.new { display: grid; grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr)); gap: var(--space-3); align-items: end; border: var(--border); padding: var(--space-3) var(--space-4); background: var(--color-bg-soft); margin-bottom: var(--space-4); }
.new h2 { grid-column: 1 / -1; margin: 0; font-size: 1.1rem; }
label { display: grid; gap: 2px; font-size: 0.8rem; font-weight: 600; }
input, select { padding: var(--space-2); border: var(--border); font: 0.9rem var(--font-body); background: #fff; border-radius: 0; }
button { border: 1px solid #000; background: #fff; cursor: pointer; font: 600 0.8rem var(--font-body); padding: var(--space-1) var(--space-3); }
button:hover { background: #000; color: #fff; } button.danger:hover { background: #b00; border-color: #b00; }
.filters { display: flex; gap: var(--space-3); align-items: center; margin-bottom: var(--space-3); flex-wrap: wrap; } .filters input { flex: 1; min-width: 14rem; } .count { font-size: 0.8rem; color: var(--color-text-muted); }
table { width: 100%; border-collapse: collapse; font-size: 0.85rem; } th, td { border-bottom: 1px solid var(--color-border); padding: var(--space-2); text-align: left; vertical-align: top; }
.act { display: flex; gap: var(--space-2); flex-wrap: wrap; } .moverow td { background: var(--color-bg-soft); }
</style>
