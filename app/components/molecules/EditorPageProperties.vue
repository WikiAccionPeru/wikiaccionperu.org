<script setup lang="ts">
import taxonomies from '~~/data/taxonomies.json'

type Tax = { prefix: string; types: string[]; terms: { slug: string; name: string }[] }
const TAX = taxonomies as Record<string, Tax>
const TAX_LABEL: Record<string, string> = { category: 'Categorías', post_tag: 'Etiquetas', enfoque_tematico: 'Enfoque temático', tipo_recurso: 'Tipo de recurso', tipo_alianza: 'Tipo de alianza' }
const TYPES: [string, string][] = [['page', 'Página'], ['post', 'Noticia'], ['recurso', 'Recurso'], ['alianza', 'Alianza'], ['nota', 'Nota en medios']]
const STATUS: [string, string][] = [['publish', 'Publicado'], ['draft', 'Borrador — oculto en listados y buscador']]
const KNOWN = ['title', 'type', 'status', 'date', 'excerpt', 'taxonomies']

const props = defineProps<{ modelValue: Record<string, any>; hide: string[] }>()
const emit = defineEmits<{ 'update:modelValue': [Record<string, any>] }>()
const set = (k: string, v: unknown) => emit('update:modelValue', { ...props.modelValue, [k]: v })
const applicable = computed(() => Object.entries(TAX).filter(([, t]) => t.types.includes(props.modelValue.type)))
const setTax = (name: string, slugs: string[]) => {
  const next = { ...(props.modelValue.taxonomies ?? {}), [name]: slugs }
  if (!slugs.length) delete next[name]
  set('taxonomies', next)
}
// <input type="datetime-local"> wants "YYYY-MM-DDTHH:mm:ss"
const dateValue = computed(() => String(props.modelValue.date ?? '').slice(0, 19))
const onDate = (v: string) => set('date', v.length === 16 ? v + ':00' : v)
const others = computed(() => Object.fromEntries(Object.entries(props.modelValue).filter(([k]) => !KNOWN.includes(k) && !props.hide.includes(k) && k !== 'home')))
const setOthers = (v: Record<string, any>) => {
  const next: Record<string, any> = {}
  for (const [k, val] of Object.entries(props.modelValue)) if (KNOWN.includes(k) || props.hide.includes(k) || k === 'home') next[k] = val
  emit('update:modelValue', { ...next, ...v })
}
const typeChanged = (t: string) => {
  // a taxonomy that does not apply to the new type would be silently ignored by the site: drop it
  const keep = Object.fromEntries(Object.entries(props.modelValue.taxonomies ?? {}).filter(([n]) => TAX[n]?.types.includes(t)))
  emit('update:modelValue', { ...props.modelValue, type: t, taxonomies: keep })
}
const typeOptions = computed(() => (TYPES.some(([v]) => v === props.modelValue.type) ? TYPES : [...TYPES, [props.modelValue.type, props.modelValue.type] as [string, string]]))
</script>

<template>
  <div class="pp">
    <label class="f wide"><span>Título</span><input type="text" :value="modelValue.title" maxlength="300" @input="set('title', ($event.target as HTMLInputElement).value)"></label>
    <label class="f"><span>Tipo de contenido</span>
      <select :value="modelValue.type" @change="typeChanged(($event.target as HTMLSelectElement).value)"><option v-for="[v, l] in typeOptions" :key="v" :value="v">{{ l }}</option></select>
    </label>
    <label class="f"><span>Estado</span>
      <select :value="modelValue.status" @change="set('status', ($event.target as HTMLSelectElement).value)"><option v-for="[v, l] in STATUS" :key="v" :value="v">{{ l }}</option></select>
    </label>
    <label class="f"><span>Fecha de publicación</span><input type="datetime-local" step="1" :value="dateValue" @input="onDate(($event.target as HTMLInputElement).value)"></label>
    <label class="f wide"><span>Resumen</span><textarea rows="3" :value="modelValue.excerpt ?? ''" @input="set('excerpt', ($event.target as HTMLTextAreaElement).value)" /></label>
    <div v-if="applicable.length" class="tax wide">
      <EditorTermPicker v-for="[name, t] in applicable" :key="name" :label="TAX_LABEL[name] ?? name" :terms="t.terms" :model-value="modelValue.taxonomies?.[name] ?? []" @update:model-value="setTax(name, $event)" />
    </div>
    <p v-else class="hint wide">Este tipo de contenido no usa categorías ni etiquetas.</p>
    <div v-if="Object.keys(others).length" class="wide"><EditorPageFieldTree :model-value="others" @update:model-value="setOthers($event as any)" /></div>
  </div>
</template>

<style scoped>
.pp { display: grid; grid-template-columns: repeat(auto-fit, minmax(15rem, 1fr)); gap: var(--space-3); }
.wide { grid-column: 1 / -1; }
.f { display: grid; gap: 2px; font-size: 0.8rem; align-content: start; } .f span { font-weight: 600; }
input[type='text'], input[type='datetime-local'], select, textarea { width: 100%; padding: var(--space-2); border: var(--border); font: 0.9rem var(--font-body); border-radius: 0; background: #fff; }
.tax { display: grid; gap: var(--space-3); } .hint { color: var(--color-text-muted); font-size: 0.85rem; margin: 0; }
</style>
