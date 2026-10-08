<script setup lang="ts">
useSeoMeta({ title: 'Editores — WikiAcción Perú', robots: 'noindex' })
type Row = { username: string; id: string | null; resolvedId: string | null }
const { me, refresh } = useAuth()
const rely = ref(true)
const rows = ref<Row[]>([])
const original = ref('')
const msg = ref<{ kind: 'ok' | 'error'; text: string }>()
const newName = ref('')
const dirty = computed(() => !!original.value && JSON.stringify({ rely: rely.value, r: rows.value.map((r) => [r.username, r.id]) }) !== original.value)
const snapshot = () => (original.value = JSON.stringify({ rely: rely.value, r: rows.value.map((r) => [r.username, r.id]) }))

async function load() {
  const r = await adminFetch<{ relyOnUsername: boolean; admins: Row[] }>('/api/admin/editors')
  rely.value = r.relyOnUsername; rows.value = r.admins; snapshot()
}
onMounted(async () => { await refresh(); if (me.value.admin) await load().catch((e) => (msg.value = { kind: 'error', text: e.message })) })

// "username → id" helper
const helperInput = ref('')
const helperOut = ref<{ name: string; id: string | null }[]>([])
const helperInvalid = ref<string[]>([])
async function resolve() {
  try {
    const r = await adminFetch<{ ids: Record<string, string | null>; invalid: string[] }>('/api/admin/resolve-users', { query: { names: helperInput.value } })
    helperOut.value = Object.entries(r.ids).map(([name, id]) => ({ name, id })); helperInvalid.value = r.invalid
  } catch (e: any) { msg.value = { kind: 'error', text: e.message } }
}
async function add() {
  const n = newName.value.trim(); if (!n) return
  try {
    const r = await adminFetch<{ ids: Record<string, string | null> }>('/api/admin/resolve-users', { query: { names: n } })
    const [name, id] = Object.entries(r.ids)[0] ?? []
    if (!name || !id) throw new Error(`No existe ninguna cuenta llamada «${n}» en Wikimedia Commons`)
    if (rows.value.some((x) => x.username.toLowerCase() === name.toLowerCase())) throw new Error(`«${name}» ya está en la lista`)
    rows.value.push({ username: name, id, resolvedId: id }); newName.value = ''; msg.value = undefined
  } catch (e: any) { msg.value = { kind: 'error', text: e.message } }
}
async function save() {
  try {
    await adminFetch('/api/admin/editors', { method: 'PUT', body: { relyOnUsername: rely.value, admins: rows.value.map((r) => ({ username: r.username, id: r.id ?? r.resolvedId })) } })
    msg.value = { kind: 'ok', text: 'Lista de editores guardada.' }
    await load()
  } catch (e: any) { msg.value = { kind: 'error', text: e.message } }
}
onBeforeRouteLeave(() => (dirty.value ? window.confirm('Hay cambios sin guardar. ¿Salir de todos modos?') : true))
</script>

<template>
  <div class="container pad">
    <AdminNav />
    <h1>Editores</h1>
    <AdminGate>
      <p v-if="msg" :class="['msg', msg.kind]" role="status">{{ msg.text }}</p>
      <label class="rely"><input v-model="rely" type="checkbox"> Basta con el nombre de usuario <small>(el sitio consulta el id de cada cuenta en Wikimedia Commons)</small></label>
      <table>
        <thead><tr><th>Usuario</th><th>Id</th><th /></tr></thead>
        <tbody>
          <tr v-for="(r, i) in rows" :key="r.username">
            <td>{{ r.username }} <em v-if="r.username === me.user?.username">(tú)</em></td>
            <td>
              <template v-if="r.resolvedId">{{ r.resolvedId }}</template>
              <span v-else class="bad">no existe en Commons</span>
              <small v-if="!rely && r.id && r.resolvedId && r.id !== r.resolvedId" class="bad"> · el id guardado ({{ r.id }}) no coincide</small>
            </td>
            <td><button type="button" class="danger" @click="rows.splice(i, 1)">Quitar</button></td>
          </tr>
        </tbody>
      </table>
      <form class="add" @submit.prevent="add"><input v-model="newName" placeholder="Nombre de usuario de Wikimedia" aria-label="Nuevo editor"> <button type="submit">＋ Añadir</button></form>
      <div class="bar"><button type="button" class="save" :disabled="!dirty" @click="save">💾 Guardar lista</button> <span v-if="dirty" class="dirty">cambios sin guardar</span></div>

      <h2>Utilidad «usuario → id»</h2>
      <p class="hint">Para obtener el id de una o varias cuentas (uno por línea o separados por «|»).</p>
      <textarea v-model="helperInput" rows="3" placeholder="Yug&#10;Jesedmateo" aria-label="Nombres" />
      <p><button type="button" :disabled="!helperInput.trim()" @click="resolve">Buscar ids</button></p>
      <table v-if="helperOut.length"><tbody><tr v-for="o in helperOut" :key="o.name"><td>{{ o.name }}</td><td>{{ o.id ?? 'no existe' }}</td><td><code v-if="o.id">{{ o.name }} | {{ o.id }}</code></td></tr></tbody></table>
      <p v-if="helperInvalid.length" class="bad">Nombres no válidos: {{ helperInvalid.join(', ') }}</p>
    </AdminGate>
  </div>
</template>

<style scoped>
.pad { padding-block: var(--space-4) var(--space-6); }
.msg { padding: var(--space-2) var(--space-3); border: var(--border); } .msg.ok { background: var(--color-green); } .msg.error { background: #fcc; font-weight: 600; }
.rely { display: block; margin-bottom: var(--space-3); } small { color: var(--color-text-muted); }
table { width: 100%; max-width: 46rem; border-collapse: collapse; font-size: 0.85rem; margin-bottom: var(--space-3); } th, td { border-bottom: 1px solid var(--color-border); padding: var(--space-2); text-align: left; }
.bad { color: #b00; } .add { display: flex; gap: var(--space-2); margin-bottom: var(--space-3); } .add input, textarea { padding: var(--space-2); border: var(--border); font: 0.9rem var(--font-body); } .add input { flex: 1; max-width: 24rem; } textarea { width: 100%; max-width: 24rem; }
button { border: 1px solid #000; background: #fff; cursor: pointer; font: 600 0.8rem var(--font-body); padding: var(--space-1) var(--space-3); } button:hover { background: #000; color: #fff; } .danger:hover { background: #b00; border-color: #b00; }
.save { background: #000; color: #fff; padding: var(--space-2) var(--space-4); } .save:disabled, button:disabled { opacity: 0.4; cursor: default; } .dirty { color: #a40; font-size: 0.85rem; margin-left: var(--space-3); } .hint { color: var(--color-text-muted); font-size: 0.85rem; }
</style>
