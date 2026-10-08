<template>
  <nav class="adminnav" aria-label="Administración">
    <NuxtLink to="/admin/">Ajustes</NuxtLink>
    <NuxtLink to="/admin/pages/">Páginas</NuxtLink>
    <NuxtLink to="/admin/menu/">Menú</NuxtLink>
    <NuxtLink to="/admin/editors/">Editores</NuxtLink>
  </nav>
</template>
<style scoped>
.adminnav { display: flex; gap: var(--space-4); flex-wrap: wrap; border-bottom: var(--border); margin-bottom: var(--space-4); padding-bottom: var(--space-2); }
a { text-decoration: none; font-weight: 600; text-transform: uppercase; font-size: 0.85rem; }
a.router-link-exact-active { border-bottom: 3px solid #000; }
</style>
