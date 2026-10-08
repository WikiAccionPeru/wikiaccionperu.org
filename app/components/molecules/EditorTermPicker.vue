<script setup lang="ts">
/** Closed-list picker: few options → checkboxes; many options → type-ahead over the existing terms only. */
type Term = { slug: string; name: string }
const props = defineProps<{ label: string; terms: Term[]; modelValue: string[] }>()
const emit = defineEmits<{ 'update:modelValue': [string[]] }>()
const selected = computed(() => props.modelValue ?? [])
const nameOf = (slug: string) => (props.terms.find((t) => t.slug === slug)?.name ?? slug).replace(/&amp;/g, '&')
const known = (slug: string) => props.terms.some((t) => t.slug === slug)
const toggle = (slug: string) => emit('update:modelValue', selected.value.includes(slug) ? selected.value.filter((s) => s !== slug) : [...selected.value, slug])

const small = computed(() => props.terms.length <= 12)
const q = ref('')
const open = ref(false)
const active = ref(0)
const norm = (s: string) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()
const matches = computed(() => {
  const n = norm(q.value)
  return props.terms.filter((t) => !selected.value.includes(t.slug) && (!n || norm(t.name).includes(n) || t.slug.includes(n))).slice(0, 12)
})
const pick = (slug: string) => { toggle(slug); q.value = ''; active.value = 0 }
const onKey = (e: KeyboardEvent) => {
  if (e.key === 'ArrowDown') { active.value = Math.min(active.value + 1, matches.value.length - 1); e.preventDefault() }
  else if (e.key === 'ArrowUp') { active.value = Math.max(active.value - 1, 0); e.preventDefault() }
  else if (e.key === 'Enter') { const m = matches.value[active.value]; if (m) { pick(m.slug); e.preventDefault() } }
  else if (e.key === 'Escape') open.value = false
}
watch(q, () => { active.value = 0; open.value = true })
const uid = useId()
</script>

<template>
  <fieldset class="tp">
    <legend>{{ label }}</legend>
    <div v-if="small" class="checks">
      <label v-for="t in terms" :key="t.slug"><input type="checkbox" :checked="selected.includes(t.slug)" @change="toggle(t.slug)"> {{ t.name.replace(/&amp;/g, '&') }}</label>
    </div>
    <template v-else>
      <ul class="chips" aria-label="Seleccionadas">
        <li v-for="s in selected" :key="s" :class="{ unknown: !known(s) }">
          {{ nameOf(s) }}<span v-if="!known(s)" title="Esta etiqueta ya no existe en el sitio"> ⚠</span>
          <button type="button" :aria-label="`Quitar ${nameOf(s)}`" @click="toggle(s)">✕</button>
        </li>
        <li v-if="!selected.length" class="none">Ninguna</li>
      </ul>
      <div class="combo">
        <input :id="uid" v-model="q" type="text" role="combobox" aria-autocomplete="list" :aria-expanded="open && matches.length > 0" :aria-controls="`${uid}-list`" placeholder="Buscar y añadir…" autocomplete="off" @focus="open = true" @blur="open = false" @keydown="onKey">
        <ul v-show="open && matches.length" :id="`${uid}-list`" role="listbox">
          <li v-for="(m, i) in matches" :key="m.slug" role="option" :aria-selected="i === active" :class="{ on: i === active }" @mousedown.prevent="pick(m.slug)">{{ m.name.replace(/&amp;/g, '&') }}</li>
        </ul>
      </div>
    </template>
  </fieldset>
</template>

<style scoped>
.tp { border: var(--border); padding: var(--space-2) var(--space-3); margin: 0; background: #fff; }
legend { font: 600 0.8rem var(--font-body); padding: 0 var(--space-1); }
.checks { display: flex; flex-wrap: wrap; gap: var(--space-2) var(--space-4); font-size: 0.85rem; }
.chips { list-style: none; margin: 0 0 var(--space-2); padding: 0; display: flex; flex-wrap: wrap; gap: var(--space-1); }
.chips li { background: var(--color-bg-soft); border: 1px solid var(--color-border); padding: 0 var(--space-2); font-size: 0.8rem; display: inline-flex; gap: var(--space-1); align-items: center; }
.chips .unknown { background: #fde; } .chips .none { color: var(--color-text-muted); border: 0; background: none; }
.chips button { border: 0; background: none; cursor: pointer; font-size: 0.75rem; padding: 0 2px; } .chips button:hover { color: #b00; }
.combo { position: relative; max-width: 24rem; }
.combo input { width: 100%; padding: var(--space-2); border: var(--border); font: 0.85rem var(--font-body); border-radius: 0; }
.combo ul { position: absolute; z-index: 20; left: 0; right: 0; margin: 0; padding: 0; list-style: none; background: #fff; border: var(--border); max-height: 14rem; overflow: auto; }
.combo li { padding: var(--space-1) var(--space-2); font-size: 0.85rem; cursor: pointer; } .combo li.on, .combo li:hover { background: var(--color-accent-lilac); }
</style>
