<script setup lang="ts">
const props = defineProps<{ initial?: string }>()
const q = ref(props.initial ?? '')
</script>
<template>
  <form class="search" action="/buscar/" method="get" role="search">
    <label for="site-search" class="label">Buscar</label>
    <div class="row">
      <input id="site-search" v-model="q" type="search" name="q" autocomplete="off" required>
      <button type="submit">Buscar</button>
    </div>
  </form>
</template>
<style scoped>
.search { background: #fff; border: var(--border); padding: var(--space-3) var(--space-4); }
.label { display: block; font: 600 0.8rem var(--font-body); margin-bottom: var(--space-2); }
.row { display: flex; gap: var(--space-2); }
input { flex: 1; min-width: 0; padding: var(--space-2); border: var(--border); font: inherit; border-radius: 0; }
button { padding: var(--space-2) var(--space-3); border: 1px solid #000; background: #111; color: #fff; font: 600 0.85rem var(--font-body); cursor: pointer; }
button:hover, button:focus-visible { background: #fff; color: #000; }
</style>
