<script setup lang="ts">
useSeoMeta({ title: 'Menú — WikiAcción Perú', robots: 'noindex' })
type Item = { title: string; url: string; children: Item[] }
const { me, refresh } = useAuth()
const menu = ref<Item[]>([])
const original = ref('')
const pages = ref<{ path: string; title: string }[]>([])
const msg = ref<{ kind: 'ok' | 'error'; text: string }>()
const dirty = computed(() => !!original.value && JSON.stringify(menu.value) !== original.value)

onMounted(async () => {
  await refresh()
  if (!me.value.admin) return
  try {
    menu.value = (await adminFetch<Item[]>('/api/admin/menu')).map((i) => ({ ...i, children: i.children ?? [] }))
    original.value = JSON.stringify(menu.value)
    pages.value = await adminFetch('/api/admin/pages')
  } catch (e: any) { msg.value = { kind: 'error', text: e.message } }
})
const swap = (list: Item[], i: number, d: number) => { const j = i + d; if (j < 0 || j >= list.length) return; [list[i], list[j]] = [list[j], list[i]] }
const addTop = () => menu.value.push({ title: 'Nuevo elemento', url: '/', children: [] })
const addChild = (it: Item) => it.children.push({ title: 'Nuevo subelemento', url: '/', children: [] })
async function save() {
  try {
    const r = await adminFetch<{ items: number }>('/api/admin/menu', { method: 'PUT', body: menu.value })
    original.value = JSON.stringify(menu.value)
    msg.value = { kind: 'ok', text: `Menú guardado (${r.items} elementos).` }
  } catch (e: any) { msg.value = { kind: 'error', text: e.message } }
}
onBeforeRouteLeave(() => (dirty.value ? window.confirm('Hay cambios sin guardar. ¿Salir de todos modos?') : true))
</script>

<template>
  <div class="container pad">
    <AdminNav />
    <h1>Menú de la cabecera</h1>
    <AdminGate>
      <div class="bar">
        <button type="button" class="save" :disabled="!dirty" @click="save">💾 Guardar menú</button>
        <button type="button" @click="addTop">＋ Elemento</button>
        <span v-if="dirty" class="dirty">cambios sin guardar</span>
      </div>
      <p v-if="msg" :class="['msg', msg.kind]" role="status">{{ msg.text }}</p>
      <datalist id="pagelist"><option v-for="p in pages" :key="p.path" :value="p.path">{{ p.title }}</option></datalist>
      <ol class="menu">
        <li v-for="(it, i) in menu" :key="i">
          <div class="row">
            <input v-model="it.title" aria-label="Título" placeholder="Título">
            <input v-model="it.url" list="pagelist" aria-label="Dirección" placeholder="/ruta o https://…">
            <button type="button" aria-label="Subir" @click="swap(menu, i, -1)">↑</button>
            <button type="button" aria-label="Bajar" @click="swap(menu, i, 1)">↓</button>
            <button type="button" aria-label="Añadir subelemento" @click="addChild(it)">＋ sub</button>
            <button type="button" class="danger" aria-label="Quitar" @click="menu.splice(i, 1)">✕</button>
          </div>
          <ol v-if="it.children.length" class="sub">
            <li v-for="(c, j) in it.children" :key="j" class="row">
              <input v-model="c.title" aria-label="Título del subelemento" placeholder="Título">
              <input v-model="c.url" list="pagelist" aria-label="Dirección del subelemento" placeholder="/ruta o https://…">
              <button type="button" aria-label="Subir" @click="swap(it.children, j, -1)">↑</button>
              <button type="button" aria-label="Bajar" @click="swap(it.children, j, 1)">↓</button>
              <button type="button" class="danger" aria-label="Quitar" @click="it.children.splice(j, 1)">✕</button>
            </li>
          </ol>
        </li>
      </ol>
      <p class="hint">El menú se aplica a toda la cabecera. Los cambios se ven al recargar.</p>
    </AdminGate>
  </div>
</template>

<style scoped>
.pad { padding-block: var(--space-4) var(--space-6); }
.bar { display: flex; gap: var(--space-3); align-items: center; margin-bottom: var(--space-3); }
.msg { padding: var(--space-2) var(--space-3); border: var(--border); } .msg.ok { background: var(--color-green); } .msg.error { background: #fcc; font-weight: 600; }
.menu, .sub { list-style: none; padding: 0; margin: 0; display: grid; gap: var(--space-2); }
.sub { margin: var(--space-2) 0 var(--space-2) var(--space-5); }
.row { display: flex; gap: var(--space-2); align-items: center; } .row input { padding: var(--space-2); border: var(--border); font: 0.85rem var(--font-body); min-width: 0; } .row input:first-child { flex: 1 1 14rem; } .row input:nth-child(2) { flex: 2 1 18rem; }
button { border: 1px solid #000; background: #fff; cursor: pointer; font: 600 0.8rem var(--font-body); padding: var(--space-1) var(--space-2); } button:hover { background: #000; color: #fff; } .danger:hover { background: #b00; border-color: #b00; }
.save { background: #000; color: #fff; padding: var(--space-2) var(--space-4); } .save:disabled { opacity: 0.4; cursor: default; } .dirty { color: #a40; font-size: 0.85rem; } .hint { color: var(--color-text-muted); font-size: 0.85rem; }
</style>
