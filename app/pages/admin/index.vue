<script setup lang="ts">
useSeoMeta({ title: 'Ajustes — WikiAcción Perú', robots: 'noindex' })
const { me } = useAuth()
</script>
<template>
  <div class="container pad">
    <AdminNav />
    <h1>Ajustes del sitio</h1>
    <AdminGate>
      <p>Hola, <strong>{{ me.user?.username }}</strong>.</p>
      <ul class="cards">
        <li><NuxtLink to="/admin/pages/"><strong>Páginas</strong><span>Crear, mover, eliminar y editar páginas y noticias.</span></NuxtLink></li>
        <li><NuxtLink to="/admin/menu/"><strong>Menú</strong><span>Elementos y submenús de la cabecera.</span></NuxtLink></li>
        <li><NuxtLink to="/admin/editors/"><strong>Editores</strong><span>Quién puede editar el sitio y utilidad «usuario → id».</span></NuxtLink></li>
        <li class="soon"><span><strong>Sincronización con git</strong><span>Próximamente: ver cambios, traer y enviar al repositorio.</span></span></li>
      </ul>
    </AdminGate>
  </div>
</template>
<style scoped>
.pad { padding-block: var(--space-4) var(--space-6); }
.cards { list-style: none; padding: 0; display: grid; grid-template-columns: repeat(auto-fill, minmax(15rem, 1fr)); gap: var(--space-4); }
.cards a, .cards .soon > span { display: grid; gap: var(--space-2); height: 100%; padding: var(--space-4); border: var(--border); text-decoration: none; background: #fff; }
.cards a:hover { background: var(--color-accent-lilac); }
.cards span span { font-size: 0.85rem; color: var(--color-text-muted); }
.soon { opacity: 0.55; }
</style>
