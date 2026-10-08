<script setup lang="ts">
import all from '~~/data/medios.json'
const items = all.slice(0, 3)
</script>
<template>
  <section class="band">
    <div class="container">
      <h2>WikiAcción Perú en medios</h2>
      <ul class="cards">
        <li v-for="m in items" :key="m.nota_id" class="card">
          <svg viewBox="0 0 24 24" width="40" height="40" fill="currentColor" aria-hidden="true">
            <path v-if="m.kind === 'video'" d="M3 5h18v14H3zm7 3v8l6-4z" fill-rule="evenodd" />
            <path v-else d="M4 4h16v16H4zM7 8h10v3H7zm0 5h10v1.5H7zm0 3h10v1.5H7z" fill-rule="evenodd" />
          </svg>
          <h3><a :href="m.url" target="_blank" rel="noopener">{{ m.title }}</a></h3>
          <p>{{ m.excerpt }}</p>
          <OutlineButton :to="m.url" external>Leer más</OutlineButton>
        </li>
      </ul>
      <p class="more"><OutlineButton to="/wikiaccion-peru-en-medios/">Ver más notas en medios</OutlineButton></p>
    </div>
  </section>
</template>
<style scoped>
.band { background: var(--color-green); border-bottom: var(--border); padding-block: var(--space-5); }
h2 { margin-top: 0; font-size: 2rem; }
.cards { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--space-4); }
.card { background: #fff; border: var(--border); padding: var(--space-4); display: flex; flex-direction: column; align-items: flex-start; gap: var(--space-2); }
h3 { margin: 0; font-size: 1.35rem; } h3 a { text-decoration: none; }
p { margin: 0; font-size: 0.8rem; flex: 1; }
.more { text-align: right; margin: var(--space-4) 0 0; }
@media (max-width: 900px) { .cards { grid-template-columns: 1fr; } }
</style>
