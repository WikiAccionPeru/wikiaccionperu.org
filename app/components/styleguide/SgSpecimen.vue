<script setup lang="ts">
/**
 * One component in the styleguide: its name, kind, props, and a BOUNDED live demo.
 * Nothing may be oversized: a normal demo is capped at `maxHeight` (scrolls). A full-width section sets `design`
 * (the width it is designed for, e.g. 1440): it is shown at a constant, readable `maxScale`; its layout width is the
 * design width, or less when the frame is narrow (so a phone shows the responsive layout, not an unreadable speck).
 * The frame takes the measured height of the shrunken result.
 */
const props = withDefaults(defineProps<{
  name: string
  kind: 'átomo' | 'molécula' | 'organismo' | 'contenido' | 'layout'
  note?: string
  props?: string
  design?: number // full-width section: lay out at this width (px) and shrink
  maxScale?: number
  maxHeight?: number
  height?: number // fixed height (non-scaled demos only)
  visible?: boolean // let popups (dropdown menus) escape the frame
  compact?: boolean // squeeze tall widgets (editor) for the demo
  maxWidth?: string
}>(), { maxScale: 0.55, maxHeight: 360, maxWidth: '100%' })

const frame = ref<HTMLElement>()
const inner = ref<HTMLElement>()
const k = props.maxScale
const layoutW = ref(props.design ?? 0)
const measured = ref<number>()
const fit = () => {
  if (!props.design || !frame.value || !inner.value) return
  layoutW.value = Math.round(Math.min(props.design, frame.value.clientWidth / k))
  measured.value = Math.ceil(inner.value.offsetHeight * k)
}
let ro: ResizeObserver | undefined
onMounted(() => {
  if (!props.design) return
  ro = new ResizeObserver(fit)
  ro.observe(frame.value!); ro.observe(inner.value!)
  fit()
})
onBeforeUnmount(() => ro?.disconnect())

const style = computed(() => {
  const s: Record<string, string> = { maxWidth: props.maxWidth }
  if (props.design) s.height = Math.min(measured.value ?? props.maxHeight, props.maxHeight) + 'px'
  else if (props.height) s.height = props.height + 'px'
  else s.maxHeight = props.maxHeight + 'px'
  return s
})
const innerStyle = computed(() => (props.design ? { width: `${layoutW.value}px`, transform: `scale(${k})`, transformOrigin: '0 0' } : undefined))
</script>

<template>
  <figure :id="`c-${name}`" class="sg-spec">
    <figcaption>
      <h3><code>&lt;{{ name }} /&gt;</code> <span class="kind">{{ kind }}</span></h3>
      <p v-if="note" class="note">{{ note }}</p>
      <p v-if="props.props" class="sig"><code>{{ props.props }}</code></p>
    </figcaption>
    <div ref="frame" class="sg-frame" :class="{ visible: visible && !design, compact, scaled: !!design }" :style="style">
      <div ref="inner" class="scaler" :style="innerStyle"><slot /></div>
    </div>
  </figure>
</template>

<style scoped>
.sg-spec { margin: 0 0 var(--space-5); }
h3 { margin: 0 0 var(--space-1); font-size: 1rem; display: flex; gap: var(--space-2); align-items: baseline; flex-wrap: wrap; }
.kind { font: 600 0.7rem var(--font-body); text-transform: uppercase; background: var(--color-accent-lilac); padding: 0 var(--space-2); }
.note { margin: 0 0 var(--space-1); font-size: 0.85rem; color: var(--color-text-muted); }
.sig { margin: 0 0 var(--space-2); font-size: 0.75rem; word-break: break-word; }
.sig code { background: var(--color-bg-soft); padding: 1px var(--space-1); }
.sg-frame { border: 1px dashed var(--color-text-muted); background: #fff; overflow: auto; position: relative; contain: paint; }
.sg-frame.scaled { overflow: hidden; }
.sg-frame.visible { overflow: visible; contain: none; }
.sg-frame.compact :deep(.cm-editor) { min-height: 7rem; max-height: 11rem; }
.scaler { padding: var(--space-3); }
.sg-frame.scaled .scaler { padding: 0; }
</style>
