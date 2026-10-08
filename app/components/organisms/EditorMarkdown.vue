<script setup lang="ts">
import { EditorState } from '@codemirror/state'
import { EditorView, keymap, lineNumbers, highlightActiveLine } from '@codemirror/view'
import { defaultKeymap, history, historyKeymap, indentWithTab } from '@codemirror/commands'
import { markdown } from '@codemirror/lang-markdown'
import { syntaxHighlighting, defaultHighlightStyle } from '@codemirror/language'

const model = defineModel<string>({ default: '' })
const emit = defineEmits<{ save: [] }>()
const host = ref<HTMLElement>()
let view: EditorView | undefined

onMounted(() => {
  view = new EditorView({
    parent: host.value!,
    state: EditorState.create({
      doc: model.value,
      extensions: [
        lineNumbers(), highlightActiveLine(), history(), markdown(), syntaxHighlighting(defaultHighlightStyle), EditorView.lineWrapping,
        keymap.of([{ key: 'Mod-s', preventDefault: true, run: () => (emit('save'), true) }, indentWithTab, ...defaultKeymap, ...historyKeymap]),
        EditorView.updateListener.of((u) => { if (u.docChanged) model.value = u.state.doc.toString() }),
      ],
    }),
  })
})
onBeforeUnmount(() => view?.destroy())
// External changes (e.g. after loading the file) replace the document.
watch(model, (v) => {
  if (view && v !== view.state.doc.toString()) view.dispatch({ changes: { from: 0, to: view.state.doc.length, insert: v } })
})

/** Wraps the selection (or inserts a placeholder) — the toolbar's building block. */
function wrap(before: string, after = before, placeholder = 'texto') {
  if (!view) return
  const { from, to } = view.state.selection.main
  const sel = view.state.sliceDoc(from, to) || placeholder
  view.dispatch({ changes: { from, to, insert: before + sel + after }, selection: { anchor: from + before.length, head: from + before.length + sel.length } })
  view.focus()
}
function linePrefix(prefix: string) {
  if (!view) return
  const line = view.state.doc.lineAt(view.state.selection.main.from)
  view.dispatch({ changes: { from: line.from, insert: prefix } })
  view.focus()
}
/** Inserts a block at the cursor, on its own lines (used by components such as the Commons inserter). */
function insertBlock(text: string) {
  if (!view) return
  const { from, to } = view.state.selection.main
  view.dispatch({ changes: { from, to, insert: `\n\n${text}\n\n` } })
  view.focus()
}
defineExpose({ wrap, linePrefix, insertBlock })
</script>

<template>
  <div class="editor">
    <div class="toolbar" role="toolbar" aria-label="Formato">
      <button type="button" title="Negrita" @click="wrap('**')"><b>B</b></button>
      <button type="button" title="Cursiva" @click="wrap('*')"><i>I</i></button>
      <button type="button" title="Enlace" @click="wrap('[', '](https://)', 'texto del enlace')">🔗</button>
      <button type="button" title="Título 2" @click="linePrefix('## ')">H2</button>
      <button type="button" title="Título 3" @click="linePrefix('### ')">H3</button>
      <button type="button" title="Lista" @click="linePrefix('- ')">• Lista</button>
      <button type="button" title="Cita" @click="linePrefix('> ')">❝</button>
      <span class="sep" />
      <slot name="tools" :insert-block="insertBlock" />
    </div>
    <div ref="host" class="cm" />
  </div>
</template>

<style scoped>
.editor { border: var(--border); background: #fff; }
.toolbar { display: flex; flex-wrap: wrap; gap: var(--space-1); align-items: center; padding: var(--space-2); border-bottom: var(--border); background: var(--color-bg-soft); }
.toolbar button { min-width: 2rem; padding: 2px var(--space-2); border: 1px solid #000; background: #fff; font: 600 0.8rem var(--font-body); cursor: pointer; }
.toolbar button:hover { background: #000; color: #fff; }
.sep { flex: 1; }
.cm :deep(.cm-editor) { min-height: 22rem; max-height: 70vh; font: 0.9rem/1.5 var(--font-body); }
.cm :deep(.cm-scroller) { overflow: auto; }
.cm :deep(.cm-focused) { outline: 3px solid var(--color-accent-lilac); }
</style>
