// Front-end test of the editor with mocked API responses (no real login needed).
import { chromium } from 'playwright'
const base = process.argv[2]
const b = await chromium.launch({ channel: 'chrome' })
const p = await b.newPage()
const logs = []
p.on('console', (m) => ['error', 'warning'].includes(m.type()) && logs.push(`[${m.type()}] ${m.text().slice(0, 220)}`))
p.on('pageerror', (e) => logs.push(`[pageerror] ${e.message.slice(0, 220)}`))
await p.route('**/api/auth/me', (r) => r.fulfill({ json: { user: { id: '5554', username: 'Yug' }, admin: true } }))
let puts = 0
await p.route('**/api/admin/page**', (r) => {
  if (r.request().method() === 'PUT') { puts++; return r.fulfill({ json: { ok: true } }) }
  return r.fulfill({ json: { path: '/foo', text: '---\ntitle: "Hola"\n---\n\n## Texto de prueba\n\nUn párrafo.\n' } })
})
await p.goto(`${base}/admin/edit/?path=/foo`, { waitUntil: 'load' })
await p.waitForTimeout(12000)
const content = await p.locator('.cm-content').first().innerText().catch(() => '(no .cm-content)')
console.log('editor text:', JSON.stringify(content.slice(0, 80)))
console.log('preview html:', JSON.stringify((await p.locator('.preview').first().innerHTML().catch(() => '(none)')).slice(0, 300)))
console.log('status:', await p.locator('.msg').allInnerTexts())
if (content.includes('Texto de prueba')) {
  await p.locator('.cm-content').first().click(); await p.keyboard.type('X')
  await p.waitForTimeout(300); await p.click('.save'); await p.waitForTimeout(800)
  console.log('PUT requests after save:', puts, '| status:', await p.locator('.msg').allInnerTexts())
}
console.log(logs.slice(0, 8).join('\n') || '(no console errors)')
await b.close()
