// Front-end tests of the admin UI with mocked API (no real login needed).
import { chromium } from 'playwright'
import { readFileSync } from 'node:fs'
import { parse } from 'yaml'
const base = process.argv[2]
const homeText = readFileSync('content/index.md', 'utf8')
let fails = 0
const ok = (name, cond, extra = '') => { console.log(cond ? 'ok  ' : 'FAIL', name, extra); if (!cond) fails++ }
const b = await chromium.launch({ channel: 'chrome' })

async function newPage(handlers) {
  const p = await b.newPage()
  const errs = []; p.on('pageerror', (e) => errs.push(e.message.slice(0, 200)))
  await p.route('**/api/auth/me', (r) => r.fulfill({ json: { user: { id: '5554', username: 'Yug' }, admin: true } }))
  for (const [pat, fn] of Object.entries(handlers)) await p.route(pat, fn)
  p.errs = errs
  return p
}
const fm = (text) => parse(text.match(/^---\r?\n([\s\S]*?)\r?\n---/)[1])

// 1. Section-level editing of the home page ------------------------------------------------
{
  const puts = []
  const p = await newPage({ '**/api/admin/page**': (r) => { const q = r.request(); if (q.method() === 'PUT') { puts.push(q.postDataJSON()); return r.fulfill({ json: { ok: true } }) } return r.fulfill({ json: { path: '/', text: homeText } }) } })
  await p.goto(`${base}/admin/edit/?path=/&section=hero`, { waitUntil: 'load' })
  await p.waitForSelector('[data-section="hero"]', { timeout: 15000 })
  ok('home: sections are forms (not raw YAML)', (await p.locator('.cm-content').count()) === 0 && (await p.locator('[data-section]').count()) >= 4)
  ok('home: requested section is open', await p.locator('[data-section="hero"]').evaluate((e) => e.open))
  ok('home: other sections collapsed', await p.locator('[data-section="features"]').evaluate((e) => !e.open))
  ok('home: generic properties hidden when editing a section', (await p.locator('h2:has-text("Propiedades")').count()) === 0)
  const title = p.locator('[data-section="hero"] input[type=text]').nth(1) // kicker=0, title=1
  await title.fill('WikiAcción Perú — editado')
  await p.click('.save'); await p.waitForTimeout(600)
  ok('home: one PUT', puts.length === 1)
  const saved = fm(puts[0].text)
  ok('home: edited value saved inside home.hero.title', saved.home.hero.title === 'WikiAcción Perú — editado')
  ok('home: untouched data intact (features=4, buttons kept)', saved.home.features.length === 4 && saved.home.hero.buttons.length === 2 && saved.title === 'Inicio')
  ok('home: no page errors', p.errs.length === 0, p.errs.join('|'))
  await p.close()
}

// 2. Normal page: closed-choice properties + body editor ------------------------------------------------
{
  const text = '---\ntitle: "Mi página"\nslug: "mi-pagina"\ntype: "post"\nstatus: "publish"\ndate: "2026-01-01T10:30:00"\nexcerpt: "Resumen"\ntaxonomies: {"category": ["cultura"], "post_tag": ["wikipedia"], "enfoque_tematico": ["cultura"]}\nid: 7\n---\n\n## Hola\n\nCuerpo.\n'
  const puts = []
  const p = await newPage({ '**/api/admin/page**': (r) => { const q = r.request(); if (q.method() === 'PUT') { puts.push(q.postDataJSON()); return r.fulfill({ json: { ok: true } }) } return r.fulfill({ json: { path: '/mi-pagina', text } }) } })
  await p.goto(`${base}/admin/edit/?path=/mi-pagina`, { waitUntil: 'load' })
  await p.waitForSelector('.cm-content', { timeout: 15000 })
  ok('page: markdown body in editor, frontmatter not in it', !(await p.locator('.cm-content').innerText()).includes('title:'))
  // closed choices
  const typeOpts = await p.locator('select').nth(0).locator('option').allInnerTexts()
  ok('type is a dropdown of 5 content types', typeOpts.length === 5 && typeOpts.includes('Noticia'), typeOpts.join(','))
  const stOpts = await p.locator('select').nth(1).locator('option').allInnerTexts()
  ok('status is a dropdown: Publicado / Borrador', stOpts.length === 2 && stOpts[0] === 'Publicado', stOpts.join(','))
  ok('date is a date-time picker holding the current value', (await p.locator('input[type=datetime-local]').inputValue()).startsWith('2026-01-01T10:30'))
  ok('few options (focus area) are checkboxes, one checked', (await p.locator('fieldset:has(legend:text("Enfoque temático")) input[type=checkbox]').count()) === 3 && (await p.locator('fieldset:has(legend:text("Enfoque temático")) input:checked').count()) === 1)
  // type-ahead is closed: only existing terms can be added
  const cat = p.locator('fieldset:has(legend:text("Categorías"))')
  await cat.locator('input[role=combobox]').fill('zzzz-no-such-category'); ok('type-ahead offers nothing for an unknown term (closed list)', (await cat.locator('[role=option]').count()) === 0)
  await cat.locator('input[role=combobox]').fill('conv'); const opts = await cat.locator('[role=option]').allInnerTexts()
  ok('type-ahead lists existing categories only', opts.length >= 1, opts.join('|'))
  await cat.locator('[role=option]').first().click()
  ok('picked category appears as a chip', (await cat.locator('.chips li').count()) === 2)
  // edits
  await p.locator('label:has-text("Título") input').first().fill('Mi página nueva')
  await p.locator('select').nth(1).selectOption('draft')
  await p.locator('input[type=datetime-local]').fill('2026-02-03T04:05:06')
  await p.locator('.cm-content').click(); await p.keyboard.press('Control+End'); await p.keyboard.type(' Extra.')
  await p.click('.save'); await p.waitForTimeout(600)
  const s = puts[0]?.text ?? ''
  const f = fm(s)
  ok('page: title edited', f.title === 'Mi página nueva')
  ok('page: status saved as draft, date saved', f.status === 'draft' && String(f.date).startsWith('2026-02-03T04:05:06'), String(f.date))
  ok('page: category added, others kept', f.taxonomies.category.length === 2 && f.taxonomies.category[0] === 'cultura' && f.taxonomies.post_tag[0] === 'wikipedia' && f.taxonomies.enfoque_tematico[0] === 'cultura')
  ok('page: body edited & kept', s.includes('## Hola') && s.includes('Extra.'))
  ok('page: technical fields preserved (id, slug)', f.id === 7 && f.slug === 'mi-pagina')
  // changing type to one that has no taxonomies drops them
  await p.locator('select').nth(0).selectOption('page'); await p.click('.save'); await p.waitForTimeout(600)
  ok('type change to "page" drops taxonomies that no longer apply', puts[1] && fm(puts[1].text).taxonomies === undefined || Object.keys(fm(puts[1].text).taxonomies ?? {}).length === 0)
  ok('page: no page errors', p.errs.length === 0, p.errs.join('|'))
  await p.close()
}

// 3. Page manager ------------------------------------------------------------------------------
{
  const calls = []
  const list = [{ path: '/', title: 'Inicio', type: 'page', date: '' }, { path: '/uno', title: 'Uno', type: 'post', date: '' }, { path: '/dos', title: 'Dos', type: 'page', date: '' }]
  const p = await newPage({
    '**/api/admin/pages': (r) => { const q = r.request(); if (q.method() === 'POST') { calls.push(['create', q.postDataJSON()]); return r.fulfill({ json: { ok: true, path: '/nueva' } }) } return r.fulfill({ json: list }) },
    '**/api/admin/pages/move': (r) => { calls.push(['move', r.request().postDataJSON()]); return r.fulfill({ json: { ok: true } }) },
    '**/api/admin/pages/delete': (r) => { calls.push(['delete', r.request().postDataJSON()]); return r.fulfill({ json: { ok: true } }) },
    '**/api/admin/page?**': (r) => r.fulfill({ json: { path: '/nueva', text: '---\ntitle: "N"\ntype: "page"\ndate: "x"\n---\nhi' } }),
  })
  p.on('dialog', (d) => d.accept())
  await p.goto(`${base}/admin/pages/`, { waitUntil: 'load' })
  await p.waitForSelector('tbody tr', { timeout: 15000 })
  ok('pages: lists all, home has no move/delete', (await p.locator('tbody tr').count()) === 3 && (await p.locator('tbody tr').first().locator('button').count()) === 0)
  await p.fill('input[type=search]', 'uno'); ok('pages: filter works', (await p.locator('tbody tr').count()) === 1)
  await p.fill('input[type=search]', '')
  await p.locator('tbody tr:has-text("Dos") button:has-text("Mover")').click()
  await p.locator('.moverow input').fill('/guia/dos'); await p.locator('.moverow button[type=submit]').click(); await p.waitForTimeout(400)
  ok('pages: move sent', JSON.stringify(calls.find((c) => c[0] === 'move')?.[1]) === JSON.stringify({ from: '/dos', to: '/guia/dos' }))
  await p.locator('tbody tr:has-text("Uno") button:has-text("Eliminar")').click(); await p.waitForTimeout(400)
  ok('pages: delete sent after confirm', calls.find((c) => c[0] === 'delete')?.[1].path === '/uno')
  await p.fill('.new input[required]:not([pattern])', 'Página nueva'); await p.fill('.new input[pattern]', '/nueva'); ok('pages: new-page form validates', await p.locator('.new').evaluate((f) => f.checkValidity())); await p.fill('.new input[pattern]', '/Mala dirección'); ok('pages: bad address blocked by the form', !(await p.locator('.new').evaluate((f) => f.checkValidity()))); await p.fill('.new input[pattern]', '/nueva'); await p.click('.new button[type=submit]'); await p.waitForTimeout(800)
  ok('pages: create sent and goes to editor', calls.find((c) => c[0] === 'create')?.[1].path === '/nueva' && p.url().includes('/admin/edit/'), p.url())
  ok('pages: no page errors', p.errs.length === 0, p.errs.join('|'))
  await p.close()
}

// 4. Menu editor ---------------------------------------------------------------------------------
{
  let put
  const menu = [{ title: 'Inicio', url: '/', children: [] }, { title: 'Recursos', url: '/recursos', children: [{ title: 'Cursos', url: '/x', children: [] }] }]
  const p = await newPage({ '**/api/admin/menu': (r) => { const q = r.request(); if (q.method() === 'PUT') { put = q.postDataJSON(); return r.fulfill({ json: { ok: true, items: put.length } }) } return r.fulfill({ json: menu }) }, '**/api/admin/pages': (r) => r.fulfill({ json: [] }) })
  await p.goto(`${base}/admin/menu/`, { waitUntil: 'load' })
  await p.waitForSelector('.menu .row', { timeout: 15000 })
  await p.locator('.menu > li').nth(1).locator('.row').first().locator('button[aria-label="Subir"]').click()
  await p.click('button:has-text("＋ Elemento")')
  await p.click('.save'); await p.waitForTimeout(500)
  ok('menu: reorder + add saved', put?.[0].title === 'Recursos' && put?.[1].title === 'Inicio' && put?.length === 3 && put[0].children[0].title === 'Cursos')
  ok('menu: no page errors', p.errs.length === 0, p.errs.join('|'))
  await p.close()
}

// 5. Editors + username→id helper ------------------------------------------------------------------
{
  let put
  const p = await newPage({
    '**/api/admin/editors': (r) => { const q = r.request(); if (q.method() === 'PUT') { put = q.postDataJSON(); return r.fulfill({ json: { ok: true } }) } return r.fulfill({ json: { relyOnUsername: true, admins: [{ username: 'Yug', id: null, resolvedId: '5554' }], me: {} } }) },
    '**/api/admin/resolve-users**': (r) => { const n = new URL(r.request().url()).searchParams.get('names'); return r.fulfill({ json: { ids: Object.fromEntries(n.split('\n').map((x) => [x, x === 'Nadie' ? null : '11134990'])), invalid: [] } }) },
  })
  await p.goto(`${base}/admin/editors/`, { waitUntil: 'load' })
  await p.waitForSelector('tbody tr', { timeout: 15000 })
  await p.fill('textarea', 'Jesedmateo'); await p.click('button:has-text("Buscar ids")'); await p.waitForTimeout(400)
  ok('editors: helper shows paste-ready line', (await p.locator('table code').innerText()) === 'Jesedmateo | 11134990')
  await p.fill('.add input', 'Jesedmateo'); await p.click('.add button'); await p.waitForTimeout(400)
  await p.click('.save'); await p.waitForTimeout(500)
  ok('editors: add + save payload', put?.relyOnUsername === true && put.admins.length === 2 && put.admins[1].username === 'Jesedmateo')
  await p.fill('.add input', 'Nadie'); await p.click('.add button'); await p.waitForTimeout(400)
  ok('editors: unknown account refused with message', (await p.locator('.msg.error').count()) === 1)
  ok('editors: no page errors', p.errs.length === 0, p.errs.join('|'))
  await p.close()
}

// 6. Section pen on the public home page ----------------------------------------------------------------
{
  const p = await newPage({})
  await p.goto(`${base}/`, { waitUntil: 'load' })
  await p.waitForSelector('a.pen', { timeout: 15000 })
  const hrefs = await p.locator('a.pen').evaluateAll((a) => a.map((x) => x.getAttribute('href')))
  ok('home: ✎ on hero/features/thematic/partners', hrefs.length === 4 && hrefs.every((h) => h.includes('section=')), hrefs.join(' '))
  await p.close()
}
await b.close()
console.log(fails ? `\n${fails} FAILED` : '\nALL PASSED')
process.exit(fails ? 1 : 0)
