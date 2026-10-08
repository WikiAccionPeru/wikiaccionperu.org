import { chromium } from 'playwright'
const base = process.argv[2]
const b = await chromium.launch({ channel: 'chrome' })
const p = await b.newPage()
await p.goto(`${base}/noticias/`, { waitUntil: 'load' })
await p.fill('#site-search', 'Cinéfilias')   // accent/case-insensitive
await p.click('button[type=submit]')
await p.waitForURL('**/buscar/**')
await p.waitForSelector('.results li', { timeout: 15000 })
const n = await p.locator('.results li').count()
const first = await p.locator('.results li a').first().innerText()
console.log('results:', n, '| first:', first)
await p.goto(`${base}/buscar/?q=zzzzqqq`, { waitUntil: 'load' })
await p.waitForSelector('text=Sin resultados', { timeout: 15000 })
console.log('no-result message ok')
await b.close()
