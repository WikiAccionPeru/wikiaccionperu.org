<script setup lang="ts">
/** Styleguide helper: shows editor-only components as if an editor (or a non-editor) were logged in. Display only — the server still decides. */
const props = withDefaults(defineProps<{ admin?: boolean }>(), { admin: true })
provide('authDemo', { user: { id: '0', username: 'Usuaria Demo' }, admin: props.admin })
</script>
<template><div><slot /></div></template>
