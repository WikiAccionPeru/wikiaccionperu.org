<script setup lang="ts">
defineProps<{ path: string }>()
const { me, loaded, refresh } = useAuth()
onMounted(() => { if (!loaded.value) refresh() })
</script>
<template>
  <NuxtLink v-if="me.admin" :to="{ path: '/admin/edit/', query: { path } }" class="edit" title="Editar esta página">✎ Editar</NuxtLink>
</template>
<style scoped>
.edit { display: inline-block; padding: 2px var(--space-3); border: 1px solid #000; background: var(--color-accent-lilac); color: #000; font: 600 0.8rem var(--font-body); text-decoration: none; }
.edit:hover { background: #000; color: #fff; }
</style>
