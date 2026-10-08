<script setup lang="ts">
const { me, loaded, refresh, loginUrl } = useAuth()
const route = useRoute()
onMounted(refresh)
</script>
<template>
  <p v-if="!loaded">Comprobando sesión…</p>
  <p v-else-if="!me.user">Esta sección es solo para editores. <a :href="loginUrl(route.fullPath)">Iniciar sesión con Wikimedia</a>.</p>
  <p v-else-if="!me.admin">La cuenta <strong>{{ me.user.username }}</strong> no figura en la lista de editores.</p>
  <slot v-else />
</template>
