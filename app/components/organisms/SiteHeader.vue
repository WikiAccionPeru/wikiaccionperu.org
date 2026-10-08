<template>
  <header class="site-header">
    <div class="container bar">
      <SiteLogo />
      <NavMenu />
    </div>
  </header>
</template>
<style scoped>
.site-header { border-bottom: var(--border); background: var(--color-bg); position: sticky; top: 0; z-index: 20; }
.bar { display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); padding-block: var(--space-2); flex-wrap: wrap; }
</style>
