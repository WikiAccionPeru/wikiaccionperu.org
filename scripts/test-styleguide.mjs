// Styleguide rules: (1) every component, layout and design token has an entry, (2) no demo is oversized, (3) no errors.
//   node scripts/test-styleguide.mjs http://localhost:8079
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { join, basename } from 'node:path'
import { chromium } from 'playwright'

const base = process.argv[2]
let fails = 0
const ok = (n, c, x = '') => { console.log(c ? 'ok  ' : 'FAIL', n, c ? '' : x); if (!c) fails++ }
const walk = (d) => readdirSync(d).flatMap((f) => (statSync(join(d, f)).isDirectory() ? walk(join(d, f)) : [join(d, f)]))
const src = readFileSync('app/pages/styleguide.vue', 'utf8')

// 1. coverage (static)
const comps = walk('app/components').filter((f) => f.endsWith('.vue') && !f.includes('/styleguide/')).map((f) => basename(f, '.vue'))
const layouts = walk('app/layouts').map((f) => basename(f, '.vue'))
const documented = [...src.matchAll(/<SgSpecimen\s+name="([^"]+)"/g)].map((m) => m[1])
const missing = [...comps, ...layouts].filter((n) => !documented.includes(n))
ok(`every component and layout has a specimen (${comps.length} components + ${layouts.length} layouts)`, missing.length === 0, 'missing: ' + missing.join(', '))
const stale = documented.filter((n) => ![...comps, ...layouts].includes(n))
ok('no specimen for a component that no longer exists', stale.length === 0, 'stale: ' + stale.join(', '))
ok('no duplicated specimens', new Set(documented).size === documented.length)
const tokens = [...readFileSync('app/assets/tokens.css', 'utf8').matchAll(/(--[\w-]+)\s*:/g)].map((m) => m[1])
const untokened = tokens.filter((t) => !src.includes(`'${t}'`) && !src.includes(`<code>${t}</code>`))
ok(`every design token is shown (${tokens.length})`, untokened.length === 0, 'missing: ' + untokened.join(', '))

// 2+3. rendered
const b = await chromium.launch({ channel: 'chrome' })
for (const [label, vp] of [['desktop 1440', { width: 1440, height: 900 }], ['mobile 390', { width: 390, height: 844 }]]) {
  const p = await b.newPage({ viewport: vp })
  const errs = []
  p.on('pageerror', (e) => errs.push(e.message.slice(0, 160)))
  p.on('console', (m) => { if (m.type() === 'error' || /hydrat/i.test(m.text())) errs.push(m.text().slice(0, 160)) })
  await p.goto(`${base}/styleguide/`, { waitUntil: 'load', timeout: 90000 })
  await p.waitForSelector('.sg-spec', { timeout: 60000 })
  await p.waitForTimeout(4000)
  const r = await p.evaluate(() => {
    const frames = [...document.querySelectorAll('.sg-frame')]
    return {
      specs: document.querySelectorAll('.sg-spec').length,
      pageOverflow: document.documentElement.scrollWidth - window.innerWidth,
      tall: frames.map((f) => ({ id: f.closest('.sg-spec').id, h: Math.round(f.getBoundingClientRect().height) })).filter((x) => x.h > 560),
      wide: frames.map((f) => ({ id: f.closest('.sg-spec').id, over: Math.round(f.getBoundingClientRect().right - document.documentElement.clientWidth) })).filter((x) => x.over > 1),
      empty: frames.filter((f) => f.getBoundingClientRect().height < 20).map((f) => f.closest('.sg-spec').id),
      totalHeight: document.documentElement.scrollHeight,
    }
  })
  ok(`${label}: ${r.specs} specimens rendered (= ${documented.length} documented)`, r.specs === documented.length, String(r.specs))
  ok(`${label}: no horizontal page scroll`, r.pageOverflow <= 1, `overflow ${r.pageOverflow}px`)
  ok(`${label}: no demo taller than 560 px`, r.tall.length === 0, JSON.stringify(r.tall))
  ok(`${label}: no demo wider than the page`, r.wide.length === 0, JSON.stringify(r.wide))
  ok(`${label}: no empty demo frame`, r.empty.length === 0, r.empty.join(', '))
  ok(`${label}: no console / hydration errors`, errs.length === 0, errs.slice(0, 4).join(' | '))
  console.log(`      page height ${r.totalHeight}px`)
  await p.close()
}
await b.close()
console.log(fails ? `\n${fails} FAILED` : '\nALL PASSED'); process.exit(fails ? 1 : 0)
