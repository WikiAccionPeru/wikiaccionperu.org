<script setup lang="ts">
/**
 * Living styleguide: design tokens + EVERY component in app/components + the layouts, each in a bounded frame.
 * Rule: a new component is not done until it has a <SgSpecimen> here (scripts/test-styleguide.mjs fails otherwise).
 * Demo data is the site's own sample content; editor-only parts are shown through <SgAuthScope> (display only).
 */
import taxonomies from '~~/data/taxonomies.json'

const commit = useRuntimeConfig().public.commit
useSeoMeta({ title: 'Guía de estilo — WikiAcción Perú', robots: 'noindex' })

// ---- tokens (assets/tokens.css) ---------------------------------------------------------------------------------------
const colorGroups: [string, string[]][] = [
  ['Superficies y texto', ['--color-text', '--color-text-muted', '--color-bg', '--color-bg-soft', '--color-border', '--color-line', '--color-link']],
  ['Marca (bandas pastel)', ['--color-lilac', '--color-green', '--color-blue']],
  ['Alias (uso antiguo)', ['--color-accent-lilac', '--color-accent-green', '--color-accent-cyan']],
]
const fonts = ['--font-body', '--font-heading', '--font-mono']
const steps = ['--step--1', '--step-0', '--step-1', '--step-2', '--step-3', '--step-4']
const spaces = ['--space-1', '--space-2', '--space-3', '--space-4', '--space-5', '--space-6']
const shape = ['--radius', '--border', '--container', '--header-h', '--bp-md']
const values = reactive<Record<string, string>>({})
onMounted(() => {
  const cs = getComputedStyle(document.documentElement)
  for (const t of [...colorGroups.flatMap(([, l]) => l), ...fonts, ...steps, ...spaces, ...shape]) values[t] = cs.getPropertyValue(t).trim()
})

// ---- demo data ----------------------------------------------------------------------------------------------------------
const { data: posts } = await useAsyncData('sg-posts', () =>
  queryCollection('content').where('status', '=', 'publish').where('type', '=', 'post').order('date', 'DESC').select('path', 'title', 'date', 'featured_media', 'taxonomies').limit(3).all())
const { data: homeDoc } = await useAsyncData('sg-home', () => queryCollection('content').path('/').select('home').first())
const post = computed(() => posts.value?.[0])
const demoPaths = computed(() => (posts.value ?? []).map((p) => p.path))
const home = computed(() => (homeDoc.value?.home ?? {}) as Record<string, any>)
const hero = computed(() => home.value.hero ?? { kicker: 'Somos', title: 'WikiAcción Perú', text: 'Una organización que visibiliza al Perú en Wikipedia.', image: '/media/2022/10/post-wiki30.png', buttons: [{ label: 'Recursos', to: '/recursos/' }] })
const features = computed(() => home.value.features ?? [{ icon: 'training', title: 'Formación', text: 'Capacitación sobre Wikipedia.', to: '/categoria/formacion/' }])
const thematic = computed(() => home.value.thematic ?? { title: '¿No sabes qué editar?', text: 'Listados temáticos.', list: ['Tema uno'], buttons: [{ label: 'Ver', to: '#' }], image: '/media/2022/06/post-wiki.png', cta: { text: 'Suscríbete', label: 'Suscribirme', to: '#' } })

type Tax = { terms: { slug: string; name: string }[] }
const TAX = taxonomies as Record<string, Tax>
const focusTerms = TAX.enfoque_tematico?.terms ?? [] // 3 options -> checkboxes
const categoryTerms = TAX.category?.terms ?? [] // many -> type-ahead
const pickSmall = ref<string[]>([focusTerms[0]?.slug].filter(Boolean) as string[])
const pickBig = ref<string[]>([categoryTerms[0]?.slug].filter(Boolean) as string[])
const demoProps = ref<Record<string, any>>({ title: 'Título de ejemplo', type: 'post', status: 'publish', date: '2026-01-15T10:30:00', excerpt: 'Resumen de la página.', taxonomies: {}, id: 1 })
const tree = ref<unknown>({ title: 'Portada', buttons: [{ label: 'Recursos', to: '/recursos/' }], list: ['uno', 'dos'] })
const md = ref('## Título\n\nTexto con **negrita** y un [enlace](https://example.org).\n')

const sections = [['tokens', 'Tokens'], ['layouts', 'Layouts'], ['atomos', 'Átomos'], ['moleculas', 'Moléculas'], ['organismos', 'Organismos'], ['contenido', 'Contenido (MDC)']]
</script>

<template>
  <div class="sg container">
    <h1>Guía de estilo <small>versión <code>{{ commit }}</code></small></h1>
    <p class="intro">Tokens, layouts y <strong>todos</strong> los componentes de <code>app/components</code>, cada uno en un marco acotado (las secciones a ancho completo se muestran reducidas). Datos de ejemplo: el contenido real del sitio.</p>
    <nav class="toc" aria-label="Secciones"><a v-for="[id, label] in sections" :key="id" :href="`#${id}`">{{ label }}</a></nav>

    <!-- ===================================================== TOKENS -->
    <section id="tokens">
      <h2>Tokens</h2>
      <div v-for="[group, list] in colorGroups" :key="group">
        <h3>Color · {{ group }}</h3>
        <ul class="swatches"><li v-for="t in list" :key="t"><span :style="{ background: `var(${t})` }" /><code>{{ t }}</code><small>{{ values[t] }}</small></li></ul>
      </div>
      <h3>Tipografía</h3>
      <p v-for="f in fonts" :key="f" class="font" :style="{ fontFamily: `var(${f})` }"><code>{{ f }}</code> — La enciclopedia libre que todos podemos editar <small>{{ values[f]?.split(',')[0] }}</small></p>
      <p v-for="s in steps" :key="s" :style="{ fontSize: `var(${s})`, margin: '0.25rem 0' }"><code class="tk">{{ s }}</code> Escala tipográfica <small>{{ values[s] }}</small></p>
      <h3>Espaciado</h3>
      <ul class="spaces"><li v-for="s in spaces" :key="s"><code>{{ s }}</code><span :style="{ width: `var(${s})` }" /><small>{{ values[s] }}</small></li></ul>
      <h3>Forma y medidas</h3>
      <ul class="shape">
        <li><code>--radius</code><span class="box" :style="{ borderRadius: 'var(--radius)' }" /><small>{{ values['--radius'] }}</small></li>
        <li><code>--border</code><span class="box" :style="{ border: 'var(--border)' }" /><small>{{ values['--border'] }}</small></li>
        <li><code>--container</code><small>{{ values['--container'] }} — ancho máximo del contenido</small></li>
        <li><code>--header-h</code><small>{{ values['--header-h'] }} — altura de la cabecera (barra pegajosa de edición)</small></li>
        <li><code>--bp-md</code><small>{{ values['--bp-md'] }} — punto de corte móvil/escritorio</small></li>
      </ul>
    </section>

    <!-- ===================================================== LAYOUTS -->
    <section id="layouts">
      <h2>Layouts</h2>
      <SgSpecimen name="default" kind="layout" note="Páginas de contenido: barra de edición, cabecera, contenido (cada página pone su propio .container), pie." :max-height="200">
        <div class="lay"><b>AdminBar</b><b>SiteHeader</b><i>contenido</i><b>SiteFooter</b></div>
      </SgSpecimen>
      <SgSpecimen name="home" kind="layout" note="Portada: igual, pero el contenido va a ancho completo (bandas pastel)." :max-height="200">
        <div class="lay"><b>AdminBar</b><b>SiteHeader</b><i class="wide">bandas a ancho completo</i><b>SiteFooter</b></div>
      </SgSpecimen>
      <SgSpecimen name="band" kind="layout" note="Listados y archivos: fondo lila, contenido centrado en .container." :max-height="200">
        <div class="lay"><b>AdminBar</b><b>SiteHeader</b><i class="lilac">fondo lila + .container</i><b>SiteFooter</b></div>
      </SgSpecimen>
    </section>

    <!-- ===================================================== ÁTOMOS -->
    <section id="atomos">
      <h2>Átomos</h2>

      <SgSpecimen name="BaseButton" kind="átomo" props="to?: string; variant?: 'solid' | 'outline'" note="Botón redondeado (uso general; la portada usa OutlineButton)."><BaseButton to="#">Sólido</BaseButton> <BaseButton to="#" variant="outline">Contorno</BaseButton></SgSpecimen>
      <SgSpecimen name="BaseTag" kind="átomo" props="to?: string" note="Etiqueta enlazable."><BaseTag to="#">cultura</BaseTag> <BaseTag to="#">#wikipedia</BaseTag></SgSpecimen>
      <SgSpecimen name="OutlineButton" kind="átomo" props="to: string; external?: boolean" note="Botón de la marca: mayúsculas, línea arriba/abajo, «»»; invierte al pasar el cursor."><OutlineButton to="#">Conocer más</OutlineButton> <OutlineButton to="https://wikipedia.org" external>Externo</OutlineButton></SgSpecimen>
      <SgSpecimen name="SiteLogo" kind="átomo" note="Logotipo enlazado a la portada."><SiteLogo /></SgSpecimen>
    </section>

    <!-- ===================================================== MOLÉCULAS -->
    <section id="moleculas">
      <h2>Moléculas</h2>
      <SgSpecimen name="AdminBar" kind="molécula" note="Barra negra para quien ha iniciado sesión (aquí: editora simulada)."><SgAuthScope><AdminBar /></SgAuthScope></SgSpecimen>
      <SgSpecimen name="AdminGate" kind="molécula" note="Protege una pantalla de administración. Izquierda: editora · derecha: cuenta sin permiso (simulados)." :max-height="200">
        <div class="two"><SgAuthScope><AdminGate><p class="ok">Contenido solo para editores.</p></AdminGate></SgAuthScope><SgAuthScope :admin="false"><AdminGate><p>No se ve.</p></AdminGate></SgAuthScope></div>
      </SgSpecimen>
      <SgSpecimen name="AdminNav" kind="molécula" note="Navegación de las pantallas de administración."><AdminNav /></SgSpecimen>
      <SgSpecimen name="EditorCommonsFileInserter" kind="molécula" note="Botón de la barra del editor: abre un diálogo de búsqueda en Wikimedia Commons (la red solo se usa al buscar)."><EditorCommonsFileInserter /></SgSpecimen>
      <SgSpecimen name="EditorEditableSection" kind="molécula" props="section: string; path?: string" note="Envuelve una sección y muestra ✎ solo a editores (simulado)."><SgAuthScope><EditorEditableSection section="demo"><div class="demo-box">Sección editable</div></EditorEditableSection></SgAuthScope></SgSpecimen>
      <SgSpecimen name="EditorEditLink" kind="molécula" props="path: string" note="Botón «Editar» de cada página (solo editores)."><SgAuthScope><EditorEditLink path="/sobre-el-proyecto" /></SgAuthScope></SgSpecimen>
      <SgSpecimen name="EditorPageFieldTree" kind="molécula" props="modelValue: unknown; label?: string; hide?: string[]; open?: string" note="Formulario genérico para datos estructurados (textos, listas, objetos anidados)." :max-height="320"><EditorPageFieldTree v-model="tree" /></SgSpecimen>
      <SgSpecimen name="EditorPageProperties" kind="molécula" props="modelValue: Record<string, any>; hide: string[]" note="Propiedades de una página con opciones cerradas: tipo y estado (listas), fecha (selector) y categorías/etiquetas (solo existentes)." :max-height="400"><EditorPageProperties v-model="demoProps" :hide="[]" /></SgSpecimen>
      <SgSpecimen name="EditorTermPicker" kind="molécula" props="label: string; terms: {slug,name}[]; modelValue: string[]" note="Selector de lista cerrada. Pocas opciones → casillas; muchas → búsqueda predictiva que solo admite términos existentes." :max-height="300">
        <div class="two"><EditorTermPicker v-model="pickSmall" label="Enfoque temático (pocas opciones)" :terms="focusTerms" /><EditorTermPicker v-model="pickBig" label="Categorías (muchas opciones)" :terms="categoryTerms" /></div>
      </SgSpecimen>
      <SgSpecimen name="NavMenu" kind="molécula" note="Menú principal con submenús; pasa el cursor sobre un elemento con submenú." :height="190" visible><NavMenu /></SgSpecimen>
      <SgSpecimen name="NewsCard" kind="molécula" props="path, title, date: string; featuredMedia?: number; taxonomies?: Record<string, string[]>" note="Tarjeta vertical de noticia (datos: la última noticia publicada)." max-width="16rem" :max-height="520">
        <NewsCard v-if="post" :path="post.path" :title="post.title" :date="post.date" :featured-media="post.featured_media" :taxonomies="post.taxonomies" />
        <NewsCard v-else path="#" title="Título de ejemplo" date="2026-01-15T10:00:00" />
      </SgSpecimen>
      <SgSpecimen name="PaginationNav" kind="molécula" props="page: number; pages: number; base: string" note="Paginación numerada con puntos suspensivos."><PaginationNav :page="3" :pages="12" base="/styleguide/" /></SgSpecimen>
      <SgSpecimen name="RecentPosts" kind="molécula" note="Barra lateral: búsqueda + entradas recientes." max-width="20rem" :max-height="420"><RecentPosts /></SgSpecimen>
      <SgSpecimen name="SearchBox" kind="molécula" props="initial?: string" note="Formulario de búsqueda (va a /buscar/)." max-width="20rem"><SearchBox /></SgSpecimen>
      <SgSpecimen name="TermLines" kind="molécula" props="taxonomies?: Record<string, string[]>; maxTags?: number" note="Líneas de enfoque, categorías y etiquetas de una noticia."><TermLines v-if="post" :taxonomies="post.taxonomies" /></SgSpecimen>
    </section>

    <!-- ===================================================== ORGANISMOS -->
    <section id="organismos">
      <h2>Organismos</h2>

      <SgSpecimen name="ContentPage" kind="organismo" props="path: string; seo?: boolean" note="Página de contenido (título, fecha, Markdown, términos, barra lateral en noticias). Aquí: /sobre-el-proyecto." :max-height="340"><ClientOnly><ContentPage path="/sobre-el-proyecto" :seo="false" /></ClientOnly></SgSpecimen>
      <SgSpecimen name="EditorMarkdown" kind="organismo" note="Editor Markdown (CodeMirror) con barra; admite herramientas extra por la ranura «tools»." compact><ClientOnly><EditorMarkdown v-model="md" /></ClientOnly></SgSpecimen>
      <SgSpecimen name="FeatureCards" kind="organismo" props="items: {icon,title,text,to}[]" note="Cuatro tarjetas de líneas de acción (datos de la portada)." :design="1440"><FeatureCards :items="features" /></SgSpecimen>
      <SgSpecimen name="HomeHero" kind="organismo" props="kicker, title, text, image: string; buttons: {label,to}[]" note="Portada: panel verde + foto." :design="1440"><HomeHero v-bind="hero" /></SgSpecimen>
      <SgSpecimen name="MediaBand" kind="organismo" note="Banda verde «en medios» (tres notas de prensa)." :design="1440"><MediaBand /></SgSpecimen>
      <SgSpecimen name="NewsBand" kind="organismo" note="Banda lila con las 4 últimas noticias." :design="1440"><NewsBand /></SgSpecimen>
      <SgSpecimen name="NewsList" kind="organismo" props="page: number; base: string; paths?: string[]; type?: string" note="Cuadrícula paginada de NewsCard (aquí limitada a 3 noticias para el ejemplo)." :design="1000"><NewsList :page="1" base="/styleguide/" :paths="demoPaths" /></SgSpecimen>
      <SgSpecimen name="SiteFooter" kind="organismo" note="Pie: logotipo, recursos, contacto, licencia y versión." :design="1440"><SiteFooter /></SgSpecimen>
      <SgSpecimen name="SiteHeader" kind="organismo" note="Cabecera pegajosa: logotipo + menú." :design="1440"><SiteHeader /></SgSpecimen>
      <SgSpecimen name="ThematicSplit" kind="organismo" props="title, text, image: string; list: string[]; buttons; cta: {text,label,to}" note="Bloque «¿No sabes sobre qué editar?» con llamada a suscribirse." :design="1440"><ThematicSplit v-bind="thematic" /></SgSpecimen>
    </section>

    <!-- ===================================================== CONTENIDO -->
    <section id="contenido">
      <h2>Contenido (componentes MDC dentro del Markdown)</h2>
      <p class="intro">Se usan como <code>::nombre{…}</code> dentro de las páginas; el editor los inserta desde la barra.</p>

      <SgSpecimen name="CenteredBlock" kind="contenido" note="::centered-block — bloque de texto centrado."><CenteredBlock><p>Texto centrado de ejemplo.</p></CenteredBlock></SgSpecimen>
      <SgSpecimen name="MediaMentions" kind="contenido" props="perPage?: number | string" note="::media-mentions — rejilla paginada de notas de prensa (data/medios.json)." :max-height="320"><MediaMentions :per-page="2" /></SgSpecimen>
      <SgSpecimen name="PartnersCarousel" kind="contenido" note="::partners-carousel — tarjetas verticales que giran sin fin; se pausa al pasar el cursor o con el botón; respeta «reducir movimiento»." :max-height="450"><PartnersCarousel /></SgSpecimen>
      <SgSpecimen name="ProseImg" kind="contenido" props="src, alt, title?: string; width?, height?" note="Imagen del Markdown con pie de foto; las locales se optimizan."><ProseImg src="/media/2021/10/cropped-isotipo_wikiaccion-2.png" alt="Isotipo de WikiAcción Perú" title="Pie de foto de ejemplo" width="120" /></SgSpecimen>
      <SgSpecimen name="SplitHero" kind="contenido" props="image: string; color?: 'lilac' | 'green' | 'blue'; alt?: string" note="::split-hero — texto sobre fondo de color + foto." :design="1440"><SplitHero image="/media/2022/10/post-wiki30.png" color="lilac"><h2>Título</h2><p>Texto de la portada de sección.</p></SplitHero></SgSpecimen>
      <SgSpecimen name="VideoEmbed" kind="contenido" props="src: string; title?: string" note="::video-embed — vídeo incrustado 16:9 (YouTube pasa por youtube-nocookie). Aquí vacío para no cargar terceros." max-width="26rem"><VideoEmbed src="about:blank" title="Ejemplo" /></SgSpecimen>
    </section>
  </div>
</template>

<style scoped>
.sg { padding-block: var(--space-4) var(--space-6); }
h1 small { font-size: 1rem; color: var(--color-text-muted); }
.intro { color: var(--color-text-muted); max-width: 52rem; }
.toc { display: flex; flex-wrap: wrap; gap: var(--space-3); margin: var(--space-3) 0 var(--space-4); padding-bottom: var(--space-2); border-bottom: var(--border); }
.toc a { font: 600 0.8rem var(--font-body); text-transform: uppercase; text-decoration: none; }
section { margin-bottom: var(--space-6); }
h2 { border-bottom: var(--border); padding-bottom: var(--space-1); }
h3 { font-size: 1rem; margin: var(--space-4) 0 var(--space-2); }
code { font-size: 0.8rem; }
small { color: var(--color-text-muted); margin-left: var(--space-2); font-size: 0.75rem; }
.swatches { list-style: none; padding: 0; margin: 0; display: grid; grid-template-columns: repeat(auto-fill, minmax(13rem, 1fr)); gap: var(--space-2) var(--space-3); }
.swatches li { display: flex; align-items: center; gap: var(--space-2); flex-wrap: wrap; }
.swatches span { width: 2rem; height: 2rem; border: 1px solid var(--color-line); flex: none; }
.font { margin: var(--space-1) 0; font-size: 1.1rem; }
.tk { display: inline-block; min-width: 6rem; }
.spaces, .shape { list-style: none; padding: 0; margin: 0; display: grid; gap: var(--space-2); }
.spaces li, .shape li { display: flex; align-items: center; gap: var(--space-3); }
.spaces code, .shape code { min-width: 7rem; }
.spaces span { height: 1rem; background: var(--color-accent-lilac); border: 1px solid var(--color-line); }
.box { width: 3rem; height: 1.5rem; background: var(--color-bg-soft); display: inline-block; }
.lay { display: grid; gap: var(--space-1); text-align: center; font-size: 0.8rem; }
.lay b { background: var(--color-bg-soft); border: 1px solid var(--color-line); padding: 2px; } .lay i { background: #fff; border: 1px dashed var(--color-line); padding: var(--space-3); font-style: normal; }
.lay .wide { background: var(--color-green); } .lay .lilac { background: var(--color-lilac); }
.two { display: grid; grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr)); gap: var(--space-3); align-items: start; }
.demo-box { padding: var(--space-4); border: 1px dashed var(--color-line); background: var(--color-bg-soft); } .ok { color: #060; margin: 0; }
</style>
