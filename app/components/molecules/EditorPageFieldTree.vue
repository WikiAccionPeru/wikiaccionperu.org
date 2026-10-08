<script setup lang="ts">
/** Generic form for a JSON-like value (strings, numbers, booleans, lists, nested objects): the structured-settings editor. */
const props = defineProps<{ modelValue: unknown; label?: string; hide?: string[]; open?: string }>()
const emit = defineEmits<{ 'update:modelValue': [unknown] }>()
const LABELS: Record<string, string> = {
  title: 'Título', date: 'Fecha', modified: 'Modificado', excerpt: 'Resumen', status: 'Estado', type: 'Tipo', slug: 'Dirección (slug)',
  taxonomies: 'Categorías y etiquetas (slugs)', category: 'Categorías', post_tag: 'Etiquetas', enfoque_tematico: 'Enfoque temático',
  home: 'Secciones de la portada', hero: 'Portada (hero)', features: 'Tarjetas de líneas de acción', thematic: '«¿No sabes sobre qué editar?»',
  partnersTitle: 'Título de «organizaciones»', kicker: 'Antetítulo', text: 'Texto', image: 'Imagen', buttons: 'Botones', label: 'Etiqueta', to: 'Enlace',
  icon: 'Icono', list: 'Lista', cta: 'Llamada a la acción', id: 'id', parent: 'Padre', menu_order: 'Orden', author: 'Autor', source_url: 'URL original', featured_media: 'Imagen destacada (id)', wide: 'Página a ancho completo',
}
const nice = (k: string) => LABELS[k] ?? k
const isObj = (v: unknown): v is Record<string, unknown> => !!v && typeof v === 'object' && !Array.isArray(v)
const set = (k: string, v: unknown) => emit('update:modelValue', { ...(props.modelValue as object), [k]: v })
const setAt = (i: number, v: unknown) => { const a = [...(props.modelValue as unknown[])]; a[i] = v; emit('update:modelValue', a) }
const move = (i: number, d: number) => { const a = [...(props.modelValue as unknown[])]; const j = i + d; if (j < 0 || j >= a.length) return; [a[i], a[j]] = [a[j], a[i]]; emit('update:modelValue', a) }
const remove = (i: number) => emit('update:modelValue', (props.modelValue as unknown[]).filter((_, x) => x !== i))
const blank = (like: unknown): unknown => (isObj(like) ? Object.fromEntries(Object.keys(like).map((k) => [k, blank(like[k])])) : Array.isArray(like) ? [] : typeof like === 'number' ? 0 : typeof like === 'boolean' ? false : '')
const add = () => { const a = props.modelValue as unknown[]; emit('update:modelValue', [...a, a.length ? blank(a[a.length - 1]) : '']) }
const keys = computed(() => (isObj(props.modelValue) ? Object.keys(props.modelValue).filter((k) => !props.hide?.includes(k)) : []))
const long = (v: unknown) => typeof v === 'string' && (v.length > 70 || v.includes('\n'))
</script>

<template>
  <div class="ft">
    <template v-if="isObj(modelValue)">
      <template v-for="k in keys" :key="k">
        <details v-if="isObj(modelValue[k]) || Array.isArray(modelValue[k])" class="group" :open="open === k || !open" :data-section="k">
          <summary>{{ nice(k) }}</summary>
          <EditorPageFieldTree :model-value="modelValue[k]" @update:model-value="set(k, $event)" />
        </details>
        <EditorPageFieldTree v-else :model-value="modelValue[k]" :label="nice(k)" @update:model-value="set(k, $event)" />
      </template>
    </template>
    <template v-else-if="Array.isArray(modelValue)">
      <div v-for="(item, i) in modelValue" :key="i" class="item">
        <div class="ctl">
          <span>#{{ i + 1 }}</span>
          <button type="button" aria-label="Subir" @click="move(i, -1)">↑</button>
          <button type="button" aria-label="Bajar" @click="move(i, 1)">↓</button>
          <button type="button" aria-label="Quitar" @click="remove(i)">✕</button>
        </div>
        <EditorPageFieldTree :model-value="item" @update:model-value="setAt(i, $event)" />
      </div>
      <button type="button" class="add" @click="add">＋ Añadir</button>
    </template>
    <label v-else-if="typeof modelValue === 'boolean'" class="row"><input type="checkbox" :checked="modelValue" @change="emit('update:modelValue', ($event.target as HTMLInputElement).checked)"> {{ label }}</label>
    <label v-else-if="typeof modelValue === 'number'" class="row"><span>{{ label }}</span><input type="number" :value="modelValue" @input="emit('update:modelValue', Number(($event.target as HTMLInputElement).value))"></label>
    <label v-else class="row"><span v-if="label">{{ label }}</span>
      <textarea v-if="long(modelValue)" :value="String(modelValue ?? '')" rows="4" @input="emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)" />
      <input v-else type="text" :value="String(modelValue ?? '')" @input="emit('update:modelValue', ($event.target as HTMLInputElement).value)">
    </label>
  </div>
</template>

<style scoped>
.ft { display: grid; gap: var(--space-2); }
.row { display: grid; gap: 2px; font-size: 0.8rem; }
.row span { font-weight: 600; }
input[type='text'], input[type='number'], textarea { width: 100%; padding: var(--space-2); border: var(--border); font: 0.9rem var(--font-body); border-radius: 0; background: #fff; }
.group { border: var(--border); padding: var(--space-2) var(--space-3); background: #fff; }
.group > summary { cursor: pointer; font: 600 0.95rem var(--font-heading); }
.group[open] > summary { margin-bottom: var(--space-2); }
.item { border-left: 4px solid var(--color-accent-lilac); padding-left: var(--space-3); display: grid; gap: var(--space-2); }
.ctl { display: flex; gap: var(--space-1); align-items: center; font-size: 0.75rem; color: var(--color-text-muted); }
button { border: 1px solid #000; background: #fff; cursor: pointer; font: 600 0.75rem var(--font-body); padding: 0 var(--space-2); }
button:hover { background: #000; color: #fff; }
.add { justify-self: start; padding: 2px var(--space-3); }
</style>
