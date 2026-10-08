<script setup lang="ts">
const { me, loaded, refresh, logout } = useAuth()
onMounted(refresh)
</script>
<template>
  <div v-if="loaded && me.user" class="adminbar" role="region" aria-label="Editores">
    <span>Sesión: <strong>{{ me.user.username }}</strong> <em v-if="!me.admin">(sin permisos de edición)</em></span>
    <span class="actions">
      <NuxtLink v-if="me.admin" to="/admin/" class="gear" aria-label="Ajustes del sitio" title="Ajustes del sitio">⚙</NuxtLink>
      <button type="button" @click="logout">Salir</button>
    </span>
  </div>
</template>
<style scoped>
.adminbar { display: flex; justify-content: space-between; gap: var(--space-3); padding: var(--space-1) var(--space-4); background: #000; color: #fff; font-size: 0.8rem; }
.actions { display: flex; gap: var(--space-3); align-items: center; }
.gear { color: #fff; text-decoration: none; font-size: 1.1rem; }
button { background: none; border: 1px solid #fff; color: #fff; font: inherit; cursor: pointer; padding: 0 var(--space-2); }
button:hover { background: #fff; color: #000; }
</style>
