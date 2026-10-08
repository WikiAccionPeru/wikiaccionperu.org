<script setup lang="ts">
const { menu } = useSite()
const open = ref(false)
</script>
<template>
  <nav aria-label="Principal">
    <button class="burger" :aria-expanded="open" @click="open = !open"><span class="sr-only">Menú</span>☰</button>
    <ul :class="{ open }">
      <li v-for="item in menu" :key="item.url">
        <NuxtLink :to="item.url" @click="open = false">{{ item.title }}</NuxtLink>
        <ul v-if="item.children.length" class="sub">
          <li v-for="c in item.children" :key="c.url"><NuxtLink :to="c.url" @click="open = false">{{ c.title }}</NuxtLink></li>
        </ul>
      </li>
    </ul>
  </nav>
</template>
<style scoped>
ul { list-style: none; margin: 0; padding: 0; display: flex; gap: var(--space-4); }
li { position: relative; }
a { text-decoration: none; padding: var(--space-2) 0; display: inline-block; font: 500 1rem var(--font-heading); text-transform: uppercase; }
a.router-link-exact-active { border-bottom: 3px solid #000; }
.sub { display: none; position: absolute; left: 0; top: 100%; flex-direction: column; gap: 0; background: var(--color-bg); border: 1px solid #000; background: #fff; padding: var(--space-2) var(--space-3); min-width: 15rem; z-index: 10; }
li:hover > .sub, li:focus-within > .sub { display: flex; }
.burger { display: none; background: none; border: 0; font-size: var(--step-2); cursor: pointer; }
@media (max-width: 768px) {
  .burger { display: block; }
  nav > ul { display: none; flex-direction: column; gap: 0; }
  nav > ul.open { display: flex; }
  .sub { display: flex; position: static; border: 0; padding-left: var(--space-3); }
}
</style>
